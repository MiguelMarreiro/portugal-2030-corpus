import os
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
from database import Call
from datetime import datetime
from playwright.sync_api import sync_playwright


class StaticCrawler:
    def __init__(self, output_dir="data/raw"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Portugal2030CorpusBot/1.0 (Research purpose)'
        })

    def download_file(self, url, filename=None):
        """Downloads a static file (PDF/HTML) to the raw directory."""
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = "index.html"
                
        # Avoid overriding files easily if they have the same name
        safe_filename = filename.replace('/', '_').replace('?', '_').replace('=', '_')
        filepath = os.path.join(self.output_dir, safe_filename)

        print(f"Downloading {url} to {filepath}")
        try:
            time.sleep(1) # Respectful rate limit
            response = self.session.get(url, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def scrape_with_playwright(self, url, selector="body"):
        """Fallback for complex/dynamic sources."""
        print(f"Playwright fallback: fetching {url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                content = page.locator(selector).inner_text() if page.locator(selector).count() > 0 else page.locator("body").inner_text()
                browser.close()
                return content
        except Exception as e:
            print(f"Playwright error on {url}: {e}")
            return None


class DynamicCallTracker:
    """
    Tracks calls (Avisos) from sources like Compete 2030.
    Since we are using standard libraries right now, we will simulate
    a generic HTML table scraper for Avisos that can be adapted
    to use Playwright or APIs if needed later.
    """
    def __init__(self, db_session):
        self.db = db_session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Portugal2030CorpusBot/1.0 (Research purpose)'
        })

    def fetch_compete_avisos(self, url="https://compete2030.gov.pt/avisos/"):
        """
        Sample implementation of Avisos fetching.
        (Note: The actual Compete 2030 site might require JS rendering,
        in which case we will switch to Playwright. This is a placeholder structure).
        """
        print(f"Fetching Avisos from {url}")
        try:
            time.sleep(1)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract calls from Compete 2030 HTML structure
            articles = soup.find_all('article')
            if not articles:
                # Fallback to div cards if article tags aren't used
                articles = soup.find_all('div', class_=lambda c: c and 'card' in c)

            for article in articles:
                title_tag = article.find(['h2', 'h3'])
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                link_tag = article.find('a', href=True)
                link = link_tag['href'] if link_tag else url
                
                # Heuristic: usually title starts with "Aviso N.º XYZ"
                call_code = title.split()[0] if "Aviso" in title else f"COMP-{abs(hash(title)) % 10000}"
                
                call_data = {
                    "call_code": call_code,
                    "title": title,
                    "status": "Aberto", # Placeholder status
                    "link": link,
                    "budget": "Consulte o Aviso",
                    "instrument": "COMPETE 2030"
                }
                self._upsert_call(call_data)

        except Exception as e:
            print(f"Error fetching calls from {url}: {e}")

    def fetch_norte2030_avisos(self, url="https://www.norte2030.pt/concursos/"):
        """Sample expansion for Norte 2030 Avisos"""
        print(f"Fetching Avisos from {url}")
        try:
            time.sleep(1)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Note: Norte 2030 might use different classes
            articles = soup.find_all('article')
            for article in articles:
                title_tag = article.find(['h2', 'h3'])
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                link_tag = article.find('a', href=True)
                link = link_tag['href'] if link_tag else url
                call_code = f"NORTE-{abs(hash(title)) % 10000}"
                
                self._upsert_call({
                    "call_code": call_code,
                    "title": title,
                    "status": "Aberto",
                    "link": link,
                    "budget": "Consulte o Aviso",
                    "instrument": "NORTE 2030"
                })
        except Exception as e:
            print(f"Error fetching calls from {url}: {e}")

    def _upsert_call(self, call_data):
        existing = self.db.query(Call).filter_by(call_code=call_data["call_code"]).first()
        if existing:
            existing.title = call_data.get("title", existing.title)
            existing.status = call_data.get("status", existing.status)
            existing.link = call_data.get("link", existing.link)
            existing.budget = call_data.get("budget", existing.budget)
            existing.instrument = call_data.get("instrument", existing.instrument)
            print(f"Updated Call: {existing.call_code}")
        else:
            new_call = Call(
                call_code=call_data["call_code"],
                title=call_data.get("title"),
                status=call_data.get("status"),
                link=call_data.get("link"),
                budget=call_data.get("budget"),
                instrument=call_data.get("instrument")
            )
            self.db.add(new_call)
            print(f"Added New Call: {new_call.call_code}")
        
        self.db.commit()

class DiarioDaRepublicaSpider:
    def __init__(self, output_dir="data/raw"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def scrape_legislation(self, url):
        print(f"Scraping dynamic legislation from {url}")
        parsed = urlparse(url)
        filename = f"dr_{os.path.basename(parsed.path)}.txt"
        filepath = os.path.join(self.output_dir, filename)

        if os.path.exists(filepath):
            print(f"Already downloaded: {filepath}")
            return filepath

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                
                # DRE uses specific IDs or classes for the consolidated text
                content_locator = page.locator("#legislacao-consolidada, .texto-integral, article")
                if content_locator.count() > 0:
                    text_content = content_locator.first.inner_text()
                else:
                    text_content = page.locator("body").inner_text()
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Source: {url}\n\n{text_content}")
                    
                browser.close()
                return filepath
        except Exception as e:
            print(f"Error in DiarioDaRepublicaSpider: {e}")
            return None

class IapmeiSpider(StaticCrawler):
    def scrape_concursos(self, url="https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Incentivos-Financiamento/Sistemas-de-Incentivos/Concursos-abertos.aspx"):
        print(f"Scraping IAPMEI Concursos from {url}")
        try:
            time.sleep(1)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            downloaded = []
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                text = a.text.lower()
                if '.pdf' in href and ('guia' in text or 'formulário' in text or 'aviso' in text):
                    full_link = urljoin(url, a['href'])
                    print(f"Found IAPMEI guide: {full_link}")
                    path = self.download_file(full_link)
                    if path:
                        downloaded.append(path)
            
            return downloaded
        except Exception as e:
            print(f"Error in IapmeiSpider: {e}")
            return []

class PrrSpider(StaticCrawler):
    def fetch_manuals(self, urls):
        print(f"Fetching PRR manuals from {len(urls)} links.")
        downloaded = []
        for url in urls:
            print(f"Inspecting PRR source: {url}")
            try:
                if url.endswith('.pdf'):
                    path = self.download_file(url)
                    if path:
                        downloaded.append(path)
                else:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if 'wp-content/uploads' in href and href.endswith('.pdf'):
                            full_link = urljoin(url, href)
                            path = self.download_file(full_link)
                            if path:
                                downloaded.append(path)
            except Exception as e:
                print(f"Error fetching PRR URL {url}: {e}")
                
        return downloaded

class BalcaoFundosSpider(StaticCrawler):
    def scrape_faq(self, url="https://portugal2030.pt/ajuda-arquivo/"):
        print(f"Scraping Balcão dos Fundos FAQ from {url}")
        try:
            time.sleep(1)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            filepath = os.path.join(self.output_dir, "balcao_faq.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Source: {url}\n\n")
                # WordPress standard loops often use <article>
                articles = soup.find_all('article')
                for article in articles:
                    title = article.find(['h2', 'h3'])
                    content = article.find('div', class_='entry-content')
                    if title:
                        f.write(f"Q: {title.get_text(strip=True)}\n")
                    if content:
                        f.write(f"A: {content.get_text(strip=True)}\n\n")
            return filepath
        except Exception as e:
            print(f"Error in BalcaoFundosSpider: {e}")
            return None

class AcademicResearchSpider(StaticCrawler):
    def fetch_research(self, urls):
        print(f"Fetching Academic Research from {len(urls)} links.")
        downloaded = []
        for url in urls:
            try:
                path = self.download_file(url)
                if path:
                    downloaded.append(path)
            except Exception as e:
                print(f"Error fetching research {url}: {e}")
        return downloaded

class BlogSpider(StaticCrawler):
    def scrape_blog(self, url):
        print(f"Scraping Blog from {url}")
        parsed = urlparse(url)
        filename = f"blog_{parsed.netloc}_{os.path.basename(parsed.path)}.txt"
        filepath = os.path.join(self.output_dir, filename.replace('/', '_'))

        # Try requests first
        content = None
        try:
            time.sleep(1)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('article') or soup.find('main') or soup.find('body')
            content = article.get_text(separator='\n', strip=True) if article else ""
            
            # If content is too short, fallback to playwright
            if len(content) < 500:
                print("Content too short, falling back to Playwright...")
                content = self.scrape_with_playwright(url)
        except Exception as e:
            print(f"Requests failed, trying Playwright: {e}")
            content = self.scrape_with_playwright(url)
            
        if content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Source: {url}\n\n{content}")
            return filepath
        return None

class MethodologySpider(StaticCrawler):
    def fetch_methodologies(self, urls):
        print(f"Fetching Methodologies from {len(urls)} links.")
        downloaded = []
        for url in urls:
            try:
                if url.endswith('.pdf'):
                    path = self.download_file(url)
                    if path:
                        downloaded.append(path)
                else:
                    path = self.scrape_with_playwright(url)
                    if path:
                        # Write to file
                        filename = f"methodology_{abs(hash(url))}.txt"
                        filepath = os.path.join(self.output_dir, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(f"Source: {url}\n\n{path}")
                        downloaded.append(filepath)
            except Exception as e:
                print(f"Error fetching methodology {url}: {e}")
        return downloaded

if __name__ == "__main__":
    from database import init_db
    db = init_db()
    tracker = DynamicCallTracker(db)
    tracker.fetch_compete_avisos()
