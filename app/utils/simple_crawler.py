"""
Simple fallback crawler using requests and BeautifulSoup when crawl4ai is not available.
"""

import requests
from bs4 import BeautifulSoup
import html2text
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse


class SimpleCrawler:
    """Simple fallback crawler using requests and BeautifulSoup."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.html_to_text = html2text.HTML2Text()
        self.html_to_text.ignore_links = False
        self.html_to_text.ignore_images = True
    
    def crawl_url(self, url: str) -> Dict[str, Any]:
        """Crawl a single URL and return markdown content."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert to markdown
            markdown = self.html_to_text.handle(str(soup))
            
            # Extract internal links
            internal_links = []
            base_domain = urlparse(url).netloc
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                link_domain = urlparse(full_url).netloc
                
                if link_domain == base_domain:
                    internal_links.append({
                        "href": full_url,
                        "text": link.get_text(strip=True)
                    })
            
            return {
                'url': url,
                'markdown': markdown,
                'success': True,
                'links': {'internal': internal_links}
            }
            
        except Exception as e:
            return {
                'url': url,
                'markdown': '',
                'success': False,
                'error_message': str(e),
                'links': {'internal': []}
            }


async def simple_crawl_recursive_internal_links(start_urls, max_depth=3, max_concurrent=10) -> List[Dict[str,Any]]:
    """Simple recursive crawl using requests."""
    crawler = SimpleCrawler()
    visited = set()
    results_all = []
    
    def normalize_url(url):
        return url.split('#')[0]  # Remove fragment
    
    current_urls = set([normalize_url(u) for u in start_urls])
    
    for depth in range(max_depth):
        urls_to_crawl = [url for url in current_urls if normalize_url(url) not in visited]
        if not urls_to_crawl:
            break
        
        next_level_urls = set()
        
        for url in urls_to_crawl:
            norm_url = normalize_url(url)
            visited.add(norm_url)
            
            result = crawler.crawl_url(url)
            
            if result['success'] and result['markdown']:
                results_all.append({'url': result['url'], 'markdown': result['markdown']})
                
                for link in result['links']['internal']:
                    next_url = normalize_url(link["href"])
                    if next_url not in visited:
                        next_level_urls.add(next_url)
        
        current_urls = next_level_urls
    
    return results_all


async def simple_crawl_markdown_file(url: str) -> List[Dict[str,Any]]:
    """Simple crawl for markdown/text files."""
    crawler = SimpleCrawler()
    result = crawler.crawl_url(url)
    
    if result['success'] and result['markdown']:
        return [{'url': url, 'markdown': result['markdown']}]
    else:
        raise Exception(f"Failed to crawl {url}: {result.get('error_message', 'Unknown error')}")


async def simple_crawl_batch(urls: List[str], max_concurrent: int = 10) -> List[Dict[str,Any]]:
    """Simple batch crawl."""
    crawler = SimpleCrawler()
    results = []
    
    for url in urls:
        result = crawler.crawl_url(url)
        if result['success'] and result['markdown']:
            results.append({'url': result['url'], 'markdown': result['markdown']})
    
    return results
