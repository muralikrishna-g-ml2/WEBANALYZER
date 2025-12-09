"""
Browser MCP Server

Provides deterministic web automation capabilities to agents via MCP.
Handles navigation, DOM capture, screenshots, and element discovery.
"""

import asyncio
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
except ImportError:
    print("Warning: Playwright not installed. Install with: pip install playwright && npx playwright install")
    Browser = None
    Page = None
    BrowserContext = None


class BrowserMCPServer:
    """
    MCP Server for browser automation.
    
    Provides tools for:
    - Navigation to URLs
    - DOM capture and analysis
    - Screenshot capture
    - Element discovery and interaction
    - Dynamic content synchronization
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Browser MCP Server.
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout for operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Playwright and browser instance"""
        if self._initialized:
            return
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        self._initialized = True
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL and wait for page load.
        
        Args:
            url: Target URL to navigate to
            wait_until: When to consider navigation complete
                       ('load', 'domcontentloaded', 'networkidle')
        
        Returns:
            Dict with status, final_url, and title
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self.page.goto(url, wait_until=wait_until)
            
            # Wait for any dynamic content
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            return {
                "status": "success",
                "final_url": self.page.url,
                "title": await self.page.title(),
                "response_status": response.status if response else None,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    async def capture_dom(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Capture the DOM structure.
        
        Args:
            selector: Optional CSS selector to capture specific element
                     If None, captures entire page HTML
        
        Returns:
            Dict with html content and metadata
        """
        if not self._initialized or not self.page:
            return {"status": "error", "error": "Browser not initialized"}
        
        try:
            if selector:
                element = await self.page.query_selector(selector)
                if not element:
                    return {"status": "error", "error": f"Element not found: {selector}"}
                html = await element.inner_html()
            else:
                html = await self.page.content()
            
            return {
                "status": "success",
                "html": html,
                "url": self.page.url,
                "size_bytes": len(html.encode('utf-8')),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    async def capture_screenshot(
        self, 
        path: Optional[Path] = None,
        full_page: bool = True
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of the page.
        
        Args:
            path: Optional path to save screenshot
            full_page: Capture full scrollable page
        
        Returns:
            Dict with screenshot data (base64 if no path) or file path
        """
        if not self._initialized or not self.page:
            return {"status": "error", "error": "Browser not initialized"}
        
        try:
            screenshot_bytes = await self.page.screenshot(
                full_page=full_page,
                type='png'
            )
            
            if path:
                path = Path(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(screenshot_bytes)
                
                return {
                    "status": "success",
                    "path": str(path),
                    "size_bytes": len(screenshot_bytes),
                }
            else:
                return {
                    "status": "success",
                    "data": base64.b64encode(screenshot_bytes).decode('utf-8'),
                    "size_bytes": len(screenshot_bytes),
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    async def discover_elements(
        self,
        interactive_only: bool = True
    ) -> Dict[str, Any]:
        """
        Discover elements on the page.
        
        Args:
            interactive_only: Only return interactive elements
        
        Returns:
            Dict with list of discovered elements and their properties
        """
        if not self._initialized or not self.page:
            return {"status": "error", "error": "Browser not initialized"}
        
        try:
            # JavaScript to extract element information
            js_code = """
            () => {
                const interactiveSelectors = [
                    'button', 'a', 'input', 'select', 'textarea',
                    '[role="button"]', '[role="link"]', '[role="textbox"]',
                    '[role="combobox"]', '[role="checkbox"]', '[role="radio"]',
                    '[onclick]', '[tabindex]'
                ];
                
                const selector = arguments[0] ? interactiveSelectors.join(',') : '*';
                const elements = document.querySelectorAll(selector);
                
                return Array.from(elements).map((el, index) => {
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    return {
                        index: index,
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: Array.from(el.classList),
                        role: el.getAttribute('role') || null,
                        ariaLabel: el.getAttribute('aria-label') || null,
                        text: el.textContent?.trim().substring(0, 100) || null,
                        placeholder: el.placeholder || null,
                        name: el.name || null,
                        type: el.type || null,
                        href: el.href || null,
                        visible: rect.width > 0 && rect.height > 0 && styles.visibility !== 'hidden',
                        position: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        },
                        testId: el.getAttribute('data-testid') || el.getAttribute('data-test-id') || null,
                    };
                }).filter(el => !arguments[0] || el.visible);
            }
            """
            
            elements = await self.page.evaluate(js_code, interactive_only)
            
            return {
                "status": "success",
                "count": len(elements),
                "elements": elements,
                "url": self.page.url,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    async def wait_for_selector(
        self,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Dict[str, Any]:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds (uses default if None)
            state: Element state to wait for ('attached', 'visible', 'hidden')
        
        Returns:
            Dict with status and element info
        """
        if not self._initialized or not self.page:
            return {"status": "error", "error": "Browser not initialized"}
        
        try:
            element = await self.page.wait_for_selector(
                selector,
                timeout=timeout or self.timeout,
                state=state
            )
            
            if element:
                return {
                    "status": "success",
                    "found": True,
                    "selector": selector,
                }
            else:
                return {
                    "status": "success",
                    "found": False,
                    "selector": selector,
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "selector": selector,
            }
    
    async def get_page_metadata(self) -> Dict[str, Any]:
        """
        Get comprehensive page metadata.
        
        Returns:
            Dict with title, URL, meta tags, and other metadata
        """
        if not self._initialized or not self.page:
            return {"status": "error", "error": "Browser not initialized"}
        
        try:
            metadata = await self.page.evaluate("""
            () => {
                const metas = {};
                document.querySelectorAll('meta').forEach(meta => {
                    const name = meta.name || meta.property;
                    if (name) {
                        metas[name] = meta.content;
                    }
                });
                
                return {
                    title: document.title,
                    description: metas['description'] || null,
                    keywords: metas['keywords'] || null,
                    ogTitle: metas['og:title'] || null,
                    ogDescription: metas['og:description'] || null,
                    ogType: metas['og:type'] || null,
                    viewport: metas['viewport'] || null,
                    allMetas: metas,
                    lang: document.documentElement.lang || null,
                    links: Array.from(document.querySelectorAll('a[href]')).length,
                    forms: Array.from(document.querySelectorAll('form')).length,
                    images: Array.from(document.querySelectorAll('img')).length,
                };
            }
            """)
            
            return {
                "status": "success",
                "url": self.page.url,
                **metadata
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }


# Convenience function for one-off operations
async def analyze_url(url: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze a URL in one call.
    
    Args:
        url: URL to analyze
        output_dir: Optional directory to save screenshot
    
    Returns:
        Dict with navigation, DOM, elements, metadata, and screenshot
    """
    server = BrowserMCPServer()
    
    try:
        await server.initialize()
        
        # Navigate
        nav_result = await server.navigate(url)
        if nav_result["status"] != "success":
            return nav_result
        
        # Capture DOM
        dom_result = await server.capture_dom()
        
        # Discover elements
        elements_result = await server.discover_elements()
        
        # Get metadata
        metadata_result = await server.get_page_metadata()
        
        # Screenshot
        screenshot_path = None
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = output_dir / "screenshot.png"
        
        screenshot_result = await server.capture_screenshot(screenshot_path)
        
        return {
            "status": "success",
            "url": url,
            "navigation": nav_result,
            "dom": dom_result,
            "elements": elements_result,
            "metadata": metadata_result,
            "screenshot": screenshot_result,
        }
    finally:
        await server.cleanup()


# Example usage
if __name__ == "__main__":
    async def main():
        # Example: Analyze a URL
        result = await analyze_url(
            "https://example.com",
            output_dir=Path("./output/example-com")
        )
        
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
