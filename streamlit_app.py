"""
eCourts Intelligence - Streamlit Version
Advanced Cause List Scraper
Author: Your Name
"""

import streamlit as st
import os
import json
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import base64

# Page Configuration
st.set_page_config(
    page_title="eCourts Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    h1, h2, h3 {
        color: #f1f5f9 !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        font-weight: 600;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
    }
    
    .success-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #f1f5f9;
    }
    
    .error-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #f1f5f9;
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%);
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #f1f5f9;
    }
    
    .metric-card {
        background: rgba(19, 24, 41, 0.8);
        border: 1px solid #1e293b;
        border-radius: 0.75rem;
        padding: 1.5rem;
        text-align: center;
    }
    
    .stSelectbox label, .stTextInput label {
        color: #94a3b8 !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'states' not in st.session_state:
    st.session_state.states = {}
if 'districts' not in st.session_state:
    st.session_state.districts = {}
if 'complexes' not in st.session_state:
    st.session_state.complexes = {}
if 'courts' not in st.session_state:
    st.session_state.courts = {}
if 'download_history' not in st.session_state:
    st.session_state.download_history = []

# Create directories
os.makedirs('downloads', exist_ok=True)
os.makedirs('results', exist_ok=True)
os.makedirs('pdfs', exist_ok=True)

class ECourtsScraper:
    """Streamlit-optimized eCourts scraper"""
    
    def __init__(self):
        self.base_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Setup Chrome WebDriver for Streamlit Cloud"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            try:
                # For Streamlit Cloud
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                self.wait = WebDriverWait(self.driver, 20)
            except Exception as e:
                st.error(f"Failed to initialize browser: {str(e)}")
                return False
        return True
    
    def get_states(self):
        """Fetch all states"""
        try:
            if not self.setup_driver():
                return {}
            
            self.driver.get(f"{self.base_url}?p=cause_list/")
            time.sleep(3)
            
            state_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "sess_state_code"))
            ))
            
            states = {}
            for option in state_select.options[1:]:
                state_name = option.text.strip()
                state_code = option.get_attribute("value")
                if state_name and state_code:
                    states[state_name] = state_code
            
            return states
        except Exception as e:
            st.error(f"Error fetching states: {str(e)}")
            return {}
    
    def get_districts(self, state_code):
        """Fetch districts for a state"""
        try:
            time.sleep(2)
            district_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "sess_dist_code"))
            ))
            
            districts = {}
            for option in district_select.options[1:]:
                district_name = option.text.strip()
                district_code = option.get_attribute("value")
                if district_name and district_code:
                    districts[district_name] = district_code
            
            return districts
        except Exception as e:
            st.error(f"Error fetching districts: {str(e)}")
            return {}
    
    def get_court_complexes(self, state_code, district_code):
        """Fetch court complexes"""
        try:
            # Select state
            state_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "sess_state_code"))
            ))
            state_select.select_by_value(state_code)
            time.sleep(2)
            
            # Select district
            district_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "sess_dist_code"))
            ))
            district_select.select_by_value(district_code)
            time.sleep(2)
            
            # Get complexes
            complex_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "court_complex_code"))
            ))
            
            complexes = {}
            for option in complex_select.options[1:]:
                complex_name = option.text.strip()
                complex_code = option.get_attribute("value")
                if complex_name and complex_code:
                    complexes[complex_name] = complex_code
            
            return complexes
        except Exception as e:
            st.error(f"Error fetching court complexes: {str(e)}")
            return {}
    
    def get_courts(self, complex_code):
        """Fetch courts for a complex"""
        try:
            time.sleep(2)
            court_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "court_code"))
            ))
            
            courts = {}
            for option in court_select.options[1:]:
                court_name = option.text.strip()
                court_code = option.get_attribute("value")
                if court_name and court_code:
                    courts[court_name] = court_code
            
            return courts
        except Exception as e:
            st.error(f"Error fetching courts: {str(e)}")
            return {}
    
    def download_cause_list(self, state_code, district_code, complex_code, 
                          court_code, date_str, court_name=""):
        """Download cause list"""
        try:
            # Navigate to cause list page
            self.driver.get(f"{self.base_url}?p=cause_list/")
            time.sleep(2)
            
            # Select state
            state_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "sess_state_code"))
            ))
            state_select.select_by_value(state_code)
            time.sleep(2)
            
            # Select district
            district_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "sess_dist_code"))
            ))
            district_select.select_by_value(district_code)
            time.sleep(2)
            
            # Select complex
            complex_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "court_complex_code"))
            ))
            complex_select.select_by_value(complex_code)
            time.sleep(2)
            
            # Select court
            court_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "court_code"))
            ))
            court_select.select_by_value(court_code)
            time.sleep(1)
            
            # Enter date
            date_input = self.driver.find_element(By.ID, "causelist_date")
            date_input.clear()
            date_input.send_keys(date_str)
            time.sleep(1)
            
            # Submit
            submit_btn = self.driver.find_element(By.XPATH, 
                "//button[@type='submit' and contains(text(), 'Go')]")
            submit_btn.click()
            time.sleep(4)
            
            # Try to download PDF
            return self._process_response(court_name, date_str)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "court_name": court_name
            }
    
    def _process_response(self, court_name, date_str):
        """Process the response"""
        try:
            # Try to find PDF link
            pdf_links = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, '.pdf')]")
            
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute("href")
                return self._download_pdf(pdf_url, court_name, date_str)
            
            # Extract HTML
            return self._extract_html(court_name, date_str)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _download_pdf(self, pdf_url, court_name, date_str):
        """Download PDF file"""
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            filename = f"causelist_{court_name.replace(' ', '_')}_{date_str.replace('/', '-')}.pdf"
            filepath = os.path.join("pdfs", filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return {
                "success": True,
                "type": "pdf",
                "file": filename,
                "path": filepath,
                "size": len(response.content),
                "court_name": court_name,
                "date": date_str
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_html(self, court_name, date_str):
        """Extract data from HTML"""
        try:
            page_content = self.driver.page_source
            soup = BeautifulSoup(page_content, 'html.parser')
            
            cause_list = []
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    headers = [th.text.strip() for th in rows[0].find_all(['th', 'td'])]
                    
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        if cols:
                            case_data = {}
                            for i, col in enumerate(cols):
                                header = headers[i] if i < len(headers) else f"Column_{i}"
                                case_data[header] = col.text.strip()
                            cause_list.append(case_data)
            
            if cause_list:
                filename = f"causelist_{court_name.replace(' ', '_')}_{date_str.replace('/', '-')}.json"
                filepath = os.path.join("results", filename)
                
                data = {
                    "court_name": court_name,
                    "date": date_str,
                    "cases": cause_list,
                    "total_cases": len(cause_list),
                    "extracted_at": datetime.now().isoformat()
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return {
                    "success": True,
                    "type": "json",
                    "file": filename,
                    "path": filepath,
                    "total_cases": len(cause_list),
                    "court_name": court_name,
                    "date": date_str,
                    "data": data
                }
            else:
                return {
                    "success": False,
                    "error": "No cause list data found",
                    "court_name": court_name
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_all_courts(self, state_code, district_code, complex_code, date_str):
        """Download all courts in a complex"""
        courts = self.get_courts(complex_code)
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (court_name, court_code) in enumerate(courts.items(), 1):
            status_text.text(f"Processing {i}/{len(courts)}: {court_name}")
            
            result = self.download_cause_list(
                state_code, district_code, complex_code,
                court_code, date_str, court_name
            )
            results.append(result)
            
            progress_bar.progress(i / len(courts))
            time.sleep(2)
        
        progress_bar.empty()
        status_text.empty()
        
        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "date": date_str,
            "total_courts": len(courts),
            "successful": sum(1 for r in results if r.get('success')),
            "failed": sum(1 for r in results if not r.get('success')),
            "results": results
        }
        
        summary_file = os.path.join("results", 
            f"bulk_summary_{date_str.replace('/', '-')}.json")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return results
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

# Main App
def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; background: linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            ⚖️ eCourts Intelligence
        </h1>
        <p style='color: #94a3b8; font-size: 1.25rem;'>Advanced Cause List Scraper with Real-time Data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <h2 style='color: #6366f1;'>{len(st.session_state.download_history)}</h2>
                <p style='color: #94a3b8; font-size: 0.875rem;'>Downloads</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            success_count = sum(1 for d in st.session_state.download_history if d.get('success'))
            success_rate = (success_count / len(st.session_state.download_history) * 100) if st.session_state.download_history else 0
            st.markdown(f"""
            <div class='metric-card'>
                <h2 style='color: #10b981;'>{success_rate:.0f}%</h2>
                <p style='color: #94a3b8; font-size: 0.875rem;'>Success</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### ✨ Features")
        st.markdown("""
        - 🔄 Real-time scraping
        - 📥 Single & bulk download
        - 📄 PDF & JSON exports
        - 📊 Analytics dashboard
        - 💾 Download history
        """)
    
    # Main Content
    tabs = st.tabs(["🔍 Scraper", "📁 Downloads", "📖 Guide"])
    
    # Tab 1: Scraper
    with tabs[0]:
        st.markdown("<div class='info-box'>Select court hierarchy to download cause lists</div>", 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Initialize scraper
            if st.button("🚀 Initialize Scraper", key="init"):
                with st.spinner("Initializing browser..."):
                    st.session_state.scraper = ECourtsScraper()
                    st.session_state.states = st.session_state.scraper.get_states()
                    if st.session_state.states:
                        st.success(f"✅ Loaded {len(st.session_state.states)} states")
                    else:
                        st.error("Failed to load states")
        
        with col2:
            # Date input
            date_input = st.text_input(
                "📅 Date (DD/MM/YYYY)",
                value=datetime.now().strftime("%d/%m/%Y")
            )
        
        if st.session_state.states:
            col1, col2 = st.columns(2)
            
            with col1:
                # State selection
                selected_state = st.selectbox(
                    "🗺️ Select State",
                    options=[""] + list(st.session_state.states.keys()),
                    index=0
                )
                
                if selected_state:
                    state_code = st.session_state.states[selected_state]
                    
                    # Load districts
                    if st.button("Load Districts", key="load_dist"):
                        with st.spinner("Loading districts..."):
                            st.session_state.districts = st.session_state.scraper.get_districts(state_code)
                            if st.session_state.districts:
                                st.success(f"✅ Loaded {len(st.session_state.districts)} districts")
                    
                    if st.session_state.districts:
                        selected_district = st.selectbox(
                            "🏙️ Select District",
                            options=[""] + list(st.session_state.districts.keys()),
                            index=0
                        )
                        
                        if selected_district:
                            district_code = st.session_state.districts[selected_district]
                            
                            # Load complexes
                            if st.button("Load Court Complexes", key="load_complex"):
                                with st.spinner("Loading court complexes..."):
                                    st.session_state.complexes = st.session_state.scraper.get_court_complexes(
                                        state_code, district_code
                                    )
                                    if st.session_state.complexes:
                                        st.success(f"✅ Loaded {len(st.session_state.complexes)} complexes")
            
            with col2:
                if st.session_state.complexes:
                    selected_complex = st.selectbox(
                        "🏛️ Select Court Complex",
                        options=[""] + list(st.session_state.complexes.keys()),
                        index=0
                    )
                    
                    if selected_complex:
                        complex_code = st.session_state.complexes[selected_complex]
                        
                        # Load courts
                        if st.button("Load Courts", key="load_courts"):
                            with st.spinner("Loading courts..."):
                                st.session_state.courts = st.session_state.scraper.get_courts(complex_code)
                                if st.session_state.courts:
                                    st.success(f"✅ Loaded {len(st.session_state.courts)} courts")
                        
                        if st.session_state.courts:
                            selected_court = st.selectbox(
                                "⚖️ Select Court",
                                options=[""] + list(st.session_state.courts.keys()),
                                index=0
                            )
                            
                            st.markdown("---")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                # Single download
                                if st.button("📥 Download Cause List", key="download_single"):
                                    if selected_court:
                                        court_code = st.session_state.courts[selected_court]
                                        
                                        with st.spinner(f"Downloading {selected_court}..."):
                                            result = st.session_state.scraper.download_cause_list(
                                                state_code, district_code, complex_code,
                                                court_code, date_input, selected_court
                                            )
                                            
                                            st.session_state.download_history.append(result)
                                            
                                            if result.get('success'):
                                                st.markdown(f"""
                                                <div class='success-box'>
                                                    <h4>✅ Success!</h4>
                                                    <p><strong>Court:</strong> {result['court_name']}</p>
                                                    <p><strong>File:</strong> {result['file']}</p>
                                                    {f"<p><strong>Cases:</strong> {result.get('total_cases', 'N/A')}</p>" if 'total_cases' in result else ''}
                                                </div>
                                                """, unsafe_allow_html=True)
                                            else:
                                                st.markdown(f"""
                                                <div class='error-box'>
                                                    <h4>❌ Failed</h4>
                                                    <p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    else:
                                        st.warning("Please select a court")
                            
                            with col_btn2:
                                # Bulk download
                                if st.button("📦 Download All Courts", key="download_all"):
                                    with st.spinner("Starting bulk download..."):
                                        results = st.session_state.scraper.download_all_courts(
                                            state_code, district_code, complex_code, date_input
                                        )
                                        
                                        st.session_state.download_history.extend(results)
                                        
                                        success_count = sum(1 for r in results if r.get('success'))
                                        
                                        st.markdown(f"""
                                        <div class='success-box'>
                                            <h4>✅ Bulk Download Complete!</h4>
                                            <p><strong>Successful:</strong> {success_count}/{len(results)}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
    
    # Tab 2: Downloads
    with tabs[1]:
        st.markdown("### 📁 Downloaded Files")
        
        # List PDFs
        if os.path.exists("pdfs"):
            pdfs = [f for f in os.listdir("pdfs") if f.endswith('.pdf')]
            
            if pdfs:
                st.markdown(f"**PDF Files ({len(pdfs)})**")
                for pdf in pdfs:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📄 {pdf}")
                    with col2:
                        with open(os.path.join("pdfs", pdf), "rb") as file:
                            st.download_button(
                                label="Download",
                                data=file,
                                file_name=pdf,
                                mime="application/pdf",
                                key=f"download_pdf_{pdf}"
                            )
            else:
                st.info("No PDF files downloaded yet")
        
        st.markdown("---")
        
        # List JSON files
        if os.path.exists("results"):
            jsons = [f for f in os.listdir("results") if f.endswith('.json')]
            
            if jsons:
                st.markdown(f"**JSON Files ({len(jsons)})**")
                for json_file in jsons:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📋 {json_file}")
                    with col2:
                        with open(os.path.join("results", json_file), "rb") as file:
                            st.download_button(
                                label="Download",
                                data=file,
                                file_name=json_file,
                                mime="application/json",
                                key=f"download_json_{json_file}"
                            )
            else:
                st.info("No JSON files saved yet")
    
    # Tab 3: Guide
    with tabs[2]:
        st.markdown("""
        ### 📖 How to Use
        
        1. **Initialize Scraper**: Click 'Initialize Scraper' to start
        2. **Select State**: Choose your state from dropdown
        3. **Load Districts**: Click to load districts
        4. **Select District**: Choose district
        5. **Load Complexes**: Click to load court complexes
        6. **Select Complex**: Choose court complex
        7. **Load Courts**: Click to load courts
        8. **Select Court**: Choose specific court
        9. **Download**: Click 'Download Cause List' for single or 'Download All Courts' for bulk
        
        ### ✨ Features
        
        - **Real-time Data**: Fetches live data from eCourts
        - **Bulk Download**: Download all courts at once
        - **PDF Export**: Direct PDF downloads when available
        - **JSON Backup**: Structured data saved as JSON
        - **Progress Tracking**: Visual progress for bulk operations
        - **Download History**: Track all downloads
        
        ### ⚠️ Important Notes
        
        - Browser initialization may take 30-60 seconds
        - Each court takes 5-10 seconds to process
        - Bulk downloads process all courts sequentially
        - Files are saved in 'pdfs' and 'results' folders
        """)

if __name__ == "__main__":
    main()
