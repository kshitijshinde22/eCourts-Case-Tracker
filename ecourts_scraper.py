"""
Advanced eCourts Cause List Scraper with AI-powered features
Author: Your Name
Date: October 2024
"""

import os
import json
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, List, Optional
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class AdvancedECourtsScraper:
    """Advanced web scraper for Indian eCourts system with enhanced features"""
    
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Selenium WebDriver"""
        self.logger = logging.getLogger(__name__)
        self.setup_driver(headless)
        self.base_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
        self.session = requests.Session()
        self.create_directories()
        
    def setup_driver(self, headless: bool):
        """Setup Chrome WebDriver with optimal configurations"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Performance optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Download preferences
        prefs = {
            "download.default_directory": os.path.join(os.getcwd(), "downloads"),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self.logger.info("✓ WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize WebDriver: {e}")
            raise
    
    def create_directories(self):
        """Create necessary directories for storing data"""
        directories = ['downloads', 'results', 'logs', 'pdfs', 'analytics']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        self.logger.info("✓ Directories created")
    
    def get_states(self) -> Dict[str, str]:
        """Fetch all available states from eCourts portal"""
        try:
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
            
            self.logger.info(f"✓ Fetched {len(states)} states")
            return states
        except Exception as e:
            self.logger.error(f"✗ Error fetching states: {e}")
            return {}
    
    def get_districts(self, state_code: str) -> Dict[str, str]:
        """Fetch districts for a given state"""
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
            
            self.logger.info(f"✓ Fetched {len(districts)} districts")
            return districts
        except Exception as e:
            self.logger.error(f"✗ Error fetching districts: {e}")
            return {}
    
    def get_court_complexes(self, state_code: str, district_code: str) -> Dict[str, str]:
        """Fetch court complexes for a given district"""
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
            
            # Get court complexes
            complex_select = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, "court_complex_code"))
            ))
            
            complexes = {}
            for option in complex_select.options[1:]:
                complex_name = option.text.strip()
                complex_code = option.get_attribute("value")
                if complex_name and complex_code:
                    complexes[complex_name] = complex_code
            
            self.logger.info(f"✓ Fetched {len(complexes)} court complexes")
            return complexes
        except Exception as e:
            self.logger.error(f"✗ Error fetching court complexes: {e}")
            return {}
    
    def get_courts(self, complex_code: str) -> Dict[str, str]:
        """Fetch courts for a given complex"""
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
            
            self.logger.info(f"✓ Fetched {len(courts)} courts")
            return courts
        except Exception as e:
            self.logger.error(f"✗ Error fetching courts: {e}")
            return {}
    
    def download_cause_list(self, state_code: str, district_code: str, 
                          complex_code: str, court_code: str, 
                          date_str: str, court_name: str = "") -> Dict:
        """Download cause list PDF/HTML for specified parameters"""
        try:
            self.logger.info(f"Downloading cause list for {court_name} on {date_str}")
            
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
            
            # Select court complex
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
            
            # Click submit
            submit_btn = self.driver.find_element(By.XPATH, 
                "//button[@type='submit' and contains(text(), 'Go')]")
            submit_btn.click()
            time.sleep(4)
            
            # Try to download PDF or extract HTML
            result = self._process_cause_list_response(court_name, date_str)
            
            self.logger.info(f"✓ Successfully processed cause list for {court_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"✗ Error downloading cause list: {e}")
            return {"success": False, "error": str(e), "court_name": court_name}
    
    def _process_cause_list_response(self, court_name: str, date_str: str) -> Dict:
        """Process the cause list response (PDF or HTML)"""
        try:
            # Try to find PDF link
            pdf_links = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, '.pdf') or contains(text(), 'PDF') or contains(text(), 'Download')]")
            
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute("href")
                return self._download_pdf(pdf_url, court_name, date_str)
            
            # If no PDF, extract HTML content
            return self._extract_html_cause_list(court_name, date_str)
            
        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            return {"success": False, "error": str(e)}
    
    def _download_pdf(self, pdf_url: str, court_name: str, date_str: str) -> Dict:
        """Download PDF file"""
        try:
            response = self.session.get(pdf_url, timeout=30)
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
            self.logger.error(f"Error downloading PDF: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_html_cause_list(self, court_name: str, date_str: str) -> Dict:
        """Extract cause list data from HTML"""
        try:
            page_content = self.driver.page_source
            soup = BeautifulSoup(page_content, 'html.parser')
            
            cause_list = []
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:  # Has header and data
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
                # Save as JSON
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
                
                # Also create a formatted PDF
                pdf_path = self._create_formatted_pdf(data, court_name, date_str)
                
                return {
                    "success": True,
                    "type": "html",
                    "file": filename,
                    "path": filepath,
                    "pdf_path": pdf_path,
                    "total_cases": len(cause_list),
                    "court_name": court_name,
                    "date": date_str
                }
            else:
                return {
                    "success": False,
                    "error": "No cause list data found",
                    "court_name": court_name
                }
                
        except Exception as e:
            self.logger.error(f"Error extracting HTML: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_formatted_pdf(self, data: Dict, court_name: str, date_str: str) -> str:
        """Create a formatted PDF from cause list data"""
        try:
            filename = f"formatted_causelist_{court_name.replace(' ', '_')}_{date_str.replace('/', '-')}.pdf"
            filepath = os.path.join("pdfs", filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            title = Paragraph(f"Cause List - {court_name}", title_style)
            elements.append(title)
            elements.append(Paragraph(f"Date: {date_str}", styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Table data
            if data.get('cases'):
                table_data = []
                headers = list(data['cases'][0].keys())
                table_data.append(headers)
                
                for case in data['cases']:
                    row = [case.get(header, '') for header in headers]
                    table_data.append(row)
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
            
            doc.build(elements)
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating PDF: {e}")
            return ""
    
    def download_all_courts_cause_lists(self, state_code: str, district_code: str,
                                       complex_code: str, date_str: str) -> List[Dict]:
        """Download cause lists for all courts in a complex"""
        try:
            # Get list of courts
            courts = self.get_courts(complex_code)
            results = []
            
            self.logger.info(f"Starting bulk download for {len(courts)} courts")
            
            for i, (court_name, court_code) in enumerate(courts.items(), 1):
                self.logger.info(f"[{i}/{len(courts)}] Processing: {court_name}")
                
                result = self.download_cause_list(
                    state_code, district_code, complex_code,
                    court_code, date_str, court_name
                )
                
                results.append(result)
                time.sleep(2)  # Be respectful to server
            
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
                f"bulk_download_summary_{date_str.replace('/', '-')}.json")
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✓ Bulk download complete. Summary: {summary_file}")
            return results
            
        except Exception as e:
            self.logger.error(f"✗ Error in bulk download: {e}")
            return []
    
    def get_analytics(self) -> Dict:
        """Get analytics about downloaded cause lists"""
        try:
            analytics = {
                "total_pdfs": len([f for f in os.listdir("pdfs") if f.endswith('.pdf')]),
                "total_json": len([f for f in os.listdir("results") if f.endswith('.json')]),
                "disk_usage_mb": sum(
                    os.path.getsize(os.path.join("pdfs", f)) 
                    for f in os.listdir("pdfs")
                ) / (1024 * 1024),
                "last_download": max(
                    [os.path.getmtime(os.path.join("pdfs", f)) 
                     for f in os.listdir("pdfs")], 
                    default=0
                )
            }
            return analytics
        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return {}
    
    def close(self):
        """Close the browser and clean up"""
        try:
            self.driver.quit()
            self.logger.info("✓ Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")


if __name__ == "__main__":
    print("eCourts Advanced Scraper - Use with Flask app or CLI")
