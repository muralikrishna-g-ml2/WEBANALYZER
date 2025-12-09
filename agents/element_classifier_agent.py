"""
Element Classifier Agent

Applies LQS scoring to discovered elements and generates quality report.
Acts as a quality gate before POM generation.
"""

from typing import List, Dict, Any

from schemas import (
    ElementClassificationMap,
    ElementLocator,
    LQSReport,
    LQSCategory,
)
from core import LQSStandard


class ElementClassifierAgent:
    """
    Element Classifier Agent - Quality assurance gatekeeper.
    
    Responsibilities:
    - Apply LQS scoring to all discovered elements
    - Categorize elements (BEST, GOOD, OK, FAIL)
    - Generate recommendations for improvement
    - Filter out rejected elements
    - Provide quality metrics for decision-making
    """
    
    def __init__(self):
        """Initialize Element Classifier Agent"""
        self.lqs_standard = LQSStandard()
    
    def classify_elements(
        self,
        element_map: ElementClassificationMap
    ) -> LQSReport:
        """
        Classify all elements and generate LQS Report.
        
        Args:
            element_map: Map of discovered elements from Observer Agent
        
        Returns:
            LQSReport with scored and categorized elements
        """
        scored_elements: List[ElementLocator] = []
        
        # Score each element
        for element in element_map.elements:
            # Calculate LQS
            score, category, rationale = self.lqs_standard.calculate_lqs(
                strategy=element.locator_strategy,
                locator_value=element.locator_value,
                element_role=element.semantic_role,
                has_stable_attributes=self._has_stable_attributes(element),
                is_unique=True,  # Assume unique for now; would need validation
            )
            
            # Update element with LQS data
            element.lqs_score = score
            element.lqs_category = category
            element.stability_rationale = rationale
            
            # Generate alternative locators if current one is poor
            if category in [LQSCategory.OK, LQSCategory.FAIL]:
                element.alternative_locators = self._generate_alternatives(element)
            
            scored_elements.append(element)
        
        # Categorize elements
        approved = [e for e in scored_elements if e.lqs_category in [LQSCategory.BEST, LQSCategory.GOOD]]
        flagged = [e for e in scored_elements if e.lqs_category == LQSCategory.OK]
        rejected = [e for e in scored_elements if e.lqs_category == LQSCategory.FAIL]
        
        # Calculate overall quality score
        if scored_elements:
            overall_score = sum(e.lqs_score for e in scored_elements) / len(scored_elements)
        else:
            overall_score = 0.0
        
        # Generate recommendations
        recommendations = self.lqs_standard.generate_recommendations(scored_elements)
        
        return LQSReport(
            url=element_map.url,
            total_elements_analyzed=len(scored_elements),
            approved_elements=approved,
            flagged_elements=flagged,
            rejected_elements=rejected,
            overall_quality_score=overall_score,
            recommendations=recommendations,
        )
    
    def _has_stable_attributes(self, element: ElementLocator) -> bool:
        """
        Determine if element has stable attributes.
        
        Checks for:
        - data-testid
        - stable id (not dynamic/generated)
        - aria-label
        """
        # Check locator value for stability indicators
        locator_value = element.locator_value.lower()
        
        # Has test ID
        if element.locator_value.startswith('[data-testid'):
            return True
        
        # Has stable ID (not dynamic)
        if locator_value.startswith('#'):
            has_dynamic_pattern = any(
                pattern in locator_value
                for pattern in ['random', 'generated', 'uuid', 'temp', 'timestamp']
            )
            return not has_dynamic_pattern
        
        # Has aria-label
        if 'aria-label' in locator_value:
            return True
        
        return False
    
    def _generate_alternatives(self, element: ElementLocator) -> List[Dict[str, str]]:
        """
        Generate alternative locator strategies for poor-quality locators.
        
        Args:
            element: Element with poor LQS
        
        Returns:
            List of alternative locator strategies
        """
        alternatives = []
        
        # Suggest semantic strategies based on role
        recommended_strategy = self.lqs_standard.get_recommended_strategy(element.semantic_role)
        
        if recommended_strategy != element.locator_strategy:
            alternatives.append({
                "strategy": recommended_strategy.value,
                "suggestion": f"Use {recommended_strategy.value} for better stability",
                "priority": "HIGH"
            })
        
        # If no user-facing label, suggest adding one
        if not element.user_facing_label:
            alternatives.append({
                "strategy": "getByLabel",
                "suggestion": "Add aria-label or label element for accessibility",
                "priority": "MEDIUM"
            })
        
        # Always suggest test ID as fallback
        if element.locator_strategy.value != "getByTestId":
            alternatives.append({
                "strategy": "getByTestId",
                "suggestion": "Add data-testid attribute for stable testing",
                "priority": "LOW"
            })
        
        return alternatives


# Example usage
if __name__ == "__main__":
    from schemas import ElementRole, LocatorStrategy
    from datetime import datetime
    
    # Create sample element map
    element_map = ElementClassificationMap(
        url="https://example.com",
        total_elements=3,
        elements=[
            ElementLocator(
                element_id="elem_0",
                semantic_role=ElementRole.BUTTON,
                locator_strategy=LocatorStrategy.GET_BY_ROLE,
                locator_value="button",
                lqs_score=0,
                lqs_category=LQSCategory.FAIL,
                stability_rationale="Pending",
                user_facing_label="Submit",
            ),
            ElementLocator(
                element_id="elem_1",
                semantic_role=ElementRole.TEXTBOX,
                locator_strategy=LocatorStrategy.XPATH,
                locator_value="/html/body/div[1]/input",
                lqs_score=0,
                lqs_category=LQSCategory.FAIL,
                stability_rationale="Pending",
                user_facing_label="Username",
            ),
            ElementLocator(
                element_id="elem_2",
                semantic_role=ElementRole.LINK,
                locator_strategy=LocatorStrategy.CSS_SELECTOR,
                locator_value=".nav-link",
                lqs_score=0,
                lqs_category=LQSCategory.FAIL,
                stability_rationale="Pending",
            ),
        ],
        timestamp=datetime.now().isoformat()
    )
    
    # Classify elements
    classifier = ElementClassifierAgent()
    lqs_report = classifier.classify_elements(element_map)
    
    print(f"Total Elements: {lqs_report.total_elements_analyzed}")
    print(f"Approved: {len(lqs_report.approved_elements)}")
    print(f"Flagged: {len(lqs_report.flagged_elements)}")
    print(f"Rejected: {len(lqs_report.rejected_elements)}")
    print(f"Overall Quality: {lqs_report.overall_quality_score:.1f}/100")
    print(f"\nRecommendations:")
    for rec in lqs_report.recommendations:
        print(f"  - {rec}")
