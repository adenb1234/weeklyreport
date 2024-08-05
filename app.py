import streamlit as st
import requests
import pandas as pd
import re
import io

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
    response.raise_for_status()
    return response.json()['id']

# Function to upload data to a chart
def upload_data(chart_id, csv_data):
    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/data"
    csv_headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "text/csv"
    }
    response = requests.put(url, headers=csv_headers, data=csv_data.encode('utf-8'))
    if response.status_code not in [204, 201]:
        st.write(f"Error uploading data: {response.status_code}")
        st.write(response.text)
        response.raise_for_status()
    else:
        st.write(f"Data uploaded successfully: {response.status_code}")
    return response.status_code

# Function to publish a chart
def publish_chart(chart_id):
    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/publish"
    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        st.write(f"Error publishing chart: {response.status_code}")
        st.write(response.text)
    response.raise_for_status()
    return response.json()

# Streamlit front-end
st.title("Weekly Report Visualizer")

# User input for the weekly report
weekly_report = st.text_area("Paste your weekly report here:")

if st.button("Generate Charts"):
    try:
        # Regular expressions for extracting data
        opinions_regex = re.compile(r"Opinions Users: ([\d\.]+) million \(up (\d+)%\)")
        pageviews_regex = re.compile(r"Pageviews for the site as a whole were up (\d+)% from the previous week")
        top_performers_regex = re.compile(r"Top Performers \(>60,000\)(.*?)Very Solid", re.DOTALL)
        solid_performers_regex = re.compile(r"Very Solid \(>33,000\)(.*?)Below 15,000", re.DOTALL)

        # Extracting opinions data
        opinions_match = opinions_regex.search(weekly_report)
        if opinions_match:
            opinions_users = float(opinions_match.group(1))
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
        opinions_df = pd.DataFrame({'Category': ['Users', 'Growth'], 'Value': [opinions_users, opinions_growth]})
        opinions_csv = opinions_df.to_csv(index=False)
        upload_data(opinions_chart_id, opinions_csv)
        opinions_publish_response = publish_chart(opinions_chart_id)

        # Create and upload data for pageviews chart
        pageviews_chart_id = create_chart("Site Pageviews Growth")
        pageviews_df = pd.DataFrame({'Category': ['Growth'], 'Value': [pageviews_growth]})
        pageviews_csv = pageviews_df.to_csv(index=False)
        upload_data(pageviews_chart_id, pageviews_csv)
        pageviews_publish_response = publish_chart(pageviews_chart_id)

        # Create and upload data for top performers chart
        top_performers_chart_id = create_chart("Top Performers (>60,000)")
        top_performers_df = pd.DataFrame(top_performers)
        top_performers_csv = top_performers_df.to_csv(index=False)
        upload_data(top_performers_chart_id, top_performers_csv)
        top_performers_publish_response = publish_chart(top_performers_chart_id)

        # Create and upload data for very solid performers chart
        solid_performers_chart_id = create_chart("Very Solid Performers (>33,000)")
        solid_performers_df = pd.DataFrame(solid_performers)
        solid_performers_csv = solid_performers_df.to_csv(index=False)
        upload_data(solid_performers_chart_id, solid_performers_csv)
        solid_performers_publish_response = publish_chart(solid_performers_chart_id)

        # Display the chart URLs
        st.success("Charts generated successfully!")
        st.write("Opinions Users Growth Chart URL:", opinions_publish_response.get('publicUrl', 'No URL found'))
        st.write("Site Pageviews Growth Chart URL:", pageviews_publish_response.get('publicUrl', 'No URL found'))
        st.write("Top Performers Chart URL:", top_performers_publish_response.get('publicUrl', 'No URL found'))
        st.write("Very Solid Performers Chart URL:", solid_performers_publish_response.get('publicUrl', 'No URL found'))

        # Debugging information
        st.write("Opinions Publish Response:", opinions_publish_response)
        st.write("Pageviews Publish Response:", pageviews_publish_response)
        st.write("Top Performers Publish Response:", top_performers_publish_response)
        st.write("Very Solid Performers Publish Response:", solid_performers_publish_response)

    except requests.exceptions.RequestException as e:
        st.error(f"HTTP error occurred: {e}")
        st.write("Response content:", e.response.text if e.response else "No response content")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        import traceback
        st.write("Traceback:", traceback.format_exc())
