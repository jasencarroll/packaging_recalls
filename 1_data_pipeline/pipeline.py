"""
FDA Packaging Recall Data Pipeline
==================================
Production-ready pipeline for extracting, transforming, and analyzing
FDA drug recall data focused on packaging defects.
"""

import time
import re
import logging
import math
import json
from pathlib import Path
import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FDARecallPipeline:
    """
    Data pipeline for FDA packaging recall analysis
    """

    def __init__(self, output_dir="data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.base_url = "https://api.fda.gov/drug/enforcement.json"

    def extract_packaging_recalls(self, limit, search_terms=None):
        """
        Extract packaging-related recalls from FDA API
        """
        if search_terms is None:
            search_terms = [
                "packaging",
                "blister",
                "container",
                "seal",
                "closure",
                "labeling",
            ]

        all_recalls = []

        for term in search_terms:
            logger.info("Extracting recalls for term: %s", term)
            # Use pagination to collect up to 'limit' results per term
            try:
                term_results = self._extract_with_pagination(term, max_results=limit)
                all_recalls.extend(term_results)
            except (requests.RequestException, ValueError, KeyError) as e:
                logger.error("Failed to paginate for term '%s': %s", term, e)
                continue

        # Remove duplicates based on event_id
        unique_recalls = {recall["event_id"]: recall for recall in all_recalls}
        final_recalls = list(unique_recalls.values())

        logger.info("Total unique recalls extracted: %d", len(final_recalls))
        return final_recalls

    def _extract_with_pagination(self, search_term, max_results):
        """Extract all results for a search term using pagination."""
        all_results = []
        skip = 0
        hard_limit = 1000  # FDA API hard limit per request

        while skip < max_results:
            remaining = max_results - skip
            current_limit = min(hard_limit, remaining)

            params = {
                "search": f'reason_for_recall:"{search_term}"',
                "limit": current_limit,
                "skip": skip,
            }

            try:
                response = requests.get(self.base_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                if "results" in data and data["results"]:
                    batch = data["results"]
                    all_results.extend(batch)
                    logger.info(
                        "Retrieved %d recalls for '%s' (skip=%d, total so far: %d)",
                        len(batch),
                        search_term,
                        skip,
                        len(all_results),
                    )

                    # If fewer than requested, we've reached the end
                    if len(batch) < current_limit:
                        logger.info(
                            "Retrieved all available data for '%s' - got %d < %d",
                            search_term,
                            len(batch),
                            current_limit,
                        )
                        break

                    skip += len(batch)
                else:
                    logger.info(
                        "No more results available for '%s' at skip=%d",
                        search_term,
                        skip,
                    )
                    break

                # Be polite to the API
                time.sleep(0.1)

            except requests.RequestException as e:
                logger.error(
                    "Failed to fetch batch for '%s' at skip=%d: %s",
                    search_term,
                    skip,
                    e,
                )
                # Attempt to continue with next page
                skip += current_limit
                continue

        logger.info("Final total extracted for '%s': %d", search_term, len(all_results))
        return all_results

    def transform_recalls(self, recalls_data):
        """
        Transform raw recall data into analysis-ready format
        """
        logger.info("Starting data transformation")

        # Convert to DataFrame
        df = pd.DataFrame(recalls_data)

        # Basic data cleaning
        df = self._clean_basic_fields(df)

        # Extract packaging information
        df = self._categorize_packaging_defects(df)

        # Extract product information
        df = self._extract_product_info(df)

        # Calculate business metrics
        df = self._calculate_metrics(df)

        # Add risk scoring
        df = self._add_risk_scoring(df)

        logger.info("Transformation complete. Final dataset: %d records", len(df))
        return df

    def _clean_basic_fields(self, df):
        """Clean and standardize basic fields"""

        # Convert dates
        date_fields = [
            "recall_initiation_date",
            "center_classification_date",
            "termination_date",
        ]
        for field in date_fields:
            if field in df.columns:
                df[field] = pd.to_datetime(df[field], format="%Y%m%d", errors="coerce")

        # Clean text fields
        text_fields = ["reason_for_recall", "product_description", "recalling_firm"]
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip()

        # Standardize classification
        if "classification" in df.columns:
            df["classification_clean"] = df["classification"].str.replace("Class ", "")

        # Extract numeric quantities where possible
        if "product_quantity" in df.columns:
            df["quantity_numeric"] = df["product_quantity"].apply(
                self._extract_quantity
            )

        return df

    def _extract_quantity(self, quantity_str):
        """Extract numeric quantity from product_quantity field"""
        if pd.isna(quantity_str):
            return None

        # Look for numbers followed by common units
        matches = re.findall(r"(\d+(?:,\d+)*)", str(quantity_str))
        if matches:
            # Take the first number found, remove commas
            return int(matches[0].replace(",", ""))
        return None

    def _categorize_packaging_defects(self, df):
        """Categorize recalls by packaging defect type"""

        # Expanded patterns to better map reasons to categories and reduce 'other'
        # Note: Use non-capturing groups (?:...) in regex to avoid pandas warnings about match groups
        defect_patterns = {
            # Labeling and printed information issues on primary or secondary packaging
            "labeling_error": [
                r"label.*mix",
                r"label.*mix[- ]?up",
                r"mix[- ]?up.*label",
                r"incorrect.*ndc",
                r"missing.*label",
                r"labeling.*error",
                r"\blabeling\b",
                r"label.*incorrect",
                r"wrong.*label",
                r"mislabel",
                r"mislabeled",
                r"mislabeling",
                r"label.*switch",
                r"label.*error",
                r"incorrect.*labeling",
                r"missing.*lot",
                r"lot.*number.*missing",
                r"exp(?:iry|iration)?.*date",
                r"incorrect.*expiration",
                r"ndc.*number|incorrect.*ndc",
                r"product.*code|ndc",
                r"barcode|upc",
                r"over[- ]?label|under[- ]?label",
                r"wrong.*strength.*label|strength.*mismatch",
                r"dosage.*mismatch|dose.*mismatch",
                r"carton.*label.*mismatch|bottle.*label.*mismatch",
                r"printed.*label.*error|artwork.*error|typographical",
                r"label.*omission|missing.*warning|missing.*instructions|missing.*insert",
                r"foreign.*label|foreign.*language|illegible.*(?:carton|label)",
                r"incorrect.*(?:carton|insert|leaflet|package)",
            ],
            # Any sterility/microbial contamination concerns
            "sterility_breach": [
                r"sterility|lack.*assurance.*sterility|non[- ]?sterile",
                r"contamination",
                r"microbial|microbiological|bioburden|endotoxin|bacterial|fung(?:al|us)|yeast",
                r"mold|mould|spore|micro[- ]?organism|microorganism",
            ],
            # Container/closure integrity, seals, caps, stoppers, leaks, tamper evidence
            "container_closure": [
                r"container.*defect|container.*integrity|package.*integrity",
                r"closure.*integrity",
                r"seal.*defect|seal.*failure|seal.*compromised|seal.*broken|poor.*seal",
                r"cap.*defect|loose.*cap|cap.*loose|cap.*missing",
                r"closure.*failure|closure.*not.*sealed|improper.*closure",
                r"tamper[- ]?evident.*(?:broken|missing)|tamper.*seal.*(?:broken|missing)",
                r"leakage|\bleak\b|leaking",
                r"crimp.*defect|crimp.*failure",
                r"pinhole",
                r"syringe.*plunger.*defect|syringe.*leak",
                r"stopper.*loose|stopper.*missing",
            ],
            # Blister pack and foil sealing problems
            "blister_seal": [
                r"blister.*seal|blister.*defect|blister.*pack|foil.*seal|heat.*seal",
                r"inadequately.*sealed|incomplete.*seal|seal.*integrity|peel.*strength|peelability",
                r"pocket.*open|cavity.*open|bubble.*pack|unit[- ]?dose.*mispackaging|mispackaging",
            ],
            # Moisture/humidity ingress and desiccant problems
            "moisture_ingress": [
                r"moisture|humidity|condensation|wet|damp",
                r"air.*ingress|water.*ingress",
                r"desiccant|silica.*gel|drying.*agent",
                r"moisture.*content|humidity.*control|pinhole",
            ],
            # Physical foreign matter
            "foreign_substance": [
                r"foreign.*substance|foreign.*material|foreign.*object|foreign.*matter|foreign.*body",
                r"particulate|\bparticles?\b|debris|contaminant|impurity|specks?",
                r"glass|rubber|metal.*shavings|metal.*fragment|fiber?s?|hair|insect|rust",
                r"white.*particles|black.*specks|black.*particles",
                r"foreign.*tablet(?:s)?|foreign.*capsule(?:s)?|foreign.*pill(?:s)?|foreign.*stopper",
            ],
            # Assay, strength, and content issues
            "potency_issues": [
                r"\bpotency\b|\bstrength\b|concentration|assay|out.*of.*specification",
                r"below.*specification|low.*potency|high.*potency|does.*not.*conform",
                r"active.*ingredient|drug.*substance|\bapi\b|content.*uniformity",
                r"sub[- ]?potent|super[- ]?potent|over[- ]?potent|under[- ]?potent|label.*claim.*not.*met",
            ],
            # Production errors and process deviations
            "manufacturing_defect": [
                r"manufacturing.*defect|manufacturing.*error|manufacturing|packaging.*line|packaging.*room",
                r"production.*error|process.*deviation|process.*control|in[- ]?process",
                r"batch.*failure|batch.*rejection|equipment.*malfunction|gmp|cgmp|cpgmp",
                r"undetected.*packaging.*issue|random.*packaging.*issue|set[- ]?up|setup",
            ],
            # Stability or degradation over time or due to packaging
            "stability_degradation": [
                r"stability|stability.*testing|shelf.*life|expiry|expiration",
                r"degradation|decompos(?:ition|e)|degradant|impurity.*increase",
                r"color.*change|discoloration|precipitat(?:e|ion)|phase.*separation|crystal(?:l)?ization|cloudiness",
            ],
            # Documentation such as package insert/leaflet and certificates
            "documentation_error": [
                r"documentation|certificate|specification|analytical.*certificate|\bcoa\b",
                r"test.*results|documentation.*error|missing.*documentation|incorrect.*documentation",
                r"package.*insert|leaflet|instructions.*missing|incorrect.*insert|spl|missing.*carton|missing.*outer\s*carton",
            ],
            # Mix-ups leading to wrong product in the wrong package
            "cross_contamination": [
                r"cross.*contamination|contamination.*between|co[- ]?mingled",
                r"product.*mix|batch.*mix|mixed.*product|mix.?up|mixup|swapped",
                r"wrong.*product|wrong.*strength|wrong.*drug|incorrect.*product",
            ],
            # Generic packaging defects and compliance (e.g., child-resistant, cartons)
            "packaging_defect": [
                r"packaging.*defect|package.*defect|packaging.*error|package.*integrity|overwrap",
                r"secondary.*packaging|carton.*defect|box.*defect|carton.*error|carton.*mismatch|wrong.*carton",
                r"child.*resistant|child.*proof|count.*mismatch|shortage.*count|mispackaging|packaging.*issue",
            ],
            # Physical dosage form defects visible at pack-out
            "tablet_defect": [
                r"tablet.*defect|capsule.*defect|tablet.*friability|hardness|dissolution",
                r"disintegration|tablet.*appearance|coating.*defect|chipped.*tablet|broken.*tablet|cracked.*tablet",
                r"soft.*gel|leaking.*capsule|empty.*capsule",
            ],
        }

        # Initialize defect category columns
        for category in defect_patterns:
            df[f"defect_{category}"] = False

        # Categorize based on reason_for_recall
        for category, patterns in defect_patterns.items():
            pattern = "|".join(patterns)
            # Use regex with non-capturing groups to avoid match-group warnings
            mask = df["reason_for_recall"].str.contains(
                pattern, case=False, na=False, regex=True
            )
            df.loc[mask, f"defect_{category}"] = True

        # Create primary defect category based on a clear priority order
        priority_order = [
            "sterility_breach",
            "cross_contamination",
            "foreign_substance",
            "container_closure",
            "blister_seal",
            "moisture_ingress",
            "packaging_defect",
            "labeling_error",
            "documentation_error",
            "stability_degradation",
            "manufacturing_defect",
            "potency_issues",
            "tablet_defect",
        ]

        df["primary_defect"] = "other"
        # Assign the first matching category by priority
        for category in priority_order:
            col = f"defect_{category}"
            if col in df.columns:
                mask = df[col]
                df.loc[mask & (df["primary_defect"] == "other"), "primary_defect"] = (
                    category
                )

        # Fallback reclassification: for remaining 'other', use broad substring stems
        # derived from the analysis breakdown logic to minimize uncategorized items.
        fallback_stems = {
            "labeling_error": [
                "mislabel",
                "wrong label",
                "incorrect label",
                "label mix",
                "labeling error",
                "wrong strength",
                "strength mismatch",
                "dosage mismatch",
            ],
            "foreign_substance": [
                "contaminat",
                "foreign matter",
                "foreign substance",
                "impurit",
                "debris",
                "particulate",
                "particle",
                "specks",
            ],
            "potency_issues": [
                "potency",
                "strength",
                "concentration",
                "assay",
                "out of specification",
            ],
            "manufacturing_defect": ["manufacturing", "production", "process", "batch"],
            "stability_degradation": [
                "stability",
                "degradation",
                "decomposition",
                "expir",
            ],
            "sterility_breach": ["microbial", "sterility", "bacterial", "endotoxin"],
            "packaging_defect": [
                "packaging",
                "container",
                "closure",
                "seal",
                "blister",
            ],
            "documentation_error": [
                "documentation",
                "record",
                "certificate",
                "specification",
            ],
        }

        reason_lower = df["reason_for_recall"].astype(str).str.lower()
        # Use the same priority order to resolve conflicts deterministically
        for category in priority_order:
            stems = fallback_stems.get(category)
            if not stems:
                continue
            stem_mask = pd.Series(False, index=df.index)
            for s in stems:
                # literal substring contains (no regex) to avoid warnings
                stem_mask = stem_mask | reason_lower.str.contains(
                    s, na=False, regex=False
                )
            assign_mask = (df["primary_defect"] == "other") & stem_mask
            if assign_mask.any():
                df.loc[assign_mask, f"defect_{category}"] = True
                df.loc[assign_mask, "primary_defect"] = category

        # Log a compact distribution after fallback
        if "primary_defect" in df.columns:
            counts = df["primary_defect"].value_counts().to_dict()
            logger.info("Primary defect distribution (post-fallback): %s", counts)

        return df

    def _extract_product_info(self, df):
        """Extract product format and packaging information"""

        # Extract packaging format from product description
        packaging_patterns = {
            "vials": ["vial", "vials"],
            "bottles": ["bottle", "bottles"],
            "blisters": ["blister", "unit dose"],
            "syringes": ["syringe", "pre-filled"],
            "tubes": ["tube", "cream", "ointment"],
            "pouches": ["pouch", "sachet"],
            "ampoules": ["ampoule", "ampule"],
        }

        df["packaging_format"] = "unknown"

        for format_type, patterns in packaging_patterns.items():
            pattern = "|".join(patterns)
            mask = df["product_description"].str.contains(pattern, case=False, na=False)
            df.loc[mask, "packaging_format"] = format_type

        # Extract dosage form
        dosage_patterns = {
            "tablets": ["tablet", "tab"],
            "capsules": ["capsule", "cap"],
            "injections": ["injection", "injectable"],
            "creams": ["cream", "ointment", "gel"],
            "solutions": ["solution", "liquid"],
        }

        df["dosage_form"] = "unknown"

        for dosage, patterns in dosage_patterns.items():
            pattern = "|".join(patterns)
            mask = df["product_description"].str.contains(pattern, case=False, na=False)
            df.loc[mask, "dosage_form"] = dosage

        return df

    def _calculate_metrics(self, df):
        """Calculate business metrics and KPIs"""

        # Time to resolution (days from initiation to termination)
        df["days_to_resolution"] = (
            df["termination_date"] - df["recall_initiation_date"]
        ).dt.days

        # Recall year for trending
        df["recall_year"] = df["recall_initiation_date"].dt.year

        # Severity scoring (Class I=10, Class II=5, Class III=1)
        severity_map = {"I": 10, "II": 5, "III": 1}
        df["severity_score"] = df["classification_clean"].map(severity_map).fillna(0)

        # Business impact estimate (based on classification and quantity)
        df["estimated_cost_impact"] = df.apply(self._estimate_cost_impact, axis=1)

        return df

    def _estimate_cost_impact(self, row):
        """Estimate cost impact based on classification and quantity"""

        base_costs = {"I": 1000000, "II": 100000, "III": 10000}  # Base cost by class

        # Get values safely
        classification = row.get("classification_clean")
        quantity = row.get("quantity_numeric")

        # Handle classification
        if pd.isna(classification) or classification not in base_costs:
            base_cost = 50000
        else:
            base_cost = base_costs[classification]

        # Handle quantity - convert to numeric and validate
        try:
            if pd.isna(quantity) or quantity is None:
                quantity = 1000
            else:
                quantity = float(quantity)
                if quantity <= 0 or not math.isfinite(quantity):
                    quantity = 1000
        except (ValueError, TypeError):
            quantity = 1000

        # Calculate multiplier safely
        try:
            quantity_multiplier = math.log10(max(quantity, 1)) / 3
            if not math.isfinite(quantity_multiplier):
                quantity_multiplier = 0
        except (ValueError, OverflowError):
            quantity_multiplier = 0

        # Calculate final result
        try:
            result = base_cost * (1 + quantity_multiplier)
            if not math.isfinite(result):
                return 50000
            return int(result)
        except (ValueError, OverflowError, TypeError):
            return 50000

    def _add_risk_scoring(self, df):
        """Add risk scoring for packaging defects"""

        # Risk factors
        risk_factors = {
            "defect_sterility_breach": 10,
            "defect_blister_seal": 8,
            "defect_container_closure": 7,
            "defect_foreign_substance": 9,
            "defect_moisture_ingress": 6,
            "defect_labeling_error": 4,
        }

        df["risk_score"] = 0

        for factor, weight in risk_factors.items():
            if factor in df.columns:
                df["risk_score"] += df[factor].astype(int) * weight

        # Add severity weight
        df["risk_score"] += df["severity_score"]

        # Categorize risk levels
        df["risk_level"] = pd.cut(
            df["risk_score"],
            bins=[0, 5, 10, 15, float("inf")],
            labels=["Low", "Medium", "High", "Critical"],
        )

        return df

    def save_processed_data(self, df, filename="fda_packaging_recalls_processed.csv"):
        """Save processed data to file"""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        logger.info("Processed data saved to %s", output_path)

        # Also save summary statistics
        summary_path = self.output_dir / "recall_summary.json"
        summary = self._generate_summary(df)

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info("Summary statistics saved to %s", summary_path)

        return output_path

    def _generate_summary(self, df):
        """Generate summary statistics"""
        return {
            "total_recalls": len(df),
            "date_range": {
                "earliest": df["recall_initiation_date"].min(),
                "latest": df["recall_initiation_date"].max(),
            },
            "classification_breakdown": df["classification_clean"]
            .value_counts()
            .to_dict(),
            "primary_defects": df["primary_defect"].value_counts().to_dict(),
            "packaging_formats": df["packaging_format"].value_counts().to_dict(),
            "risk_levels": df["risk_level"].value_counts().to_dict(),
            "top_firms": df["recalling_firm"].value_counts().head(10).to_dict(),
            "estimated_total_cost": df["estimated_cost_impact"].sum(),
            "average_resolution_days": df["days_to_resolution"].mean(),
        }

    def run_pipeline(self, limit):
        """Run the complete pipeline"""
        logger.info("Starting FDA Packaging Recall Pipeline")

        # Extract
        raw_data = self.extract_packaging_recalls(limit=limit)

        if not raw_data:
            logger.error("No data extracted. Pipeline stopped.")
            return None

        # Transform
        transformed_data = self.transform_recalls(raw_data)

        # Load (save)
        self.save_processed_data(transformed_data)

        logger.info("Pipeline completed successfully")
        return transformed_data


# Usage example
if __name__ == "__main__":
    # Initialize pipeline
    # Save into the folder that analysis.py reads from
    pipeline = FDARecallPipeline(output_dir="1_data_pipeline/fda_recall_data")

    # Run pipeline
    processed_data = pipeline.run_pipeline(limit=10000)

    if processed_data is not None:
        print(f"Pipeline complete. Processed {len(processed_data)} recall records.")
        print("\nSample of processed data:")
        print(
            processed_data[
                [
                    "recall_initiation_date",
                    "classification_clean",
                    "primary_defect",
                    "packaging_format",
                    "risk_level",
                ]
            ].head()
        )
