"""
Link Preview API module for FastAPI application.
Extracts OpenGraph metadata from a given URL using Playwright.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from urllib.parse import urlparse
import asyncio

from playwright.async_api import async_playwright

router = APIRouter(prefix="/link-preview", tags=["Link Preview"])

class LinkPreviewRequest(BaseModel):
    url: str = Field(..., description="URL to preview")

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

class LinkPreviewResponse(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    url: str
    siteName: Optional[str] = None

async def extract_opengraph_metadata(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=15000)
            og_tags = await page.evaluate('''() => {
                const og = {};
                for (const meta of document.getElementsByTagName('meta')) {
                    if (meta.getAttribute('property') && meta.getAttribute('property').startsWith('og:')) {
                        og[meta.getAttribute('property')] = meta.getAttribute('content');
                    }
                }
                og['title'] = document.title;
                const desc = document.querySelector('meta[name="description"]');
                if (desc) og['description'] = desc.getAttribute('content');
                return og;
            }''')
        finally:
            await browser.close()
    return og_tags

@router.post("/", response_model=LinkPreviewResponse)
async def link_preview(request: LinkPreviewRequest):
    try:
        og = await extract_opengraph_metadata(request.url)
        return LinkPreviewResponse(
            title=og.get('og:title') or og.get('title'),
            description=og.get('og:description') or og.get('description'),
            image=og.get('og:image'),
            url=request.url,
            siteName=og.get('og:site_name')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preview: {str(e)}")
