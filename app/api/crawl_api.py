"""
Crawl API module for FastAPI application.
Provides web crawling functionality with ChromaDB integration.
"""

import traceback
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urldefrag
from xml.etree import ElementTree

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
import requests

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, MemoryAdaptiveDispatcher
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

from app.utils.crawl_utils import (
    smart_chunk_markdown,
    extract_section_info
)


if not CRAWL4AI_AVAILABLE:
    from app.utils.simple_crawler import (
        simple_crawl_recursive_internal_links,
        simple_crawl_markdown_file,
        simple_crawl_batch
    )

router = APIRouter(prefix="/crawl", tags=["Web Crawling"])


# Pydantic models for request/response
class CrawlRequest(BaseModel):
    url: str = Field(..., description="URL to crawl (regular, .txt, or sitemap)")
    chunk_size: int = Field(default=1000, description="Max chunk size (chars)")
    max_depth: int = Field(default=3, description="Recursion depth for regular URLs")
    max_concurrent: int = Field(default=10, description="Max parallel browser sessions")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError('Invalid URL format')
            return v
        except Exception:
            raise ValueError('Invalid URL format')


class CrawlResponse(BaseModel):
    success: bool
    message: str
    total_chunks: int
    urls_crawled: List[str]
    chunks: Optional[List[Dict[str, Any]]] = None
    markdown_content: Optional[List[Dict[str, str]]] = None





# Utility functions
def is_sitemap(url: str) -> bool:
    return url.endswith('sitemap.xml') or 'sitemap' in urlparse(url).path


def is_txt(url: str) -> bool:
    return url.endswith('.txt')


async def crawl_recursive_internal_links(start_urls, max_depth=3, max_concurrent=10) -> List[Dict[str,Any]]:
    """Recursive crawl using internal links discovery."""
    if not CRAWL4AI_AVAILABLE:
        # Use simple fallback crawler
        return await simple_crawl_recursive_internal_links(start_urls, max_depth, max_concurrent)
        
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    visited = set()

    def normalize_url(url):
        return urldefrag(url)[0]

    current_urls = set([normalize_url(u) for u in start_urls])
    results_all = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for depth in range(max_depth):
            urls_to_crawl = [normalize_url(url) for url in current_urls if normalize_url(url) not in visited]
            if not urls_to_crawl:
                break

            results = await crawler.arun_many(urls=urls_to_crawl, config=run_config, dispatcher=dispatcher)
            next_level_urls = set()

            for result in results:
                norm_url = normalize_url(result.url)
                visited.add(norm_url)

                if result.success and result.markdown:
                    results_all.append({'url': result.url, 'markdown': result.markdown})
                    for link in result.links.get("internal", []):
                        next_url = normalize_url(link["href"])
                        if next_url not in visited:
                            next_level_urls.add(next_url)

            current_urls = next_level_urls

    return results_all


async def crawl_markdown_file(url: str) -> List[Dict[str,Any]]:
    """Crawl a .txt or markdown file."""
    if not CRAWL4AI_AVAILABLE:
        # Use simple fallback crawler
        return await simple_crawl_markdown_file(url)
        
    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)
        if result.success and result.markdown:
            return [{'url': url, 'markdown': result.markdown}]
        else:
            raise Exception(f"Failed to crawl {url}: {result.error_message}")


def parse_sitemap(sitemap_url: str) -> List[str]:
    resp = requests.get(sitemap_url)
    urls = []

    if resp.status_code == 200:
        try:
            tree = ElementTree.fromstring(resp.content)
            urls = [loc.text for loc in tree.findall('.//{*}loc')]
        except Exception as e:
            raise Exception(f"Error parsing sitemap XML: {e}")
    else:
        raise Exception(f"Failed to fetch sitemap: HTTP {resp.status_code}")

    return urls


async def crawl_batch(urls: List[str], max_concurrent: int = 10) -> List[Dict[str,Any]]:
    """Batch crawl multiple URLs in parallel."""
    if not CRAWL4AI_AVAILABLE:
        # Use simple fallback crawler
        return await simple_crawl_batch(urls, max_concurrent)
        
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=crawl_config, dispatcher=dispatcher)
        return [{'url': r.url, 'markdown': r.markdown} for r in results if r.success and r.markdown]


# API endpoints



@router.post("/", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website and optionally insert into ChromaDB.
    
    Supports:
    - Regular URLs (with recursive crawling)
    - Sitemap.xml files  
    - Text/markdown files
    """
    try:
        # Detect URL type and crawl accordingly
        url = request.url
        if is_txt(url):
            print(f"Detected .txt/markdown file: {url}")
            crawl_results = await crawl_markdown_file(url)
        elif is_sitemap(url):
            print(f"Detected sitemap: {url}")
            sitemap_urls = parse_sitemap(url)
            if not sitemap_urls:
                raise Exception("No URLs found in sitemap.")
            crawl_results = await crawl_batch(sitemap_urls, max_concurrent=request.max_concurrent)
        else:
            print(f"Detected regular URL: {url}")
            crawl_results = await crawl_recursive_internal_links(
                [url], 
                max_depth=request.max_depth, 
                max_concurrent=request.max_concurrent
            )

        if not crawl_results:
            raise Exception("No content could be crawled from the provided URL.")

        # Process and chunk the results
        chunk_idx = 0
        urls_crawled = []
        chunks_data = []
        markdown_data = []

        for doc in crawl_results:
            doc_url = doc['url']
            urls_crawled.append(doc_url)
            md = doc['markdown']
            chunks = smart_chunk_markdown(md, max_len=request.chunk_size)
            for chunk in chunks:
                meta = extract_section_info(chunk)
                meta["chunk_index"] = chunk_idx
                meta["source"] = doc_url
                chunks_data.append({
                    "id": f"chunk-{chunk_idx}",
                    "content": chunk,
                    "metadata": meta
                })
                chunk_idx += 1
            markdown_data.append({
                "url": doc['url'],
                "markdown": doc['markdown']
            })

        response = CrawlResponse(
            success=True,
            message=f"Successfully crawled {len(urls_crawled)} URLs and created {chunk_idx} chunks",
            total_chunks=chunk_idx,
            urls_crawled=urls_crawled,
            chunks=chunks_data,
            markdown_content=markdown_data
        )

        return response

    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Crawling failed: {str(e)}")


@router.get("/health")
async def crawl_health_check():
    """Health check endpoint for crawl service."""
    crawler_info = {
        "crawl4ai_available": CRAWL4AI_AVAILABLE,
        "crawler_type": "crawl4ai" if CRAWL4AI_AVAILABLE else "simple_fallback"
    }
    return {
        "status": "healthy", 
        "message": "Crawl service is running",
        "crawler_info": crawler_info
    }
