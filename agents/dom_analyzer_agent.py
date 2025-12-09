"""
DOM Analyzer Agent

Specialized agent for low-level structural analysis of HTML DOM.
Focuses on quantitative metrics and structural patterns.
"""

from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from collections import Counter
import re


class DOMAnalyzerAgent:
    """
    DOM Analyzer Agent - Structural analysis specialist.
    
    Responsibilities:
    - Parse HTML structure efficiently
    - Quantify element density and hierarchy
    - Extract link targets and navigation paths
    - Build component hierarchy map
    - Identify structural patterns (forms, tables, lists)
    - Calculate DOM complexity metrics
    """
    
    def __init__(self):
        """Initialize DOM Analyzer Agent"""
        pass
    
    def analyze(self, html: str, url: str) -> Dict[str, Any]:
        """
        Perform comprehensive DOM analysis.
        
        Args:
            html: Raw HTML content
            url: Source URL for context
        
        Returns:
            Dict with structural analysis results
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            return {
                "status": "success",
                "url": url,
                "metrics": self._calculate_metrics(soup),
                "hierarchy": self._analyze_hierarchy(soup),
                "navigation": self._extract_navigation(soup, url),
                "forms": self._analyze_forms(soup),
                "structural_patterns": self._identify_patterns(soup),
                "complexity": self._calculate_complexity(soup),
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def _calculate_metrics(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Calculate basic DOM metrics"""
        return {
            "total_elements": len(soup.find_all()),
            "interactive_elements": len(soup.find_all(['button', 'a', 'input', 'select', 'textarea'])),
            "links": len(soup.find_all('a', href=True)),
            "forms": len(soup.find_all('form')),
            "images": len(soup.find_all('img')),
            "headings": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            "lists": len(soup.find_all(['ul', 'ol'])),
            "tables": len(soup.find_all('table')),
            "divs": len(soup.find_all('div')),
            "spans": len(soup.find_all('span')),
        }
    
    def _analyze_hierarchy(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze DOM hierarchy and depth"""
        def get_depth(element, current_depth=0):
            """Recursively calculate max depth"""
            if not element.children:
                return current_depth
            
            max_child_depth = current_depth
            for child in element.children:
                if hasattr(child, 'children'):
                    child_depth = get_depth(child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)
            
            return max_child_depth
        
        body = soup.find('body')
        max_depth = get_depth(body) if body else 0
        
        # Find main content containers
        main_containers = soup.find_all(['main', 'article', 'section'])
        
        return {
            "max_depth": max_depth,
            "main_containers": len(main_containers),
            "sections": len(soup.find_all('section')),
            "articles": len(soup.find_all('article')),
            "navs": len(soup.find_all('nav')),
            "headers": len(soup.find_all('header')),
            "footers": len(soup.find_all('footer')),
        }
    
    def _extract_navigation(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract navigation links and structure"""
        links = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Classify link type
            link_type = "external"
            if href.startswith('/') or base_url in href:
                link_type = "internal"
            elif href.startswith('#'):
                link_type = "anchor"
            elif href.startswith('mailto:'):
                link_type = "email"
            elif href.startswith('tel:'):
                link_type = "phone"
            
            links.append({
                "href": href,
                "text": text[:100] if text else None,
                "type": link_type,
            })
        
        # Count by type
        link_types = Counter(link['type'] for link in links)
        
        return {
            "total_links": len(links),
            "by_type": dict(link_types),
            "links": links[:50],  # Limit to first 50 for performance
        }
    
    def _analyze_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Analyze form structures"""
        forms = []
        
        for form in soup.find_all('form'):
            inputs = form.find_all(['input', 'select', 'textarea'])
            
            form_data = {
                "action": form.get('action'),
                "method": form.get('method', 'get').upper(),
                "id": form.get('id'),
                "total_inputs": len(inputs),
                "input_types": [],
            }
            
            # Analyze input types
            input_types = Counter()
            for inp in inputs:
                if inp.name == 'input':
                    input_types[inp.get('type', 'text')] += 1
                else:
                    input_types[inp.name] += 1
            
            form_data["input_types"] = dict(input_types)
            forms.append(form_data)
        
        return forms
    
    def _identify_patterns(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Identify common structural patterns"""
        patterns = {
            "has_navigation": bool(soup.find('nav')),
            "has_header": bool(soup.find('header')),
            "has_footer": bool(soup.find('footer')),
            "has_sidebar": bool(soup.find(['aside', 'div'], class_=re.compile(r'sidebar|side-bar', re.I))),
            "has_modal": bool(soup.find(['div'], class_=re.compile(r'modal|dialog', re.I))),
            "has_carousel": bool(soup.find(['div'], class_=re.compile(r'carousel|slider|slideshow', re.I))),
            "has_tabs": bool(soup.find(['div', 'ul'], class_=re.compile(r'tab|tabs', re.I))),
            "has_accordion": bool(soup.find(['div'], class_=re.compile(r'accordion|collapse', re.I))),
            "has_dropdown": bool(soup.find(['div', 'ul'], class_=re.compile(r'dropdown|drop-down', re.I))),
        }
        
        # Detect grid/card layouts
        cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|product', re.I))
        patterns["has_card_layout"] = len(cards) > 3
        patterns["card_count"] = len(cards)
        
        return patterns
    
    def _calculate_complexity(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Calculate DOM complexity metrics"""
        all_elements = soup.find_all()
        
        # Calculate class usage
        class_usage = Counter()
        for elem in all_elements:
            classes = elem.get('class', [])
            for cls in classes:
                class_usage[cls] += 1
        
        # Calculate ID usage
        id_usage = Counter()
        for elem in all_elements:
            elem_id = elem.get('id')
            if elem_id:
                id_usage[elem_id] += 1
        
        # Detect dynamic IDs (likely generated)
        dynamic_ids = sum(
            1 for elem_id in id_usage.keys()
            if any(pattern in elem_id.lower() for pattern in ['random', 'generated', 'uuid', 'temp'])
        )
        
        return {
            "total_elements": len(all_elements),
            "unique_classes": len(class_usage),
            "unique_ids": len(id_usage),
            "duplicate_ids": sum(1 for count in id_usage.values() if count > 1),
            "dynamic_ids_detected": dynamic_ids,
            "most_common_classes": dict(class_usage.most_common(10)),
            "complexity_score": self._score_complexity(len(all_elements), len(class_usage)),
        }
    
    def _score_complexity(self, total_elements: int, unique_classes: int) -> str:
        """Score overall DOM complexity"""
        if total_elements < 100:
            return "LOW"
        elif total_elements < 500:
            return "MEDIUM"
        elif total_elements < 2000:
            return "HIGH"
        else:
            return "VERY_HIGH"


# Example usage
if __name__ == "__main__":
    # Example HTML
    html = """
    <html>
        <body>
            <header>
                <nav>
                    <a href="/">Home</a>
                    <a href="/about">About</a>
                </nav>
            </header>
            <main>
                <form action="/login" method="post">
                    <input type="text" name="username" />
                    <input type="password" name="password" />
                    <button type="submit">Login</button>
                </form>
            </main>
            <footer>
                <p>Copyright 2024</p>
            </footer>
        </body>
    </html>
    """
    
    analyzer = DOMAnalyzerAgent()
    result = analyzer.analyze(html, "https://example.com")
    
    import json
    print(json.dumps(result, indent=2))
