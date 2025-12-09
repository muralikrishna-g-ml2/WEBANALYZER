"""
Observer Agent

Specialized agent for browser automation and data capture.
Uses Browser MCP to navigate, capture DOM, and discover elements.
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from mcp.browser_server import BrowserMCPServer
from schemas import ElementClassificationMap, ElementLocator, ElementRole, LocatorStrategy


class ObserverAgent:
    """
    Observer Agent - Browser automation specialist.
    
    Responsibilities:
    - Navigate to target URL via Browser MCP
    - Handle dynamic content loading
    - Capture stabilized DOM snapshots
    - Discover interactive elements
    - Take visual screenshots for documentation
    - Extract raw element data for downstream agents
    """
    
    def __init__(self, browser_mcp: BrowserMCPServer):
        """
        Initialize Observer Agent.
        
        Args:
            browser_mcp: Browser MCP server instance
        """
        self.browser_mcp = browser_mcp
    
    async def observe(
        self,
        url: str,
        screenshot_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Observe a web page and collect all raw data.
        
        Args:
            url: Target URL to observe
            screenshot_path: Optional path to save screenshot
        
        Returns:
            Dict with navigation, DOM, elements, metadata, and screenshot
        """
        result = {
            "status": "success",
            "url": url,
            "navigation": None,
            "dom": None,
            "elements": None,
            "metadata": None,
            "screenshot": None,
        }
        
        try:
            # Step 1: Navigate to URL
            nav_result = await self.browser_mcp.navigate(url, wait_until="networkidle")
            result["navigation"] = nav_result
            
            if nav_result["status"] != "success":
                result["status"] = "error"
                result["error"] = f"Navigation failed: {nav_result.get('error')}"
                return result
            
            # Step 2: Capture DOM
            dom_result = await self.browser_mcp.capture_dom()
            result["dom"] = dom_result
            
            # Step 3: Discover interactive elements
            elements_result = await self.browser_mcp.discover_elements(interactive_only=True)
            result["elements"] = elements_result
            
            # Step 4: Get page metadata
            metadata_result = await self.browser_mcp.get_page_metadata()
            result["metadata"] = metadata_result
            
            # Step 5: Capture screenshot
            screenshot_result = await self.browser_mcp.capture_screenshot(
                path=screenshot_path,
                full_page=True
            )
            result["screenshot"] = screenshot_result
            
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
            return result
    
    def create_element_classification_map(
        self,
        observation: Dict[str, Any]
    ) -> ElementClassificationMap:
        """
        Create an ElementClassificationMap from observation data.
        
        Args:
            observation: Result from observe() method
        
        Returns:
            ElementClassificationMap with discovered elements
        """
        from datetime import datetime
        
        url = observation["url"]
        elements_data = observation.get("elements", {})
        
        if elements_data.get("status") != "success":
            # Return empty map if element discovery failed
            return ElementClassificationMap(
                url=url,
                total_elements=0,
                elements=[],
                timestamp=datetime.now().isoformat()
            )
        
        # Convert raw element data to ElementLocator objects
        element_locators = []
        
        for elem_data in elements_data.get("elements", []):
            # Determine semantic role
            role = self._determine_role(elem_data)
            
            # Generate initial locator strategy
            strategy, value = self._generate_initial_locator(elem_data)
            
            # Create ElementLocator (will be scored by Element Classifier later)
            element_locators.append(
                ElementLocator(
                    element_id=f"elem_{elem_data['index']}",
                    semantic_role=role,
                    locator_strategy=strategy,
                    locator_value=value,
                    lqs_score=0,  # Will be calculated by Element Classifier
                    lqs_category="FAIL",  # Placeholder
                    stability_rationale="Pending LQS analysis",
                    user_facing_label=self._extract_label(elem_data),
                    is_interactive=True,
                )
            )
        
        return ElementClassificationMap(
            url=url,
            total_elements=len(element_locators),
            elements=element_locators,
            timestamp=datetime.now().isoformat()
        )
    
    def _determine_role(self, elem_data: Dict[str, Any]) -> ElementRole:
        """Determine semantic role from element data"""
        # Check explicit role attribute
        if elem_data.get("role"):
            role_map = {
                "button": ElementRole.BUTTON,
                "link": ElementRole.LINK,
                "textbox": ElementRole.TEXTBOX,
                "combobox": ElementRole.COMBOBOX,
                "checkbox": ElementRole.CHECKBOX,
                "radio": ElementRole.RADIO,
                "heading": ElementRole.HEADING,
                "img": ElementRole.IMAGE,
                "list": ElementRole.LIST,
                "listitem": ElementRole.LISTITEM,
                "navigation": ElementRole.NAVIGATION,
                "main": ElementRole.MAIN,
                "form": ElementRole.FORM,
                "dialog": ElementRole.DIALOG,
                "alert": ElementRole.ALERT,
            }
            if elem_data["role"] in role_map:
                return role_map[elem_data["role"]]
        
        # Infer from tag and type
        tag = elem_data.get("tag", "").lower()
        elem_type = elem_data.get("type", "").lower()
        
        if tag == "button" or (tag == "input" and elem_type == "button"):
            return ElementRole.BUTTON
        elif tag == "a":
            return ElementRole.LINK
        elif tag == "input":
            if elem_type in ["text", "email", "password", "search", "tel", "url"]:
                return ElementRole.TEXTBOX
            elif elem_type == "checkbox":
                return ElementRole.CHECKBOX
            elif elem_type == "radio":
                return ElementRole.RADIO
        elif tag == "select":
            return ElementRole.COMBOBOX
        elif tag == "textarea":
            return ElementRole.TEXTBOX
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return ElementRole.HEADING
        elif tag == "img":
            return ElementRole.IMAGE
        elif tag == "form":
            return ElementRole.FORM
        
        return ElementRole.UNKNOWN
    
    def _generate_initial_locator(
        self,
        elem_data: Dict[str, Any]
    ) -> tuple[LocatorStrategy, str]:
        """
        Generate initial locator strategy and value.
        
        Priority:
        1. data-testid (if available)
        2. aria-label (if available)
        3. id (if stable)
        4. CSS class (if simple)
        5. Tag + text (fallback)
        """
        # Check for test ID
        if elem_data.get("testId"):
            return LocatorStrategy.GET_BY_TEST_ID, elem_data["testId"]
        
        # Check for aria-label
        if elem_data.get("ariaLabel"):
            return LocatorStrategy.GET_BY_LABEL, elem_data["ariaLabel"]
        
        # Check for stable ID
        elem_id = elem_data.get("id")
        if elem_id and not any(x in elem_id.lower() for x in ["random", "generated", "uuid"]):
            return LocatorStrategy.CSS_SELECTOR, f"#{elem_id}"
        
        # Check for simple class
        classes = elem_data.get("classes", [])
        if len(classes) == 1:
            return LocatorStrategy.CSS_SELECTOR, f".{classes[0]}"
        
        # Fallback: tag + text
        tag = elem_data.get("tag", "div")
        text = elem_data.get("text", "")
        if text and len(text) < 50:
            return LocatorStrategy.GET_BY_TEXT, text
        
        # Last resort: CSS with tag
        return LocatorStrategy.CSS_SELECTOR, tag
    
    def _extract_label(self, elem_data: Dict[str, Any]) -> Optional[str]:
        """Extract user-facing label from element data"""
        # Priority: aria-label > text > placeholder > name
        if elem_data.get("ariaLabel"):
            return elem_data["ariaLabel"]
        
        text = elem_data.get("text", "")
        if text and len(text) < 100:
            return text.strip()
        
        if elem_data.get("placeholder"):
            return elem_data["placeholder"]
        
        if elem_data.get("name"):
            return elem_data["name"]
        
        return None


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize Browser MCP
        browser_mcp = BrowserMCPServer(headless=True)
        await browser_mcp.initialize()
        
        try:
            # Create Observer Agent
            observer = ObserverAgent(browser_mcp)
            
            # Observe a URL
            print("Observing https://example.com...")
            observation = await observer.observe(
                url="https://example.com",
                screenshot_path=Path("./output/example-screenshot.png")
            )
            
            print(f"Status: {observation['status']}")
            print(f"Elements discovered: {observation['elements'].get('count', 0)}")
            
            # Create Element Classification Map
            element_map = observer.create_element_classification_map(observation)
            print(f"Element map created with {element_map.total_elements} elements")
            
            # Show first few elements
            for elem in element_map.elements[:5]:
                print(f"  - {elem.semantic_role.value}: {elem.user_facing_label or 'N/A'}")
                print(f"    Locator: {elem.locator_strategy.value}('{elem.locator_value}')")
        
        finally:
            await browser_mcp.cleanup()
    
    asyncio.run(main())
