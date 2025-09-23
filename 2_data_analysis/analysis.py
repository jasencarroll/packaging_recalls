import warnings
from pathlib import Path
import json
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud  # type: ignore


warnings.filterwarnings("ignore")


class RecordTable:
    """
    Load a CSV into a pandas DataFrame and return a plain‑dictionary summary.

    The CSV must live in `<cwd>/.data/<filename>`.  The class is intentionally
    lightweight – it does **not** print anything, so it is easy to test
    programmatically and to serialise for downstream reporting.
    """

    def __init__(self, name: str, filename: str):
        self.name = name
        self.df = self.load_data(filename)
        # summary is a plain dict, see :meth:`summary_data`
        self.summary: dict = self.summary_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def load_data(self, filename: str) -> pd.DataFrame:
        """Return a DataFrame from the CSV in `<cwd>/.data/`."""
        data_path = Path.cwd() / "1_data_pipeline/fda_recall_data/" / filename
        return pd.read_csv(data_path)

    # ------------------------------------------------------------------
    # Data sanitization
    # ------------------------------------------------------------------
    def clean_data(self) -> None:
        """Clean the DataFrame by dropping N/A values and unwanted columns."""
        print("🧹 Cleaning data...")

        # Store original shape
        original_shape = self.df.shape

        # Drop specified columns if they exist
        columns_to_drop = ["address_2", "more_code_info"]
        existing_columns_to_drop = [
            col for col in columns_to_drop if col in self.df.columns
        ]

        if existing_columns_to_drop:
            self.df = self.df.drop(columns=existing_columns_to_drop)
            print(f"   Dropped columns: {existing_columns_to_drop}")

        # Drop rows with N/A values
        self.df = self.df.dropna()

        # Update summary after cleaning
        self.summary = self.summary_data()

        print(f"   Original shape: {original_shape}")
        print(f"   Cleaned shape: {self.df.shape}")
        print(f"   Removed {original_shape[0] - self.df.shape[0]} rows with N/A values")
        print(f"   Removed {original_shape[1] - self.df.shape[1]} columns")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def summary_data(self) -> dict:
        """
        Return a dictionary with three keys:

        * ``columns`` – list of column names
        * ``entries`` – the whole dataframe as a list of dicts, where missing
          values are represented as ``None`` instead of ``NaN``.
        * ``missing`` – a mapping of column name to the number of missing
          values.

        The implementation deliberately keeps the data pure and test‑friendly.
        """
        df = self.df

        # Convert each row to a plain Python dict.
        entries: list[dict] = []
        for _, row in df.iterrows():
            record: dict = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    record[col] = None
                else:
                    # Convert integer‑like floats to ``int``.
                    if isinstance(val, float) and val.is_integer():
                        record[col] = int(val)
                    else:
                        record[col] = val
            entries.append(record)

        return {
            "columns": df.columns.tolist(),
            "entries": entries,
            "missing": df.isnull().sum().to_dict(),
        }

    # ------------------------------------------------------------------
    # Pretty‑print helper (interactive only)
    # ------------------------------------------------------------------
    def print_summary(self) -> None:
        """Print a meaningful summary of the dataset."""
        df = self.df
        print(f"\n{'=' * 60}")
        print(f"Dataset Summary: {self.name}")
        print(f"{'=' * 60}")

        # Basic info
        print(f"📊 Total Records: {len(df):,}")
        print(f"📈 Columns: {len(df.columns)}")
        print(
            f"📅 Date Range: {df['recall_initiation_date'].min()} to "
            f"{df['recall_initiation_date'].max()}"
        )

        # Classification breakdown
        print("\n🏷️  Classification Breakdown:")
        class_counts = df["classification_clean"].value_counts()
        for classification, count in class_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   Class {classification}: {count:,} ({percentage:.1f}%)")

        # Primary defects
        print("\n🔍 Top Primary Defects:")
        defect_counts = df["primary_defect"].value_counts().head(5)
        for defect, count in defect_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   {defect}: {count:,} ({percentage:.1f}%)")

        # Risk levels
        print("\n⚠️  Risk Level Distribution:")
        risk_counts = df["risk_level"].value_counts()
        for risk, count in risk_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   {risk}: {count:,} ({percentage:.1f}%)")

        # Cost impact stats
        if "estimated_cost_impact" in df.columns:
            print("\n💰 Cost Impact Analysis:")
            cost_stats = df["estimated_cost_impact"].describe()
            print(f"   Average: ${cost_stats['mean']:,.0f}")
            print(f"   Median: ${cost_stats['50%']:,.0f}")
            print(f"   Total Estimated: ${df['estimated_cost_impact'].sum():,.0f}")

        # Missing data
        print("\n❓ Missing Data:")
        missing = df.isnull().sum()
        missing_data = missing[missing > 0]
        if len(missing_data) > 0:
            for col, count in missing_data.items():
                percentage = (count / len(df)) * 100
                print(f"   {col}: {count:,} ({percentage:.1f}%)")
        else:
            print("   No missing data found!")

        print(f"\n{'=' * 60}\n")

    def save_columns_to_json(
        self, output_filename: str = "dataframe_columns.json"
    ) -> None:
        """Save the DataFrame column names to a pretty-printed JSON file."""
        columns_info = {
            "dataset_name": self.name,
            "total_columns": len(self.df.columns),
            "columns": self.df.columns.tolist(),
            "column_details": {
                col: {
                    "dtype": str(self.df[col].dtype),
                    "non_null_count": int(self.df[col].count()),
                    "null_count": int(self.df[col].isnull().sum()),
                }
                for col in self.df.columns
            },
        }

        output_path = Path.cwd() / "2_data_analysis" / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(columns_info, f, indent=2, default=str)

        print(f"✅ Column information saved to: {output_path}")

    def save_to_database(
        self, db_filename: str = "database.db", table_name: str = "recalls"
    ) -> None:
        """Save the cleaned DataFrame to a SQLite database."""
        db_path = Path.cwd() / "2_data_analysis" / db_filename

        print("💾 Saving cleaned data to database...")

        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(db_path)

        try:
            # Save DataFrame to SQLite table
            self.df.to_sql(table_name, conn, if_exists="replace", index=False)

            # Get some stats about the saved data
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_count = len(columns_info)

            print(f"✅ Data saved to database: {db_path}")
            print(f"   Table: {table_name}")
            print(f"   Rows: {row_count:,}")
            print(f"   Columns: {column_count}")

        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            print(f"❌ Error saving to database: {e}")
        finally:
            conn.close()

    def create_visualizations(self, output_dir: str = "visualizations") -> None:
        """Create comprehensive visualizations of the recall data."""
        viz_path = Path.cwd() / "2_data_analysis" / output_dir
        viz_path.mkdir(exist_ok=True)
        print("📊 Creating visualizations...")

        self._plot_classification_distribution(viz_path)
        self._plot_time_series(viz_path)
        self._plot_correlation_heatmap(viz_path)
        self._plot_wordcloud(viz_path)
        self._plot_cost_by_classification(viz_path)

        print("✅ Visualizations saved to:", viz_path)
        print("   📈 recall_overview.png - Main dashboard")
        print("   📅 time_series.png - Trends over time")
        print("   🔥 correlation_heatmap.png - Variable relationships")
        print("   ☁️  recall_reasons_wordcloud.png - Common recall terms")
        print("   📊 cost_by_classification.png - Cost analysis")

    def create_defect_visuals(self, output_dir: str = "visualizations") -> None:
        """Create standalone visuals for defects distribution and severity by defect."""
        viz_path = Path.cwd() / "2_data_analysis" / output_dir
        viz_path.mkdir(exist_ok=True)

        # 1) All Primary Defects Distribution (bar chart)
        plt.style.use("seaborn-v0_8")
        sns.set_palette("Set3")
        plt.figure(figsize=(12, 7))
        defect_counts = self.df["primary_defect"].value_counts()
        ax = sns.barplot(x=defect_counts.index, y=defect_counts.values)
        ax.set_title("All Primary Defects Distribution", fontsize=14, fontweight="bold")
        ax.set_xlabel("Primary Defect")
        ax.set_ylabel("Number of recalls")
        plt.xticks(rotation=45, ha="right")
        # Add value labels on bars
        for i, v in enumerate(defect_counts.values):
            ax.annotate(
                f"{int(v)}",
                (i, v),
                ha="center",
                va="bottom",
            )
        dist_path = viz_path / "all_primary_defects_distribution.png"
        plt.tight_layout()
        plt.savefig(dist_path, dpi=300, bbox_inches="tight")
        plt.close()

        # 2) Average Severity Score by Defect Type (barh)
        plt.style.use("seaborn-v0_8")
        # Compute severity proxy as in _plot_severity_correlation
        severity_by_defect = (
            self.df.groupby("primary_defect")["classification_clean"].apply(
                lambda x: (x == "I").sum() * 3
                + (x == "II").sum() * 2
                + (x == "III").sum() * 1
            )
            / self.df.groupby("primary_defect").size()
        )

        severity_by_defect = severity_by_defect.sort_values(ascending=True)
        plt.figure(figsize=(12, 8))
        ax2 = sns.barplot(
            x=severity_by_defect.values,
            y=severity_by_defect.index,
            palette=sns.color_palette("RdYlBu_r", len(severity_by_defect)),
            orient="h",
        )
        ax2.set_title(
            "Average Severity Score by Defect Type", fontsize=14, fontweight="bold"
        )
        ax2.set_xlabel("Severity Score (1=Class III, 2=Class II, 3=Class I)")
        ax2.set_ylabel("Primary Defect")
        # Add value labels without relying on Patch geometry accessors
        y_positions = ax2.get_yticks()
        for y, val in zip(y_positions, severity_by_defect.values):
            ax2.annotate(
                f"{val:.2f}",
                (val + 0.02, y),
                ha="left",
                va="center",
            )
        sev_path = viz_path / "severity_by_defect.png"
        plt.tight_layout()
        plt.savefig(sev_path, dpi=300, bbox_inches="tight")
        plt.close()

        print("🔧 Defect visuals saved to:")
        print(f"   📊 {dist_path}")
        print(f"   🎯 {sev_path}")

    def _plot_classification_distribution(self, viz_path):
        plt.style.use("seaborn-v0_8")
        sns.set_palette("husl")
        _, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        class_counts = self.df["classification_clean"].value_counts()
        colors = ["#ff9999", "#66b3ff", "#99ff99"]
        ax1.pie(
            class_counts.values,
            labels=[f"Class {c}" for c in class_counts.index],
            autopct="%1.1f%%",
            colors=colors,
        )
        ax1.set_title("FDA Classification Distribution", fontsize=14, fontweight="bold")

        risk_counts = self.df["risk_level"].value_counts()
        recall_bars = ax2.bar(
            risk_counts.index,
            risk_counts.values,
            color=["red", "orange", "yellow", "green"],
        )
        ax2.set_title("Risk Level Distribution", fontsize=14, fontweight="bold")
        ax2.set_ylabel("Number of recalls")
        for recall_bar in recall_bars:
            height = recall_bar.get_height()
            ax2.text(
                recall_bar.get_x() + recall_bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
            )

        defect_counts = self.df["primary_defect"].value_counts().head(8)
        ax3.barh(range(len(defect_counts)), defect_counts.values)
        ax3.set_yticks(range(len(defect_counts)))
        ax3.set_yticklabels(defect_counts.index)
        ax3.set_title("Top Primary Defects", fontsize=14, fontweight="bold")
        ax3.set_xlabel("Number of recalls")

        ax4.hist(
            self.df["estimated_cost_impact"],
            bins=30,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
        )
        ax4.set_title("Cost Impact Distribution", fontsize=14, fontweight="bold")
        ax4.set_xlabel("Estimated Cost Impact ($)")
        ax4.set_ylabel("Frequency")
        ax4.ticklabel_format(style="scientific", axis="x", scilimits=(0, 0))

        plt.tight_layout()
        plt.savefig(viz_path / "recall_overview.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _plot_time_series(self, viz_path):
        plt.style.use("seaborn-v0_8")
        sns.set_palette("husl")
        _, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

        self.df["recall_date"] = pd.to_datetime(self.df["recall_initiation_date"])
        self.df["year_month"] = self.df["recall_date"].dt.to_period("M")

        monthly_recalls = self.df.groupby("year_month").size()
        monthly_recalls.plot(kind="line", ax=ax1, color="blue", linewidth=2)
        ax1.set_title("recalls Over Time (Monthly)", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Number of recalls")
        ax1.grid(True, alpha=0.3)

        class_time = (
            self.df.groupby(["year_month", "classification_clean"])
            .size()
            .unstack(fill_value=0)
        )
        class_time.plot(kind="area", stacked=True, ax=ax2, alpha=0.7)
        ax2.set_title(
            "Recall Classifications Over Time", fontsize=14, fontweight="bold"
        )
        ax2.set_ylabel("Number of recalls")
        ax2.legend(title="Classification")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(viz_path / "time_series.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _plot_correlation_heatmap(self, viz_path):
        plt.figure(figsize=(12, 8))
        numeric_cols = [
            "severity_score",
            "estimated_cost_impact",
            "risk_score",
            "days_to_resolution",
            "quantity_numeric",
        ]
        corr_data = self.df[numeric_cols].corr()

        sns.heatmap(
            corr_data,
            annot=True,
            cmap="coolwarm",
            center=0,
            square=True,
            fmt=".2f",
            cbar_kws={"shrink": 0.8},
        )
        plt.title(
            "Correlation Matrix of Numeric Variables", fontsize=14, fontweight="bold"
        )
        plt.tight_layout()
        plt.savefig(viz_path / "correlation_heatmap.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _plot_wordcloud(self, viz_path):
        plt.figure(figsize=(12, 8))
        text = " ".join(self.df["reason_for_recall"].astype(str))

        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            max_words=100,
            colormap="viridis",
        ).generate(text)

        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title(
            "Most Common Words in Recall Reasons",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )
        plt.tight_layout()
        plt.savefig(
            viz_path / "recall_reasons_wordcloud.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def _plot_cost_by_classification(self, viz_path):
        plt.figure(figsize=(10, 6))
        classification_order = ["III", "II", "I"]
        ax = sns.boxplot(
            data=self.df,
            x="classification_clean",
            y="estimated_cost_impact",
            order=classification_order,
        )

        for i, classification in enumerate(classification_order):
            class_data = self.df[self.df["classification_clean"] == classification][
                "estimated_cost_impact"
            ]
            mean_val = class_data.mean()
            y_pos = ax.get_ylim()[1] * 0.95
            ax.text(
                i,
                y_pos,
                f"Mean: ${mean_val:,.0f}",
                horizontalalignment="center",
                fontweight="bold",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "yellow", "alpha": 0.7},
            )

        plt.title(
            "Cost Impact Distribution by Classification", fontsize=14, fontweight="bold"
        )
        plt.ylabel("Estimated Cost Impact ($)")
        plt.xlabel("FDA Classification (Severity: III → II → I)")
        plt.yscale("log")
        plt.tight_layout()
        plt.savefig(
            viz_path / "cost_by_classification.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def create_detailed_defects_analysis(
        self, output_dir: str = "visualizations"
    ) -> None:
        """Create detailed analysis of primary defects, unpacking the 'other' category."""
        viz_path = Path.cwd() / "2_data_analysis" / output_dir
        viz_path.mkdir(exist_ok=True)

        print("🔍 Creating detailed defects analysis...")

        # Set style and create subplots
        plt.style.use("seaborn-v0_8")
        sns.set_palette("husl")
        _, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # Create all four subplot analyses
        other_categorized = self._plot_all_defects(ax1)
        self._plot_other_breakdown(ax2, other_categorized)
        self._plot_combined_defects(ax3, other_categorized)
        self._plot_severity_correlation(ax4)

        # Save and close
        plt.tight_layout()
        plt.savefig(
            viz_path / "detailed_defects_analysis.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        self._print_analysis_summary(viz_path, other_categorized)

    def _get_defect_patterns(self) -> dict[str, list[str]]:
        """Return defect patterns for categorizing 'other' defects."""
        return {
            "Mislabeling/Wrong Label": [
                "mislabel",
                "wrong label",
                "incorrect label",
                "label mix",
                "labeling error",
            ],
            "Contamination": [
                "contaminat",
                "foreign matter",
                "foreign substance",
                "impurit",
            ],
            "Potency Issues": [
                "potency",
                "strength",
                "concentration",
                "assay",
                "out of specification",
            ],
            "Manufacturing Defect": ["manufacturing", "production", "process", "batch"],
            "Stability/Degradation": [
                "stability",
                "degradation",
                "decomposition",
                "expir",
            ],
            "Microbial/Sterility": ["microbial", "sterility", "bacterial", "endotoxin"],
            "Packaging Defect": [
                "packaging",
                "container",
                "closure",
                "seal",
                "blister",
            ],
            "Documentation Error": [
                "documentation",
                "record",
                "certificate",
                "specification",
            ],
        }

    def _categorize_other_defects(self) -> dict[str, int]:
        """Categorize defects in the 'other' category."""
        other_data = self.df[self.df["primary_defect"] == "other"][
            "reason_for_recall"
        ].astype(str)

        defect_patterns = self._get_defect_patterns()
        other_categorized: dict[str, int] = {}
        uncategorized_count = 0

        for reason in other_data:
            reason_lower = str(reason).lower()
            categorized = False

            for category, patterns in defect_patterns.items():
                if any(pattern in reason_lower for pattern in patterns):
                    other_categorized[category] = other_categorized.get(category, 0) + 1
                    categorized = True
                    break

            if not categorized:
                uncategorized_count += 1

        if uncategorized_count > 0:
            other_categorized["Truly Other"] = uncategorized_count

        return other_categorized

    def _plot_all_defects(self, ax) -> dict[str, int]:
        """Plot all primary defects distribution."""
        defect_counts = self.df["primary_defect"].value_counts()
        colors = sns.color_palette("Set3", len(defect_counts))

        chart_bars = ax.bar(
            range(len(defect_counts)), defect_counts.values, color=colors
        )
        ax.set_xticks(range(len(defect_counts)))
        ax.set_xticklabels(defect_counts.index, rotation=45, ha="right")
        ax.set_title("All Primary Defects Distribution", fontsize=14, fontweight="bold")
        ax.set_ylabel("Number of recalls")

        # Add value labels on bars
        for chart_bar in chart_bars:
            height = chart_bar.get_height()
            ax.text(
                chart_bar.get_x() + chart_bar.get_width() / 2.0,
                height + 1,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        return self._categorize_other_defects()

    def _plot_other_breakdown(self, ax, other_categorized: dict[str, int]) -> None:
        """Plot breakdown of 'other' category."""
        if not other_categorized:
            return

        other_df = pd.Series(other_categorized).sort_values(ascending=False)
        colors = sns.color_palette("pastel", len(other_df))

        chart_bars = ax.bar(range(len(other_df)), other_df.values, color=colors)
        ax.set_xticks(range(len(other_df)))
        ax.set_xticklabels(other_df.index, rotation=45, ha="right")
        ax.set_title('Breakdown of "Other" Category', fontsize=14, fontweight="bold")
        ax.set_ylabel("Number of recalls")

        # Add value labels
        for chart_bar in chart_bars:
            height = chart_bar.get_height()
            ax.text(
                chart_bar.get_x() + chart_bar.get_width() / 2.0,
                height + 0.5,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

    def _plot_combined_defects(self, ax, other_categorized: dict[str, int]) -> None:
        """Plot combined view excluding generic 'other'."""
        specific_defects = self.df[self.df["primary_defect"] != "other"][
            "primary_defect"
        ].value_counts()
        combined_defects = pd.concat(
            [specific_defects, pd.Series(other_categorized)]
        ).sort_values(ascending=False)

        colors = sns.color_palette("Set2", len(combined_defects))
        chart_bars = ax.barh(
            range(len(combined_defects)), combined_defects.values, color=colors
        )
        ax.set_yticks(range(len(combined_defects)))
        ax.set_yticklabels(combined_defects.index)
        ax.set_title(
            "All Defects (Other Category Unpacked)", fontsize=14, fontweight="bold"
        )
        ax.set_xlabel("Number of recalls")

        # Add value labels
        for chart_bar in chart_bars:
            width = chart_bar.get_width()
            ax.text(
                width + 1,
                chart_bar.get_y() + chart_bar.get_height() / 2.0,
                f"{int(width)}",
                ha="left",
                va="center",
                fontsize=10,
            )

    def _plot_severity_correlation(self, ax) -> None:
        """Plot defect severity correlation."""
        severity_by_defect = (
            self.df.groupby("primary_defect")["classification_clean"].apply(
                lambda x: (x == "I").sum() * 3
                + (x == "II").sum() * 2
                + (x == "III").sum() * 1
            )
            / self.df.groupby("primary_defect").size()
        )

        severity_by_defect = severity_by_defect.sort_values(ascending=True)
        colors = sns.color_palette("RdYlBu_r", len(severity_by_defect))

        chart_bars = ax.barh(
            range(len(severity_by_defect)), severity_by_defect.values, color=colors
        )
        ax.set_yticks(range(len(severity_by_defect)))
        ax.set_yticklabels(severity_by_defect.index)
        ax.set_title(
            "Average Severity Score by Defect Type", fontsize=14, fontweight="bold"
        )
        ax.set_xlabel("Severity Score (1=Class III, 2=Class II, 3=Class I)")

        # Add value labels
        for chart_bar in chart_bars:
            width = chart_bar.get_width()
            ax.text(
                width + 0.02,
                chart_bar.get_y() + chart_bar.get_height() / 2.0,
                f"{width:.2f}",
                ha="left",
                va="center",
                fontsize=10,
            )

    def _print_analysis_summary(
        self, viz_path: Path, other_categorized: dict[str, int]
    ) -> None:
        """Print summary of the analysis."""
        print(
            f"✅ Detailed defects analysis saved to: {viz_path}/detailed_defects_analysis.png"
        )
        print(f"   🔍 Unpacked {len(other_categorized)} subcategories from 'other'")
        print("   📊 Shows severity correlation by defect type")


def main():
    """Main function to run the data analysis pipeline."""
    recalls = RecordTable(
        name="recalls", filename="fda_packaging_recalls_processed.csv"
    )

    print("📊 Original Data Summary:")
    recalls.print_summary()

    recalls.clean_data()

    print("\n📊 Cleaned Data Summary:")
    recalls.print_summary()

    recalls.save_columns_to_json("recall_columns_info_cleaned.json")
    recalls.save_to_database("database.db", "recalls")
    recalls.create_visualizations()
    # Create standalone defect visuals (replaces detailed_defects_analysis)
    recalls.create_defect_visuals()


if __name__ == "__main__":
    main()
