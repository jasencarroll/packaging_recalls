"""
FDA Packaging Recall Interactive Dashboard
=========================================
Interactive business intelligence dashboard for FDA drug recall analysis
with focus on packaging defects and regulatory insights.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px  # type: ignore
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="FDA Packaging Recall Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .sidebar-text {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    """Load cleaned recall data from SQLite database."""
    try:
        db_path = Path(__file__).parent.parent / "2_data_analysis" / "database.db"
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM recalls", conn)
        conn.close()

        # Convert date columns
        df["recall_initiation_date"] = pd.to_datetime(df["recall_initiation_date"])
        df["recall_year"] = df["recall_initiation_date"].dt.year
        df["recall_month"] = df["recall_initiation_date"].dt.month

        # Unpack the "other" category using the same logic from detailed analysis
        df = unpack_other_category(df)

        return df
    except (sqlite3.Error, FileNotFoundError, pd.errors.DatabaseError, KeyError) as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def unpack_other_category(df):
    """Unpack the 'other' category into specific defect types based on reason_for_recall text."""

    # Define patterns to identify specific defect types within "other"
    defect_patterns = {
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
        "Stability/Degradation": ["stability", "degradation", "decomposition", "expir"],
        "Microbial/Sterility": ["microbial", "sterility", "bacterial", "endotoxin"],
        "Packaging Defect": ["packaging", "container", "closure", "seal", "blister"],
        "Documentation Error": [
            "documentation",
            "record",
            "certificate",
            "specification",
        ],
    }

    # Create a copy to avoid modifying the original
    df_updated = df.copy()

    # Process only rows where primary_defect is 'other'
    other_mask = df_updated["primary_defect"] == "other"
    other_data = df_updated[other_mask]

    for idx, row in other_data.iterrows():
        reason = str(row["reason_for_recall"]).lower()
        categorized = False

        # Check each pattern category
        for category, patterns in defect_patterns.items():
            if any(pattern in reason for pattern in patterns):
                df_updated.at[idx, "primary_defect"] = category
                categorized = True
                break

        # If not categorized, mark as "Truly Other"
        if not categorized:
            df_updated.at[idx, "primary_defect"] = "Truly Other"

    return df_updated


def create_kpi_metrics(df):
    """Create key performance indicator metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Recalls", f"{len(df):,}", delta=None)

    with col2:
        avg_cost = df["estimated_cost_impact"].mean()
        st.metric("Avg Cost Impact", f"${avg_cost:,.0f}", delta=None)

    with col3:
        class_i_pct = (df["classification_clean"] == "I").sum() / len(df) * 100
        st.metric("Class I (Critical) %", f"{class_i_pct:.1f}%", delta=None)

    with col4:
        total_cost = df["estimated_cost_impact"].sum()
        st.metric("Total Est. Impact", f"${total_cost:,.0f}", delta=None)


def create_classification_charts(df):
    """Create FDA classification analysis charts."""
    st.subheader("📋 FDA Classification Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Classification distribution pie chart
        classification_order = ["III", "II", "I"]
        class_counts = df["classification_clean"].value_counts()

        # Reorder the data according to the desired classification order
        ordered_labels = []
        ordered_values = []

        for class_type in classification_order:
            if class_type in class_counts.index:
                ordered_labels.append(f"Class {class_type}")
                ordered_values.append(class_counts[class_type])

        fig_pie = px.pie(
            values=ordered_values,
            names=ordered_labels,
            title="FDA Classification Distribution",
            color_discrete_sequence=["#45b7d1", "#4ecdc4", "#ff6b6b"],
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Cost impact by classification box plot
        classification_order = ["III", "II", "I"]
        fig_box = px.box(
            df,
            x="classification_clean",
            y="estimated_cost_impact",
            category_orders={"classification_clean": classification_order},
            title="Cost Impact by Classification",
            labels={
                "classification_clean": "FDA Classification",
                "estimated_cost_impact": "Cost Impact ($)",
            },
        )
        fig_box.update_layout(yaxis_type="log")
        st.plotly_chart(fig_box, use_container_width=True)


def create_defects_analysis(df):
    """Create primary defects analysis."""
    st.subheader("🔍 Primary Defects Analysis")

    # Defect breakdown
    col1, col2 = st.columns(2)

    with col1:
        # Top defects bar chart (show more categories now)
        defect_counts = (
            df["primary_defect"].value_counts().head(12)
        )  # Show more since we have more categories
        fig_bar = px.bar(
            x=defect_counts.values,
            y=defect_counts.index,
            orientation="h",
            title="Primary Defects",
            labels={"x": "Number of Recalls", "y": "Defect Type"},
            color=defect_counts.values,
            color_continuous_scale="viridis",
        )
        fig_bar.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=500,  # Make it taller to accommodate more categories
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # Risk level distribution
        risk_counts = df["risk_level"].value_counts()
        colors = {
            "Critical": "#ff4444",
            "High": "#ff8800",
            "Medium": "#ffcc00",
            "Low": "#44ff44",
        }
        fig_risk = px.bar(
            x=risk_counts.index,
            y=risk_counts.values,
            title="Risk Level Distribution",
            color=risk_counts.index,
            color_discrete_map=colors,
            labels={"x": "Risk Level", "y": "Number of Recalls"},
        )
        st.plotly_chart(fig_risk, use_container_width=True)


def create_time_series_analysis(df):
    """Create time series analysis."""
    st.subheader("📈 Temporal Analysis")

    # Time series of recalls
    monthly_recalls = df.groupby(df["recall_initiation_date"].dt.to_period("M")).size()

    fig_time = px.line(
        x=monthly_recalls.index.astype(str),
        y=monthly_recalls.values,
        title="Recalls Over Time (Monthly)",
        labels={"x": "Month", "y": "Number of Recalls"},
    )
    fig_time.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig_time, use_container_width=True)

    # Yearly breakdown by classification
    yearly_class = (
        df.groupby(["recall_year", "classification_clean"]).size().unstack(fill_value=0)
    )

    fig_yearly = px.bar(
        yearly_class,
        title="Annual Recalls by Classification",
        labels={"value": "Number of Recalls", "recall_year": "Year"},
        color_discrete_sequence=["#ff6b6b", "#4ecdc4", "#45b7d1"],
    )
    st.plotly_chart(fig_yearly, use_container_width=True)


def create_business_insights(df):
    """Create business insights section."""
    st.subheader("💼 Business Intelligence Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Key Findings")

        # Calculate insights
        total_recalls = len(df)
        class_i_count = (df["classification_clean"] == "I").sum()
        avg_resolution_time = df["days_to_resolution"].mean()
        most_common_defect = df["primary_defect"].value_counts().index[0]
        truly_other_count = (df["primary_defect"] == "Truly Other").sum()
        unpacked_count = total_recalls - truly_other_count

        insights = f"""
        - **{total_recalls:,} total recalls** analyzed from FDA database
        - **{class_i_count} Class I (Critical)** recalls requiring immediate action
        - **{avg_resolution_time:.0f} days** average resolution time
        - **{most_common_defect}** is the most common specific defect type
        - **${df["estimated_cost_impact"].sum():,.0f}** total estimated industry impact
        - **{unpacked_count} recalls** successfully categorized from generic "other"
        - **Only {truly_other_count} recalls** remain as "Truly Other" (uncategorizable)
        """
        st.markdown(insights)

        # Top 3 specific defect insights
        st.markdown("### 🔍 Top Defect Categories")
        top_defects = df["primary_defect"].value_counts().head(3)
        for i, (defect, count) in enumerate(top_defects.items(), 1):
            percentage = (count / total_recalls) * 100
            st.markdown(f"{i}. **{defect}**: {count} recalls ({percentage:.1f}%)")

            # Cost impact by defect type
        st.markdown("### 💰 Cost Impact by Defect")
        cost_by_defect = (
            df.groupby("primary_defect")["estimated_cost_impact"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
        )

        for defect, avg_cost in cost_by_defect.items():
            st.markdown(f"- **{defect}**: ${avg_cost:,.0f} avg impact")

    with col2:
        st.markdown("### 📊 Strategic Recommendations")

        # Generate data-driven recommendations
        labeling_issues = df[
            df["primary_defect"].str.contains("label|Label", na=False)
        ].shape[0]
        quality_issues = df[
            df["primary_defect"].str.contains(
                "Contamination|Potency|Microbial|Sterility", na=False
            )
        ].shape[0]
        packaging_issues = df[
            df["primary_defect"].str.contains(
                "Packaging|container|closure|moisture", na=False
            )
        ].shape[0]

        recommendations = f"""
        **Immediate Actions:**
        - **Labeling Systems**: {labeling_issues} labeling-related recalls - implement barcode verification
        - **Quality Control**: {quality_issues} quality issues - enhance testing protocols  
        - **Packaging Integrity**: {packaging_issues} packaging defects - upgrade validation systems
        
        **Strategic Initiatives:**
        - Develop automated defect detection using ML on recall patterns
        - Implement predictive analytics for high-risk product batches
        - Create cross-functional rapid response teams for Class I recalls
        - Invest in advanced packaging inspection technologies
        
        **Data-Driven Insights:**
        - Focus QC efforts on top {len(df["primary_defect"].unique())} identified defect categories
        - {(class_i_count / total_recalls * 100):.1f}% of recalls are critical - prioritize prevention
        """
        st.markdown(recommendations)


def main():
    """Main dashboard application."""
    st.title("FDA Packaging Recalls - Business Intelligence Dashboard")
    st.markdown("*Transforming Regulatory Data into Strategic Business Insights*")
    st.write("\n\n")
    st.divider()
    st.write("\n\n")

    # Your existing dashboard content goes here
    # Load data
    df = load_data()

    if df.empty:
        st.error("No data available. Please ensure the database file exists.")
        return

    # Create interactive filters
    df_filtered = df

    # Main dashboard content
    if len(df_filtered) == 0:
        st.warning("No data matches the current filters. Please adjust your selection.")
        return

    # Key metrics
    create_kpi_metrics(df_filtered)

    st.markdown("---")

    # Main analysis sections
    create_classification_charts(df_filtered)

    st.markdown("---")

    create_defects_analysis(df_filtered)

    st.markdown("---")

    create_time_series_analysis(df_filtered)

    st.markdown("---")

    create_business_insights(df_filtered)

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        FDA Packaging Recall Analytics Dashboard | 
        Data Source: FDA Enforcement Reports | 
        Built with Streamlit & Plotly
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
