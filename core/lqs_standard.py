"""
Locator Quality Score (LQS) Standard Implementation

Implements the scoring heuristics and validation logic for evaluating
Playwright locator quality and stability.
"""

from typing import Dict, List, Tuple
from schemas.schemas import (
    LocatorStrategy,
    LQSCategory,
    ElementLocator,
    ElementRole
)


class LQSStandard:
    """
    Locator Quality Score Standard for Semantic POM Generation.
    
    Enforces Playwright best practices by scoring locators based on
    stability, maintainability, and resistance to UI changes.
    """
    
    # Scoring matrix: strategy -> base score
    STRATEGY_SCORES: Dict[LocatorStrategy, int] = {
        LocatorStrategy.GET_BY_ROLE: 95,
        LocatorStrategy.GET_BY_LABEL: 95,
        LocatorStrategy.GET_BY_TEST_ID: 90,
        LocatorStrategy.GET_BY_TEXT: 85,
        LocatorStrategy.GET_BY_PLACEHOLDER: 80,
        LocatorStrategy.CSS_SELECTOR: 70,
        LocatorStrategy.XPATH: 40,
    }
    
    # Category thresholds
    CATEGORY_THRESHOLDS = {
        LQSCategory.BEST: 90,
        LQSCategory.GOOD: 70,
        LQSCategory.OK: 30,
        LQSCategory.FAIL: 0,
    }
    
    # Stability rationales
    RATIONALES = {
        LocatorStrategy.GET_BY_ROLE: (
            "Locator based on accessibility tree and semantic intent. "
            "Highly resistant to layout or styling changes."
        ),
        LocatorStrategy.GET_BY_LABEL: (
            "Locator based on form labels. "
            "Stable as long as user-facing text remains consistent."
        ),
        LocatorStrategy.GET_BY_TEST_ID: (
            "Unique, stable handle explicitly designed for testing. "
            "Requires development team to maintain data-testid attributes."
        ),
        LocatorStrategy.GET_BY_TEXT: (
            "Locator based on visible text content. "
            "Stable but may break with text changes or i18n."
        ),
        LocatorStrategy.GET_BY_PLACEHOLDER: (
            "Locator based on input placeholder text. "
            "Reasonably stable for form inputs."
        ),
        LocatorStrategy.CSS_SELECTOR: (
            "CSS-based selector. Stability depends on class naming conventions. "
            "Avoid overly specific or dynamic class paths."
        ),
        LocatorStrategy.XPATH: (
            "XPath locator. Highly susceptible to DOM restructuring. "
            "Use only as last resort for deeply nested structures."
        ),
    }
    
    @classmethod
    def calculate_lqs(
        cls,
        strategy: LocatorStrategy,
        locator_value: str,
        element_role: ElementRole,
        has_stable_attributes: bool = True,
        is_unique: bool = True,
    ) -> Tuple[int, LQSCategory, str]:
        """
        Calculate Locator Quality Score for a given locator.
        
        Args:
            strategy: The Playwright locator strategy used
            locator_value: The actual locator string
            element_role: Semantic role of the element
            has_stable_attributes: Whether element has stable attributes (id, data-testid)
            is_unique: Whether locator uniquely identifies the element
            
        Returns:
            Tuple of (score, category, rationale)
        """
        # Start with base score for strategy
        score = cls.STRATEGY_SCORES.get(strategy, 0)
        
        # Apply modifiers
        if not is_unique:
            score -= 20  # Non-unique locators are unreliable
            
        if strategy == LocatorStrategy.CSS_SELECTOR:
            score = cls._adjust_css_score(locator_value, has_stable_attributes)
            
        elif strategy == LocatorStrategy.XPATH:
            score = cls._adjust_xpath_score(locator_value)
        
        # Determine category
        category = cls._get_category(score)
        
        # Get rationale
        rationale = cls.RATIONALES.get(strategy, "Unknown locator strategy")
        if not is_unique:
            rationale += " WARNING: Locator is not unique and may match multiple elements."
        
        return score, category, rationale
    
    @classmethod
    def _adjust_css_score(cls, locator_value: str, has_stable_attributes: bool) -> int:
        """Adjust score for CSS selectors based on complexity and stability"""
        base_score = 70
        
        # Check for dynamic/unstable patterns
        if any(pattern in locator_value.lower() for pattern in [
            'random', 'generated', 'uuid', 'timestamp', 'temp'
        ]):
            return 20  # Likely dynamic, very unstable
        
        # Check for overly specific selectors (many levels)
        depth = locator_value.count('>') + locator_value.count(' ')
        if depth > 5:
            base_score -= 15  # Deep nesting is fragile
        
        # Check for ID-based CSS (good if stable)
        if locator_value.startswith('#') and has_stable_attributes:
            base_score = 85
        elif locator_value.startswith('#'):
            base_score = 60  # ID might be dynamic
        
        # Check for class-only selectors
        if locator_value.startswith('.') and locator_value.count('.') == 1:
            base_score = 75  # Simple class selector
        
        return max(30, min(89, base_score))  # Keep in GOOD range
    
    @classmethod
    def _adjust_xpath_score(cls, locator_value: str) -> int:
        """Adjust score for XPath selectors based on complexity"""
        base_score = 40
        
        # Absolute XPath is very fragile
        if locator_value.startswith('/html/'):
            return 10
        
        # Check for position-based selectors (fragile)
        if '[1]' in locator_value or '[2]' in locator_value:
            base_score -= 10
        
        # Relative XPath with attributes is better
        if locator_value.startswith('//') and '@' in locator_value:
            base_score = 50
        
        return max(10, min(69, base_score))  # Keep in OK/FAIL range
    
    @classmethod
    def _get_category(cls, score: int) -> LQSCategory:
        """Determine LQS category from score"""
        if score >= cls.CATEGORY_THRESHOLDS[LQSCategory.BEST]:
            return LQSCategory.BEST
        elif score >= cls.CATEGORY_THRESHOLDS[LQSCategory.GOOD]:
            return LQSCategory.GOOD
        elif score >= cls.CATEGORY_THRESHOLDS[LQSCategory.OK]:
            return LQSCategory.OK
        else:
            return LQSCategory.FAIL
    
    @classmethod
    def should_reject(cls, score: int, category: LQSCategory) -> bool:
        """Determine if a locator should be automatically rejected"""
        return category == LQSCategory.FAIL or score < 30
    
    @classmethod
    def get_recommended_strategy(cls, element_role: ElementRole) -> LocatorStrategy:
        """
        Get recommended locator strategy for a given element role.
        
        Prioritizes semantic, accessibility-based strategies.
        """
        # Map element roles to preferred strategies
        role_strategy_map = {
            ElementRole.BUTTON: LocatorStrategy.GET_BY_ROLE,
            ElementRole.TEXTBOX: LocatorStrategy.GET_BY_LABEL,
            ElementRole.COMBOBOX: LocatorStrategy.GET_BY_LABEL,
            ElementRole.CHECKBOX: LocatorStrategy.GET_BY_LABEL,
            ElementRole.RADIO: LocatorStrategy.GET_BY_LABEL,
            ElementRole.LINK: LocatorStrategy.GET_BY_ROLE,
            ElementRole.HEADING: LocatorStrategy.GET_BY_ROLE,
            ElementRole.IMAGE: LocatorStrategy.GET_BY_ROLE,
        }
        
        return role_strategy_map.get(element_role, LocatorStrategy.GET_BY_TEST_ID)
    
    @classmethod
    def generate_recommendations(cls, elements: List[ElementLocator]) -> List[str]:
        """
        Generate specific recommendations for improving locator quality.
        
        Args:
            elements: List of analyzed elements
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Count elements by category
        category_counts = {cat: 0 for cat in LQSCategory}
        for elem in elements:
            category_counts[elem.lqs_category] += 1
        
        # Analyze and recommend
        total = len(elements)
        fail_pct = (category_counts[LQSCategory.FAIL] / total * 100) if total > 0 else 0
        ok_pct = (category_counts[LQSCategory.OK] / total * 100) if total > 0 else 0
        
        if fail_pct > 10:
            recommendations.append(
                f"{category_counts[LQSCategory.FAIL]} elements ({fail_pct:.1f}%) have FAIL-quality locators. "
                "Consider adding data-testid attributes to these elements."
            )
        
        if ok_pct > 20:
            recommendations.append(
                f"{category_counts[LQSCategory.OK]} elements ({ok_pct:.1f}%) have OK-quality locators. "
                "Review these for potential upgrades to semantic locators (getByRole, getByLabel)."
            )
        
        # Check for XPath usage
        xpath_count = sum(1 for e in elements if e.locator_strategy == LocatorStrategy.XPATH)
        if xpath_count > 0:
            recommendations.append(
                f"{xpath_count} elements use XPath locators, which are fragile. "
                "Refactor to use semantic strategies where possible."
            )
        
        # Check for CSS complexity
        complex_css = sum(
            1 for e in elements 
            if e.locator_strategy == LocatorStrategy.CSS_SELECTOR 
            and (e.locator_value.count('>') + e.locator_value.count(' ')) > 5
        )
        if complex_css > 0:
            recommendations.append(
                f"{complex_css} CSS selectors are overly complex (deep nesting). "
                "Simplify or use data-testid for better stability."
            )
        
        if not recommendations:
            recommendations.append(
                "Excellent! All locators meet quality standards. "
                "Continue using semantic strategies for new elements."
            )
        
        return recommendations


# Convenience function for quick scoring
def score_locator(
    strategy: LocatorStrategy,
    value: str,
    role: ElementRole,
    **kwargs
) -> ElementLocator:
    """
    Quick helper to score a locator and create an ElementLocator object.
    
    Args:
        strategy: Playwright locator strategy
        value: Locator value/selector
        role: Semantic role of element
        **kwargs: Additional ElementLocator fields
        
    Returns:
        Fully populated ElementLocator with LQS data
    """
    score, category, rationale = LQSStandard.calculate_lqs(
        strategy=strategy,
        locator_value=value,
        element_role=role,
        has_stable_attributes=kwargs.get('has_stable_attributes', True),
        is_unique=kwargs.get('is_unique', True),
    )
    
    # Filter out LQS calculation parameters from kwargs
    filtered_kwargs = {
        k: v for k, v in kwargs.items() 
        if k not in ['has_stable_attributes', 'is_unique']
    }
    
    return ElementLocator(
        element_id=filtered_kwargs.pop('element_id', 'unknown'),
        semantic_role=role,
        locator_strategy=strategy,
        locator_value=value,
        lqs_score=score,
        lqs_category=category,
        stability_rationale=rationale,
        **filtered_kwargs
    )
