import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import requests
import seaborn as sns

# Load the dataset
data = pd.read_csv('SPD_Crime_Data__2008-Present_20241122.csv')

# Convert date columns to datetime format
data['Offense Start DateTime'] = pd.to_datetime(data['Offense Start DateTime'], errors='coerce')
data['Year'] = data['Offense Start DateTime'].dt.year

# Remove rows with invalid or missing Year values
data = data.dropna(subset=['Year'])
data['Year'] = data['Year'].astype(int)

# Filter dataset for years after 2020
data = data[data['Year'] > 2020]

# Rename latitude and longitude columns to match Streamlit map requirements
data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'}, inplace=True)

# Set Streamlit layout
st.set_page_config(page_title="Seattle Crime Data", layout="wide")

# Title
st.title("Seattle Crime Data Visualization")

st.write("Visualization by Bhavita Vijay Bhoir, Rekha Kandukuri, Shefali Saxena and Vikramjeet Singh Kundu")

# Sidebar Filters
st.sidebar.header("Filter Data")
selected_year = st.sidebar.multiselect(
    "Select Year(s):",
    options=data['Year'].unique().tolist(),
    default=data['Year'].unique().tolist()
)
selected_precinct = st.sidebar.multiselect(
    "Select Precinct(s):",
    options=data['Precinct'].dropna().unique(),
    default=data['Precinct'].dropna().unique()
)
selected_category = st.sidebar.multiselect(
    "Select Crime Category:",
    options=data['Crime Against Category'].dropna().unique(),
    default=data['Crime Against Category'].dropna().unique()
)

# Filter Data
data_filtered = data[
    (data['Year'].isin(selected_year)) &
    (data['Precinct'].isin(selected_precinct)) &
    (data['Crime Against Category'].isin(selected_category))
]


# Crime Count by Precinct
st.header("Crime Count by Precinct")
precinct_chart = px.bar(
    data_filtered.groupby('Precinct').size().reset_index(name='Count'),
    x='Precinct',
    y='Count',
    title="Crime Count by Precinct",
    labels={'Count': 'Crime Count', 'Precinct': 'Police Precinct'},
    color='Precinct'
)
st.plotly_chart(precinct_chart, use_container_width=True)

# Crime Categories Over Time
st.header("Crime Categories Over Time")
time_series_chart = px.line(
    data_filtered.groupby(['Year', 'Crime Against Category']).size().reset_index(name='Count'),
    x='Year',
    y='Count',
    color='Crime Against Category',
    title="Crime Categories Over Time",
    labels={'Year': 'Year', 'Count': 'Crime Count', 'Crime Against Category': 'Category'},
    line_shape="linear"
)
time_series_chart.update_layout(xaxis=dict(type='category'))  # Force categorical x-axis
st.plotly_chart(time_series_chart, use_container_width=True)

st.write(''' 
         This visualization provides an interactive exploration of crime trends in Seattle, segmented by precinct and crime category. 
         The bar chart highlights the distribution of crime counts across precincts, while the line chart below shows trends in crime categories over time. 
         The dynamic filters on the sidebar allow users to customize their view by selecting specific years, precincts, or crime categories, enabling real-time updates to the charts.
        This interactivity ensures that users can tailor the insights to their specific interests and investigate patterns relevant to different timeframes or areas within the city.''')



# Fetch data from API
def fetch_crime_data(limit=10000):
    API_URL = "https://data.seattle.gov/resource/33kz-ixgy.json"
    params = {
        "$limit": limit,
        "$where": "blurred_longitude != '-1' AND blurred_latitude != '-1'",
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        data = pd.DataFrame(response.json())

        # Check for datetime column alternatives
        datetime_column = None
        if "event_clearance_date" in data.columns:
            datetime_column = "event_clearance_date"
        elif "original_time_queued" in data.columns:
            datetime_column = "original_time_queued"
        else:
            st.error("No datetime column found in the dataset.")
            return pd.DataFrame()

        # Process datetime column
        data[datetime_column] = pd.to_datetime(data[datetime_column], errors="coerce")
        data["hour"] = data[datetime_column].dt.hour
        data["month"] = data[datetime_column].dt.month
        data["year"] = data[datetime_column].dt.year
        data["am_pm"] = data["hour"].apply(lambda x: "AM" if x < 12 else "PM")
        return data
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()



# Visualization: Calls by Month (AM/PM)
def plot_911_calls_by_month(data):
    
    # Subheader (smaller)
    st.markdown("<h4 style='text-align: left; color: white;'>Number of 911 Calls per Month by AM or PM</h4>", unsafe_allow_html=True)
    
    # Chart
    month_grouped = data.groupby(["month", "am_pm"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(14, 8))
    month_grouped.plot(kind="bar", stacked=True, colormap="coolwarm", ax=ax)
    ax.set_title("Number of 911 Calls per Month by AM or PM", fontsize=16, color="white")
    ax.set_xlabel("Month", fontsize=16, color="white")
    ax.set_ylabel("Number of Calls", fontsize=16, color="white")
    ax.set_xticks(range(12))
    ax.set_xticklabels(range(1, 13), fontsize=14, color="white")
    ax.legend(title="AM or PM", fontsize=14, facecolor="black", edgecolor="white", labelcolor="white", title_fontsize=14)
    ax.tick_params(colors="white")
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    st.pyplot(fig)


# Visualization: Calls by Year
def plot_911_calls_by_year(data):
    
    # Subheader (smaller)
    st.markdown("<h4 style='text-align: left; color: white;'>911 Calls by Year</h4>", unsafe_allow_html=True)
    
    # Chart
    year_grouped = data.groupby("year").size()
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.plot(year_grouped.index, year_grouped.values, marker="o", linestyle="-", color="b", linewidth=2)
    ax.set_title("911 Calls by Year", fontsize=16, color="white")
    ax.set_xlabel("Year", fontsize=16, color="white")
    ax.set_ylabel("Number of Calls", fontsize=16, color="white")
    ax.grid(alpha=0.3, color="white")
    ax.tick_params(axis="x", labelsize=14, colors="white")
    ax.tick_params(axis="y", labelsize=14, colors="white")
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    st.pyplot(fig)


# Visualization: Calls by Priority and Precinct
def plot_calls_by_priority_and_precinct(data):
   
    # Subheader (smaller)
    st.markdown("<h4 style='text-align: left; color: white;'>911 Calls by Precinct and Priority</h4>", unsafe_allow_html=True)
    
    # Chart
    priority_precinct_grouped = data.groupby(["precinct", "priority"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(16, 10))
    priority_precinct_grouped.plot(kind="bar", stacked=True, colormap="viridis", ax=ax)
    ax.set_title("911 Calls by Precinct and Priority", fontsize=16, color="white")
    ax.set_xlabel("Precinct", fontsize=16, color="white")
    ax.set_ylabel("Number of Calls", fontsize=16, color="white")
    ax.tick_params(axis="x", labelrotation=0, labelsize=14, colors="white")
    ax.tick_params(axis="y", labelsize=14, colors="white")
    ax.set_facecolor("black")
    fig.patch.set_facecolor("black")
    legend = ax.legend(title="Priority", fontsize=14)
    legend.get_frame().set_facecolor("black")
    legend.get_frame().set_edgecolor("white")
    legend.set_title("Priority")
    legend.get_title().set_color("white")  # Set legend title color
    for text in legend.get_texts():
        text.set_color("white")  # Set legend label colors
    st.pyplot(fig)



# # Visualization: Calls by Precinct
# def plot_calls_by_precinct(data):
#     st.header("911 Calls by Precinct")
#     precinct_grouped = data.groupby("precinct").size()
#     fig, ax = plt.subplots(figsize=(16, 10))
#     precinct_grouped.plot(kind="bar", color="coral", ax=ax)
#     ax.set_title("911 Calls by Precinct", fontsize=20)
#     ax.set_xlabel("Precinct", fontsize=16)
#     ax.set_ylabel("Number of Calls", fontsize=16)
#     ax.tick_params(axis="x", labelrotation=0, labelsize=14)
#     st.pyplot(fig)



# Main Streamlit App
def main():
    st.header("Contextual Visualizations of Seattle 911 Calls")

    # Fetch data
    
    data = fetch_crime_data(limit=50000)

    if data.empty:
        st.error("No data available.")
        return

    # Visualizations
    plot_911_calls_by_month(data)
    st.write('''This stacked bar chart divides emergency calls into morning (AM) and evening (PM) categories for each month of the year.
              It reveals distinct temporal patterns in call volumes, with PM calls generally surpassing AM calls, potentially due to increased activity during later hours. 
             This chart enables us to pinpoint periods of high demand for emergency services, which can guide resource allocation.''')
    plot_911_calls_by_year(data)
    st.write('''The line chart illustrates annual variations in emergency call volumes. 
             Peaks and dips across the years may correlate with specific events or broader societal trends, such as the impact of the COVID-19 pandemic on public activity and safety concerns. 
             This historical perspective helps to understand changes in emergency response needs over time.''')
    # plot_calls_by_precinct(data)
    plot_calls_by_priority_and_precinct(data)
    st.write('''This stacked bar chart highlights the distribution of calls by precinct and their assigned priority levels. 
             By showcasing how precincts differ in the urgency and volume of calls, this visualization provides insight into regional disparities in emergency service demands. 
             For instance, a precinct with more high-priority calls might require additional resources to ensure adequate response times''')
    
    st.write('''While the main visualization explores crime trends segmented by precinct and category, the contextual visualizations add depth by focusing on emergency call patterns. This connection is crucial because the volume and type of emergency calls often align with crime trends, offering a complementary view of public safety dynamics. For instance, precincts with higher crime rates may also see an uptick in emergency calls, particularly in high-priority categories. Combining crime data with emergency call information allows for a multi-dimensional analysis of public safety.
              This integration can help policymakers and law enforcement prioritize resources based on both crime and emergency call patterns.
              For example, identifying months or precincts with elevated PM calls alongside specific crime categories can guide targeted interventions. ''')

    # Data Citations
    st.subheader("**Data Sources**")

    # Primary Dataset Info
    st.write("**1. Primary Dataset:**")
    st.write("Dataset: [Seattle Crime Data](https://data.seattle.gov/Public-Safety/SPD-Crime-Data-2008-Present/tazs-3rd5/about_data)")
    st.write("Obtained from: [data.seattle.gov](https://data.seattle.gov/)")
    st.write("License: 	Public Domain")

    # Contextual Dataset Info
    st.write("**2. Contextual Dataset:**")
    st.write("Dataset: [Seattle Calls Data](https://data.seattle.gov/Public-Safety/Call-Data/33kz-ixgy/data)")
    st.write("Obtained from: [data.seattle.gov](https://data.seattle.gov/)")
    st.write("License: Public Domain")

if __name__ == "__main__":
    main()