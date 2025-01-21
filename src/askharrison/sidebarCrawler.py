import requests
from bs4 import BeautifulSoup
import logging

# Set up logging to display in Jupyter Notebook
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class SidebarCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.data = {}
        self.source_soup = None

    def extract_sidebar(self, url):
        logger.info(f"Extracting sidebar from URL: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.source_soup = soup
        
        sidebars = soup.find_all(id=lambda x: x and 'sidebar' in x) + \
                   soup.find_all(class_=lambda x: x and 'sidebar' in x)
        
        if not sidebars:
            logger.warning(f"No sidebar found in URL: {url}")
            return
        
        for sidebar in sidebars:
            content = [item.get_text(strip=True) for item in sidebar.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
            links = [a['href'] for a in sidebar.find_all('a', href=True) if a['href'].startswith('http')]
            
            self.data[url] = {
                'content': content,
                'links': links
            }
            
            for link in links:
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    self.extract_sidebar(link)

    def extract_from_lists(self, url):
        logger.info(f"Extracting list elements from URL: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        lists = soup.find_all(['ul', 'ol'])
        logger.info(f"Found {len(lists)} lists in URL: {url}")
        return lists

        for lst in lists:
            content = [item.get_text(strip=True) for item in lst.find_all('li')]
            logger.debug(f"Found {len(content)} list elements in URL: {url}")
            links = [a['href'] for a in lst.find_all('a', href=True) if a['href'].startswith('http')]
            if content or links:
                if url not in self.data:
                    self.data[url] = {'content': [], 'links': []}
                
                self.data[url]['content'].extend(content)
                self.data[url]['links'].extend(links)

                for link in links:
                    if link not in self.visited_urls:
                        self.visited_urls.add(link)
                        self.extract_from_lists(link)

    def crawl(self, start_url):
        logger.info(f"Starting crawl from URL: {start_url}")
        self.visited_urls.add(start_url)
        self.extract_from_lists(start_url)
        return self.data