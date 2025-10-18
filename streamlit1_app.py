import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd

# Create necessary folders
for folder in ["downloads", "results", "pdfs"]:
    os.makedirs(folder, exist_ok=True)

st.title("eCourts Case Tracker")

# Input form
with st.form("case_search"):
    court_state = st.text_input("State / Court Name (e.g., Maharashtra)")
    case_number = st.text_input("Case Number")
    year = st.text_input("Year")
    submitted = st.form_submit_button("Search Case")

if submitted:
    if not court_state or not case_number or not year:
        st.error("Please fill in all fields.")
    else:
        st.info("Fetching case details...")

        # Sample eCourts search URL (modify based on actual endpoint)
        search_url = "https://ecourts.gov.in/ecourts_home/case_status/search_cases_c.php"
        params = {
            "state": court_state,
            "case_no": case_number,
            "year": year
        }

        try:
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Example: Extract case status table
                table = soup.find("table")
                if table:
                    df = pd.read_html(str(table))[0]
                    st.subheader("Case Details")
                    st.dataframe(df)

                    # Optional: Save locally
                    df.to_csv(f"results/case_{case_number}_{year}.csv", index=False)
                    st.success(f"Results saved in results/case_{case_number}_{year}.csv")
                else:
                    st.warning("No case details found.")
            else:
                st.error(f"Failed to fetch data. Status code: {response.status_code}")

        except Exception as e:
            st.error(f"Error fetching case details: {e}")
