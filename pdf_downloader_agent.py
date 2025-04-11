import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

class PDFDownloaderAgent:
    def __init__(self, download_folder):
        """
        Initialize the PDF Downloader Agent
        
        Args:
            download_folder (str): Path to the folder where PDFs will be saved
        """
        self.download_folder = os.path.abspath(download_folder)
        self.download_counter = 0
        self.driver = None
        
        # Create download folder if it doesn't exist
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Setup Chrome options
        self._setup_browser()
        
    def _setup_browser(self):
        """
        Configure and initialize the Chrome browser
        """
        chrome_options = Options()
        
        # Add general options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        # Set download preferences
        prefs = {
            "download.default_directory": self.download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # Ensure PDFs are downloaded, not opened
            "safebrowsing.enabled": False  # Disable safe browsing to avoid download warnings
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Disable the "Save As" dialog for downloads
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        try:
            # Initialize the Chrome driver with the ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
        except Exception as e:
            print(f"Error setting up Chrome driver with ChromeDriverManager: {e}")
            print("Falling back to default Chrome driver...")
            try:
                # Try with default ChromeDriver
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"Error with default Chrome driver: {e2}")
                raise Exception("Could not initialize Chrome driver")
        
    def navigate_to_url(self, url):
        """
        Navigate to the specified URL
        
        Args:
            url (str): URL to navigate to
        """
        print(f"Navigating to {url}")
        try:
            self.driver.get(url)
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Page loaded successfully")
        except TimeoutException:
            print("Page load timed out, but continuing anyway")
        except Exception as e:
            print(f"Error navigating to URL: {e}")
        
    def find_pdf_links(self):
        """
        Find all PDF links on the page using multiple selectors
        
        Returns:
            list: List of WebElement objects representing PDF links
        """
        pdf_links = []
        selectors = [
            "a[href$='.pdf']",
            "a.pdf-icon",
            "a img[src*='pdf']",
            "a[href*='pdf']",
            "img[src*='pdf']",
            "a[onclick*='pdf']"
        ]
        
        print("Searching for PDF links...")
        for selector in selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    print(f"Found {len(links)} links with selector: {selector}")
                    pdf_links.extend(links)
            except Exception as e:
                print(f"Error finding links with selector {selector}: {e}")
        
        # Also try XPath for more complex cases
        try:
            xpath_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'pdf') or contains(@onclick, 'pdf')]")
            if xpath_links:
                print(f"Found {len(xpath_links)} links with XPath")
                # Add only unique elements
                for link in xpath_links:
                    if link not in pdf_links:
                        pdf_links.append(link)
        except Exception as e:
            print(f"Error finding links with XPath: {e}")
        
        # Remove duplicates and clean the list
        unique_links = []
        for link in pdf_links:
            if link.is_displayed() and link not in unique_links:
                unique_links.append(link)
        
        print(f"Total unique PDF links found: {len(unique_links)}")
        return unique_links
    
    def download_pdfs(self):
        """
        Download PDF files directly
        """
        pdf_links = self.find_pdf_links()
        
        if not pdf_links:
            print("No PDF links found on the page")
            return
        
        print(f"Starting to download {len(pdf_links)} PDFs...")
        
        for i, link in enumerate(pdf_links):
            try:
                # Get the href attribute or onclick attribute that contains the PDF URL
                pdf_url = None
                
                try:
                    pdf_url = link.get_attribute('href')
                except:
                    pass
                
                if not pdf_url:
                    try:
                        onclick = link.get_attribute('onclick')
                        if onclick and 'pdf' in onclick.lower():
                            # Try to extract URL from onclick attribute
                            import re
                            match = re.search(r"window\.open\(['\"](.+?pdf)['\"]", onclick)
                            if match:
                                pdf_url = match.group(1)
                    except:
                        pass
                
                if not pdf_url and link.tag_name == 'img':
                    # If the link is an image, try to get href from parent
                    try:
                        parent = self.driver.execute_script("return arguments[0].parentNode;", link)
                        pdf_url = parent.get_attribute('href')
                    except:
                        pass
                
                if not pdf_url:
                    print(f"Could not find PDF URL for link #{i+1}, skipping...")
                    continue
                
                if not pdf_url.lower().endswith('.pdf') and 'pdf' not in pdf_url.lower():
                    print(f"URL doesn't seem to be a PDF: {pdf_url}, skipping...")
                    continue
                
                # Download the PDF
                self.download_counter += 1
                print(f"\nDownloading PDF #{self.download_counter} from: {pdf_url}")
                
                # Create a new tab for downloading
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # Navigate to the PDF URL
                self.driver.get(pdf_url)
                
                # Wait for the download to start
                time.sleep(3)
                
                # Close the tab and go back to the main tab
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                # Rename the file (check for the newest file in the download directory)
                self.rename_latest_download(i)
                
                # Wait a bit before next download to avoid overwhelming the server
                time.sleep(2)
                
            except StaleElementReferenceException:
                print(f"Link #{i+1} is stale, skipping...")
                continue
            except Exception as e:
                print(f"Error downloading PDF from link #{i+1}: {e}")
                continue
    
    def rename_latest_download(self, index):
        """
        Rename the latest downloaded file
        
        Args:
            index (int): Index of the PDF link
        """
        try:
            # Get all PDF files in the download directory
            pdf_files = [f for f in os.listdir(self.download_folder) if f.endswith('.pdf') or f.endswith('.pdf.crdownload')]
            
            if not pdf_files:
                print("No PDF files found in download directory")
                return
            
            # Sort by modification time to get the most recent file
            pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_folder, x)), reverse=True)
            latest_file = pdf_files[0]
            
            # If the file is still being downloaded (.crdownload extension)
            if latest_file.endswith('.crdownload'):
                print("File is still downloading, waiting...")
                for _ in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    pdf_files = [f for f in os.listdir(self.download_folder) if f.endswith('.pdf') or f.endswith('.pdf.crdownload')]
                    if pdf_files:
                        pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_folder, x)), reverse=True)
                        latest_file = pdf_files[0]
                        if not latest_file.endswith('.crdownload'):
                            break
            
            if latest_file.endswith('.crdownload'):
                print("Download is taking too long, skipping renaming")
                return
            
            # Create a new filename with the counter prefix
            new_filename = f"{self.download_counter:03d}-{latest_file}"
            old_path = os.path.join(self.download_folder, latest_file)
            new_path = os.path.join(self.download_folder, new_filename)
            
            # Try to rename the file
            try:
                os.rename(old_path, new_path)
                print(f"Renamed to: {new_filename}")
            except PermissionError:
                print("File is being used by another process, waiting...")
                time.sleep(5)
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed to: {new_filename}")
                except Exception as e:
                    print(f"Could not rename file after waiting: {e}")
            except Exception as e:
                print(f"Error renaming file: {e}")
                
        except Exception as e:
            print(f"Error in rename_latest_download: {e}")
    
    def close(self):
        """
        Close the browser and clean up
        """
        if self.driver:
            self.driver.quit()
            print("Browser closed")


def main():
    # Get the download folder path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_folder = os.path.join(script_dir, "downloads")
    
    # Create the PDF downloader agent
    agent = PDFDownloaderAgent(download_folder)
    
    try:
        # Navigate to the NIRF rankings page
        agent.navigate_to_url("https://www.nirfindia.org/Rankings/2024/EngineeringRanking.html")
        
        # Wait for the page to load completely
        time.sleep(5)
        
        # Download PDFs
        agent.download_pdfs()
        
        print("All PDFs downloaded successfully!")
    
    except Exception as e:
        print(f"Error in main function: {e}")
    
    finally:
        # Close the browser
        agent.close()


if __name__ == "__main__":
    main()