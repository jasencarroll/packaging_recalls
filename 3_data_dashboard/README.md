# FDA Packaging Recall Interactive Dashboard

🚀 **Professional Business Intelligence Dashboard** showcasing FDA drug recall analysis with focus on packaging defects and regulatory insights.

## 📊 Dashboard Features

### **Interactive Visualizations**
- **Key Performance Indicators (KPIs)** - Total recalls, average cost impact, critical percentages
- **FDA Classification Analysis** - Distribution pie charts and cost impact analysis
- **Primary Defects Breakdown** - Top defect types and risk level distributions
- **Temporal Analysis** - Time series trends and yearly breakdowns
- **Business Intelligence Insights** - Key findings and strategic recommendations

### **Dynamic Filtering**
- **Date Range Selection** - Filter recalls by time period
- **FDA Classification** - Filter by Class I, II, or III severity
- **Risk Level** - Filter by Critical, High, Medium, Low risk
- **Primary Defect Type** - Focus on specific defect categories

### **Professional Features**
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-time Data Updates** - Connected to SQLite database
- **Export Capabilities** - Download charts and data
- **Business Intelligence Focus** - Actionable insights and recommendations

## 🛠️ Technical Stack

- **Frontend**: Streamlit (Python web framework)
- **Visualization**: Plotly (interactive charts)
- **Data Source**: SQLite database with cleaned FDA recall data
- **Styling**: Custom CSS for professional appearance
- **Performance**: Cached data loading for fast response

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure you have Python 3.8+ installed
python --version

# Install dependencies (already done with uv)
uv add streamlit plotly
```

### Launch Dashboard
```bash
# Navigate to project directory
cd /Users/jasen/dev/PackagingRecalls

# Launch the dashboard
streamlit run 3_data_dashboard/app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## 📈 Dashboard Sections

### 1. **Executive Summary**
- Key metrics at a glance
- Total recalls, cost impact, critical percentages
- High-level business intelligence

### 2. **FDA Classification Analysis**
- Pie chart showing Class I/II/III distribution
- Box plot analysis of cost impact by severity
- Regulatory compliance insights

### 3. **Defects Deep Dive**
- Horizontal bar chart of top primary defects
- Risk level distribution with color coding
- Quality control focus areas

### 4. **Temporal Trends**
- Monthly recall trends over time
- Annual breakdown by classification
- Seasonal pattern identification

### 5. **Business Intelligence**
- Key findings summary
- Strategic recommendations
- Actionable insights for decision makers

## 🎯 Business Value

### **For Regulatory Affairs**
- FDA classification trend analysis
- Risk assessment prioritization
- Compliance monitoring dashboard

### **For Quality Control**
- Defect pattern identification
- Cost impact analysis
- Prevention strategy development

### **For Executive Leadership**
- High-level KPI monitoring
- Strategic decision support
- Industry benchmark insights

### **For Data Analysts**
- Interactive data exploration
- Filtering and drill-down capabilities
- Export functionality for reports

## 🔧 Customization Options

### **Adding New Visualizations**
```python
def create_custom_chart(df):
    \"\"\"Add your custom visualization here\"\"\"
    fig = px.scatter(df, x='col1', y='col2', title="Custom Analysis")
    st.plotly_chart(fig, use_container_width=True)
```

### **Modifying Filters**
```python
# Add new filter in create_interactive_filters() function
new_filter = st.sidebar.selectbox(
    "New Filter",
    options=df['column_name'].unique()
)
```

### **Custom Styling**
- Modify the CSS in the `st.markdown()` section
- Add new color schemes
- Customize layout and spacing

## 📊 Data Sources

- **Primary Data**: FDA Enforcement Reports database
- **Processing**: Cleaned and enriched dataset (452 records)
- **Storage**: SQLite database for fast querying
- **Updates**: Real-time data refresh capabilities

## 🚀 Deployment Options

### **Local Development**
```bash
streamlit run 3_data_dashboard/app.py
```

### **Streamlit Cloud** (Free hosting)
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Deploy with one click

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install streamlit plotly pandas sqlite3
CMD ["streamlit", "run", "3_data_dashboard/app.py"]
```

## 🎨 Professional Portfolio Features

This dashboard demonstrates:

✅ **Data Visualization Expertise** - Interactive charts with Plotly  
✅ **Business Intelligence Skills** - KPIs, insights, recommendations  
✅ **Web Development** - Modern dashboard with Streamlit  
✅ **Data Engineering** - Database integration and processing  
✅ **UX/UI Design** - Professional styling and responsive layout  
✅ **Regulatory Knowledge** - FDA classification understanding  
✅ **Strategic Thinking** - Business value and actionable insights  

Perfect for showcasing data science and business intelligence capabilities!

## 📞 Support

For questions or customization requests, this dashboard demonstrates professional-level data visualization and business intelligence capabilities suitable for regulatory affairs, quality control, and executive decision-making roles.