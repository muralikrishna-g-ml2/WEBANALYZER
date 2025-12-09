"""
LLM Service Wrapper

Provides LLM integration for semantic analysis and classification.
Supports Gemini API with fallback to heuristics.
"""

import os
from typing import Dict, Any, Optional, List
import json


class LLMService:
    """
    LLM Service for semantic analysis.
    
    Provides integration with Gemini API for:
    - Page type classification
    - Element role identification
    - Component detection
    - Semantic understanding
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        """
        Initialize LLM Service.
        
        Args:
            api_key: Gemini API key (or from GEMINI_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(model)
            except ImportError:
                print("Warning: google-generativeai not installed. LLM features disabled.")
                self.enabled = False
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini: {e}. LLM features disabled.")
                self.enabled = False
    
    async def classify_page_type(
        self,
        url: str,
        title: str,
        description: str,
        html_snippet: str,
        dom_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify page type using LLM.
        
        Args:
            url: Page URL
            title: Page title
            description: Meta description
            html_snippet: First 1000 chars of HTML
            dom_metrics: DOM analysis metrics
        
        Returns:
            Dict with page_type, confidence, and reasoning
        """
        if not self.enabled:
            return {
                "page_type": "UNKNOWN",
                "confidence": 0.0,
                "reasoning": "LLM not available - using heuristics",
                "llm_used": False
            }
        
        prompt = f"""Analyze this web page and classify its type.

URL: {url}
Title: {title}
Description: {description}

DOM Metrics:
- Total Elements: {dom_metrics.get('total_elements', 0)}
- Forms: {dom_metrics.get('forms', 0)}
- Links: {dom_metrics.get('links', 0)}
- Interactive Elements: {dom_metrics.get('interactive_elements', 0)}

HTML Snippet:
{html_snippet[:1000]}

Classify the page type as ONE of:
- AUTH_LOGIN: Login/signin page
- AUTH_SIGNUP: Registration/signup page
- AUTH_FORGOT_PASSWORD: Password reset page
- ECOMMERCE_PRODUCT: Product detail page
- ECOMMERCE_CART: Shopping cart page
- ECOMMERCE_CHECKOUT: Checkout page
- SAAS_DASHBOARD: Application dashboard
- SAAS_SETTINGS: Settings/preferences page
- ADMIN_PANEL: Admin/management interface
- CONTENT_ARTICLE: Article/blog post
- CONTENT_LANDING: Landing/marketing page
- SEARCH_RESULTS: Search results page
- USER_PROFILE: User profile page
- UNKNOWN: Cannot determine

Respond in JSON format:
{{
  "page_type": "TYPE_HERE",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "primary_purpose": "What users do on this page"
}}"""
        
        try:
            response = self.client.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            result["llm_used"] = True
            return result
            
        except Exception as e:
            print(f"LLM classification failed: {e}")
            return {
                "page_type": "UNKNOWN",
                "confidence": 0.0,
                "reasoning": f"LLM error: {str(e)}",
                "llm_used": False
            }
    
    async def identify_element_role(
        self,
        element_html: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Identify semantic role of an element using LLM.
        
        Args:
            element_html: HTML of the element
            context: Surrounding context
        
        Returns:
            Dict with role, confidence, and reasoning
        """
        if not self.enabled:
            return {
                "role": "UNKNOWN",
                "confidence": 0.0,
                "reasoning": "LLM not available",
                "llm_used": False
            }
        
        prompt = f"""Identify the semantic role of this HTML element.

Element HTML:
{element_html}

Context:
{context}

Classify as ONE of:
- BUTTON: Clickable button
- LINK: Navigation link
- TEXTBOX: Text input field
- CHECKBOX: Checkbox input
- RADIO: Radio button
- COMBOBOX: Select/dropdown
- HEADING: Heading element
- IMAGE: Image element
- LIST: List container
- LISTITEM: List item
- NAVIGATION: Navigation menu
- MAIN: Main content area
- FORM: Form container
- DIALOG: Modal/dialog
- ALERT: Alert/notification
- UNKNOWN: Cannot determine

Respond in JSON format:
{{
  "role": "ROLE_HERE",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}"""
        
        try:
            response = self.client.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            result["llm_used"] = True
            return result
            
        except Exception as e:
            print(f"LLM role identification failed: {e}")
            return {
                "role": "UNKNOWN",
                "confidence": 0.0,
                "reasoning": f"LLM error: {str(e)}",
                "llm_used": False
            }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize LLM service
        llm = LLMService()
        
        if llm.enabled:
            print("✅ LLM Service initialized with Gemini API")
        else:
            print("⚠️  LLM Service running in fallback mode (no API key)")
        
        # Test page classification
        result = await llm.classify_page_type(
            url="https://example.com/login",
            title="Login - Example App",
            description="Sign in to your account",
            html_snippet="<form><input type='text' name='username'/><input type='password'/><button>Login</button></form>",
            dom_metrics={"total_elements": 50, "forms": 1, "links": 5, "interactive_elements": 10}
        )
        
        print(f"\nPage Classification:")
        print(f"  Type: {result['page_type']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  LLM Used: {result['llm_used']}")
        if 'reasoning' in result:
            print(f"  Reasoning: {result['reasoning']}")
    
    asyncio.run(main())
