import streamlit as st
import requests
import pandas as pd
import re

# Streamlit secret for the Datawrapper API token
api_token = st.secrets["DATAWRAPPER_API_TOKEN"]

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Function to create a chart
def create_chart(title, chart_type="d3-bars"):
    url = "https://api.datawrapper.de/v3/charts"
    data = {
        "title": title,
        "type": chart_type,
        "theme": "default"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['id']

# Function to upload data to a chart
def upload_data(chart_id, csv_data):
    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/data"
    response = requests.put(url, headers=headers, data=csv_data)
    return response.status_code

# Function to publish a chart
def publish_chart(chart_id):
    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/publish"
    response = requests.post(url, headers=headers)
    return response.json()

# Streamlit front-end
st.title("Weekly Report Visualizer")

# User input for the weekly report
weekly_report = st.text_area("Paste your weekly report here:")

if st.button("Generate Charts"):
    # Regular expressions for extracting data
    opinions_regex = re.compile(r"Opinions Users: ([\d\.]+) million \(up (\d+)%\)")
    pageviews_regex = re.compile(r"Pageviews for the site as a whole were up (\d+)% from the previous week")
    top_performers_regex = re.compile(r"Top Performers \(>60,000\)(.*?)Very Solid", re.DOTALL)
    solid_performers_regex = re.compile(r"Very Solid \(>33,000\)(.*?)Below 15,000", re.DOTALL)

    # Extracting opinions data
    opinions_match = opinions_regex.search(weekly_report)
    if opinions_match:
        opinions_users = float(opinions_match.group(1)) * 1e6
        opinions_growth = int(opinions_match.group(2))

    # Extracting pageviews data
    pageviews_match = pageviews_regex.search(weekly_report)
    if pageviews_match:
        pageviews_growth = int(pageviews_match.group(1))

    # Extracting top performers data
    top_performers_match = top_performers_regex.search(weekly_report)
    if top_performers_match:
        top_performers_data = top_performers_match.group(1).strip().split('\n')
        top_performers = []
        for item in top_performers_data:
            parts = item.split('—')
            title = parts[1].strip()
            views = int(parts[2].split()[0].replace(',', ''))
            top_performers.append({'title': title, 'views': views})

    # Extracting very solid performers data
    solid_performers_match = solid_performers_regex.search(weekly_report)
    if solid_performers_match:
        solid_performers_data = solid_performers_match.group(1).strip().split('\n')
        solid_performers = []
        for item in solid_performers_data:
            parts = item.split('—')
            title = parts[1].strip()
            views = int(parts[2].split()[0].replace(',', ''))
            solid_performers.append({'title': title, 'views': views})

    # Create and upload data for opinions chart
    opinions_chart_id = create_chart("Opinions Users Growth")
    opinions_csv = f"Category,Value\nUsers,{opinions_users}\nGrowth,{opinions_growth}"
    upload_data(opinions_chart_id, opinions_csv)
    publish_chart(opinions_chart_id)

    # Create and upload data for pageviews chart
    pageviews_chart_id = create_chart("Site Pageviews Growth")
    pageviews_csv = f"Category,Value\nGrowth,{pageviews_growth}"
    upload_data(pageviews_chart_id, pageviews_csv)
    publish_chart(pageviews_chart_id)

    # Create and upload data for top performers chart
    top_performers_chart_id = create_chart("Top Performers (>60,000)")
    top_performers_df = pd.DataFrame(top_performers)
    top_performers_csv = top_performers_df.to_csv(index=False)
    upload_data(top_performers_chart_id, top_performers_csv)
    publish_chart(top_performers_chart_id)

    # Create and upload data for very solid performers chart
    solid_performers_chart_id = create_chart("Very Solid Performers (>33,000)")
    solid_performers_df = pd.DataFrame(solid_performers)
    solid_performers_csv = solid_performers_df.to_csv(index=False)
    upload_data(solid_performers_chart_id, solid_performers_csv)
    publish_chart(solid_performers_chart_id)

    st.success("Charts generated successfully!")
