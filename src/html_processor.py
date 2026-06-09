from bs4 import BeautifulSoup
import re

class HTMLProcessor:
    def process_html(self, filepath):
        """
        Reads an HTML file, cleans it, and returns structured markdown/text.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, navs, footers
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Try to find main content
        main_content = soup.find('main') or soup.find('article') or soup.body
        if not main_content:
            return ""

        text = main_content.get_text(separator='\n', strip=True)
        # Basic cleanup
        text = re.sub(r'\n+', '\n\n', text)
        return text

if __name__ == "__main__":
    processor = HTMLProcessor()
    # Test would go here
