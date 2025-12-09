"""
Semantic Agent

Specialized agent for high-level reasoning about web pages.
Uses LLM capabilities to determine user-centric intent and classify elements.
"""

from typing import Dict, Any, List, Optional
import json

from schemas import (
    PageContextOntology,
    PageType,
    ComponentClassification,
    ElementRole,
)


class SemanticAgent:
    """
    Semantic Agent - LLM-powered reasoning engine.
    
    Responsibilities:
    - Determine user-centric intent of the application
    - Classify element roles using LLM capabilities
    - Identify reusable UI components
    - Ground understanding in web accessibility standards (ARIA)
    - Provide confidence scores for classifications
    
    Note: This is a placeholder implementation. In production, this would
    integrate with an LLM API (e.g., Gemini, GPT-4) for actual reasoning.
    """
    
    def __init__(self, llm_model: Optional[str] = None):
        """
        Initialize Semantic Agent.
        
        Args:
            llm_model: Optional LLM model identifier
        """
        self.llm_model = llm_model or "gemini-pro"  # Placeholder
    
    async def classify_page(
        self,
        url: str,
        metadata: Dict[str, Any],
        dom_analysis: Dict[str, Any],
        elements_count: int
    ) -> PageContextOntology:
        """
        Classify the page type and determine its primary purpose.
        
        Args:
            url: Target URL
            metadata: Page metadata (title, description, etc.)
            dom_analysis: Structural analysis from DOM Analyzer
            elements_count: Number of interactive elements
        
        Returns:
            PageContextOntology with classification
        """
        # TODO: Replace with actual LLM call
        # For now, use heuristic-based classification
        
        page_type = self._heuristic_page_classification(
            url, metadata, dom_analysis
        )
        
        primary_purpose = self._infer_primary_purpose(
            page_type, metadata, dom_analysis
        )
        
        secondary_purposes = self._infer_secondary_purposes(
            dom_analysis
        )
        
        components = self._identify_components(dom_analysis)
        
        requires_auth = self._detect_authentication_requirement(
            url, metadata, dom_analysis
        )
        
        dynamic_content = self._detect_dynamic_content(dom_analysis)
        
        # Confidence based on available signals
        confidence = self._calculate_confidence(
            metadata, dom_analysis, page_type
        )
        
        # Filter navigation paths to ensure all text values are strings
        nav_links = dom_analysis.get("navigation", {}).get("links", [])[:10]
        filtered_nav_links = [
            {**link, "text": link.get("text") or ""}
            for link in nav_links
        ]
        
        return PageContextOntology(
            url=url,
            page_type=page_type,
            primary_purpose=primary_purpose,
            secondary_purposes=secondary_purposes,
            identified_components=components,
            navigation_paths=filtered_nav_links,
            requires_authentication=requires_auth,
            dynamic_content=dynamic_content,
            confidence_score=confidence,
        )
    
    def _heuristic_page_classification(
        self,
        url: str,
        metadata: Dict[str, Any],
        dom_analysis: Dict[str, Any]
    ) -> PageType:
        """Classify page type using heuristics"""
        url_lower = url.lower()
        title = (metadata.get("title") or "").lower()
        description = (metadata.get("description") or "").lower()
        
        # Check for e-commerce patterns
        if any(keyword in url_lower or keyword in title for keyword in [
            "product", "shop", "store", "buy", "cart", "checkout"
        ]):
            if "cart" in url_lower or "checkout" in url_lower:
                return PageType.ECOMMERCE_CART
            elif "checkout" in url_lower:
                return PageType.ECOMMERCE_CHECKOUT
            else:
                return PageType.ECOMMERCE_PRODUCT
        
        # Check for authentication patterns
        if any(keyword in url_lower or keyword in title for keyword in [
            "login", "signin", "sign-in"
        ]):
            return PageType.AUTH_LOGIN
        
        if any(keyword in url_lower or keyword in title for keyword in [
            "signup", "register", "sign-up"
        ]):
            return PageType.AUTH_SIGNUP
        
        if any(keyword in url_lower or keyword in title for keyword in [
            "forgot", "reset", "password"
        ]):
            return PageType.AUTH_FORGOT_PASSWORD
        
        # Check for SaaS patterns
        if any(keyword in url_lower or keyword in title for keyword in [
            "dashboard", "admin", "console"
        ]):
            if "admin" in url_lower:
                return PageType.ADMIN_PANEL
            else:
                return PageType.SAAS_DASHBOARD
        
        if any(keyword in url_lower or keyword in title for keyword in [
            "settings", "preferences", "account"
        ]):
            return PageType.SAAS_SETTINGS
        
        # Check for content patterns
        if any(keyword in url_lower or keyword in title for keyword in [
            "article", "blog", "post"
        ]):
            return PageType.CONTENT_ARTICLE
        
        if any(keyword in url_lower or keyword in title for keyword in [
            "search", "results"
        ]):
            return PageType.SEARCH_RESULTS
        
        if any(keyword in url_lower or keyword in title for keyword in [
            "profile", "user"
        ]):
            return PageType.USER_PROFILE
        
        # Check for landing page indicators
        forms = dom_analysis.get("forms", [])
        if len(forms) == 1 and dom_analysis.get("metrics", {}).get("headings", 0) > 2:
            return PageType.CONTENT_LANDING
        
        return PageType.UNKNOWN
    
    def _infer_primary_purpose(
        self,
        page_type: PageType,
        metadata: Dict[str, Any],
        dom_analysis: Dict[str, Any]
    ) -> str:
        """Infer the primary user goal on this page"""
        purpose_map = {
            PageType.ECOMMERCE_PRODUCT: "View product details and add to cart",
            PageType.ECOMMERCE_CART: "Review cart items and proceed to checkout",
            PageType.ECOMMERCE_CHECKOUT: "Complete purchase transaction",
            PageType.AUTH_LOGIN: "Authenticate user credentials",
            PageType.AUTH_SIGNUP: "Create new user account",
            PageType.AUTH_FORGOT_PASSWORD: "Reset forgotten password",
            PageType.SAAS_DASHBOARD: "View key metrics and navigate application",
            PageType.SAAS_SETTINGS: "Configure application preferences",
            PageType.ADMIN_PANEL: "Manage system configuration and users",
            PageType.CONTENT_ARTICLE: "Read article content",
            PageType.CONTENT_LANDING: "Learn about product/service and convert",
            PageType.SEARCH_RESULTS: "Browse search results and navigate to content",
            PageType.USER_PROFILE: "View and edit user profile information",
        }
        
        return purpose_map.get(
            page_type,
            metadata.get("description") or "Analyze and interact with web page content"
        )
    
    def _infer_secondary_purposes(
        self,
        dom_analysis: Dict[str, Any]
    ) -> List[str]:
        """Infer secondary user goals"""
        purposes = []
        
        patterns = dom_analysis.get("structural_patterns", {})
        
        if patterns.get("has_navigation"):
            purposes.append("Navigate to other sections")
        
        if dom_analysis.get("forms"):
            purposes.append("Submit form data")
        
        if patterns.get("has_modal"):
            purposes.append("Interact with modal dialogs")
        
        if patterns.get("has_dropdown"):
            purposes.append("Select from dropdown menus")
        
        return purposes
    
    def _identify_components(
        self,
        dom_analysis: Dict[str, Any]
    ) -> List[ComponentClassification]:
        """Identify reusable UI components"""
        components = []
        patterns = dom_analysis.get("structural_patterns", {})
        hierarchy = dom_analysis.get("hierarchy", {})
        
        # Navigation component
        if patterns.get("has_navigation") or hierarchy.get("navs", 0) > 0:
            components.append(ComponentClassification(
                component_type="Navigation",
                elements=[],  # Would be populated with actual element IDs
                is_reusable=True,
                page_location="header"
            ))
        
        # Header component
        if patterns.get("has_header") or hierarchy.get("headers", 0) > 0:
            components.append(ComponentClassification(
                component_type="Header",
                elements=[],
                is_reusable=True,
                page_location="top"
            ))
        
        # Footer component
        if patterns.get("has_footer") or hierarchy.get("footers", 0) > 0:
            components.append(ComponentClassification(
                component_type="Footer",
                elements=[],
                is_reusable=True,
                page_location="bottom"
            ))
        
        # Modal component
        if patterns.get("has_modal"):
            components.append(ComponentClassification(
                component_type="Modal",
                elements=[],
                is_reusable=True,
                page_location="overlay"
            ))
        
        # Form components
        forms = dom_analysis.get("forms", [])
        for i, form in enumerate(forms):
            components.append(ComponentClassification(
                component_type=f"Form_{i+1}",
                elements=[],
                is_reusable=False,
                page_location="main"
            ))
        
        return components
    
    def _detect_authentication_requirement(
        self,
        url: str,
        metadata: Dict[str, Any],
        dom_analysis: Dict[str, Any]
    ) -> bool:
        """Detect if page requires authentication"""
        # Check URL patterns
        if any(keyword in url.lower() for keyword in [
            "login", "signin", "auth", "account"
        ]):
            return True
        
        # Check for login forms
        forms = dom_analysis.get("forms", [])
        for form in forms:
            input_types = form.get("input_types", {})
            if "password" in input_types:
                return True
        
        return False
    
    def _detect_dynamic_content(
        self,
        dom_analysis: Dict[str, Any]
    ) -> bool:
        """Detect if page has significant dynamic/AJAX content"""
        patterns = dom_analysis.get("structural_patterns", {})
        
        # Indicators of dynamic content
        dynamic_indicators = [
            patterns.get("has_carousel"),
            patterns.get("has_tabs"),
            patterns.get("has_accordion"),
            patterns.get("has_modal"),
        ]
        
        return sum(dynamic_indicators) >= 2
    
    def _calculate_confidence(
        self,
        metadata: Dict[str, Any],
        dom_analysis: Dict[str, Any],
        page_type: PageType
    ) -> float:
        """Calculate confidence score for classification"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have good metadata
        if metadata.get("title"):
            confidence += 0.1
        if metadata.get("description"):
            confidence += 0.1
        
        # Increase confidence if page type is not unknown
        if page_type != PageType.UNKNOWN:
            confidence += 0.2
        
        # Increase confidence if we have structural patterns
        patterns = dom_analysis.get("structural_patterns", {})
        pattern_count = sum(1 for v in patterns.values() if v)
        confidence += min(0.1, pattern_count * 0.02)
        
        return min(1.0, confidence)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        agent = SemanticAgent()
        
        # Example metadata and DOM analysis
        metadata = {
            "title": "Login - Example App",
            "description": "Sign in to your account",
        }
        
        dom_analysis = {
            "metrics": {"forms": 1, "headings": 2},
            "hierarchy": {"navs": 1, "headers": 1},
            "navigation": {"links": []},
            "forms": [
                {
                    "action": "/login",
                    "method": "POST",
                    "input_types": {"text": 1, "password": 1}
                }
            ],
            "structural_patterns": {
                "has_navigation": True,
                "has_header": True,
                "has_footer": True,
                "has_modal": False,
            },
        }
        
        result = await agent.classify_page(
            url="https://example.com/login",
            metadata=metadata,
            dom_analysis=dom_analysis,
            elements_count=10
        )
        
        print(f"Page Type: {result.page_type.value}")
        print(f"Primary Purpose: {result.primary_purpose}")
        print(f"Requires Auth: {result.requires_authentication}")
        print(f"Confidence: {result.confidence_score:.2%}")
        print(f"Components: {len(result.identified_components)}")
    
    asyncio.run(main())
