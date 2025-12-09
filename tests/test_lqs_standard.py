"""
Unit tests for LQS Standard
"""

import pytest
from schemas import LocatorStrategy, ElementRole, LQSCategory
from core import LQSStandard, score_locator


class TestLQSStandard:
    """Test suite for Locator Quality Score calculations"""
    
    def test_semantic_locator_best_score(self):
        """Semantic locators should get BEST category"""
        score, category, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.GET_BY_ROLE,
            locator_value="button",
            element_role=ElementRole.BUTTON,
            is_unique=True,
        )
        
        assert score >= 90
        assert category == LQSCategory.BEST
    
    def test_test_id_locator_best_score(self):
        """Test ID locators should get BEST category"""
        score, category, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.GET_BY_TEST_ID,
            locator_value="submit-button",
            element_role=ElementRole.BUTTON,
            is_unique=True,
        )
        
        assert score >= 90
        assert category == LQSCategory.BEST
    
    def test_simple_css_good_score(self):
        """Simple CSS selectors should get GOOD category"""
        score, category, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.CSS_SELECTOR,
            locator_value=".submit-btn",
            element_role=ElementRole.BUTTON,
            is_unique=True,
            has_stable_attributes=True,
        )
        
        assert 70 <= score < 90
        assert category == LQSCategory.GOOD
    
    def test_complex_css_lower_score(self):
        """Complex CSS selectors should get lower scores"""
        score, category, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.CSS_SELECTOR,
            locator_value="div > div > div > div > div > button",
            element_role=ElementRole.BUTTON,
            is_unique=True,
        )
        
        assert score < 70
    
    def test_absolute_xpath_fail_score(self):
        """Absolute XPath should get FAIL category"""
        score, category, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.XPATH,
            locator_value="/html/body/div[1]/button",
            element_role=ElementRole.BUTTON,
            is_unique=True,
        )
        
        assert score < 30
        assert category == LQSCategory.FAIL
    
    def test_non_unique_locator_penalty(self):
        """Non-unique locators should be penalized"""
        unique_score, _, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.GET_BY_ROLE,
            locator_value="button",
            element_role=ElementRole.BUTTON,
            is_unique=True,
        )
        
        non_unique_score, _, _ = LQSStandard.calculate_lqs(
            strategy=LocatorStrategy.GET_BY_ROLE,
            locator_value="button",
            element_role=ElementRole.BUTTON,
            is_unique=False,
        )
        
        assert non_unique_score < unique_score
    
    def test_should_reject_fail_category(self):
        """FAIL category locators should be rejected"""
        assert LQSStandard.should_reject(25, LQSCategory.FAIL) is True
        assert LQSStandard.should_reject(95, LQSCategory.BEST) is False
    
    def test_recommended_strategy_for_button(self):
        """Buttons should recommend getByRole"""
        strategy = LQSStandard.get_recommended_strategy(ElementRole.BUTTON)
        assert strategy == LocatorStrategy.GET_BY_ROLE
    
    def test_recommended_strategy_for_textbox(self):
        """Textboxes should recommend getByLabel"""
        strategy = LQSStandard.get_recommended_strategy(ElementRole.TEXTBOX)
        assert strategy == LocatorStrategy.GET_BY_LABEL
    
    def test_score_locator_helper(self):
        """Test the convenience score_locator function"""
        element = score_locator(
            strategy=LocatorStrategy.GET_BY_ROLE,
            value="button",
            role=ElementRole.BUTTON,
            element_id="test_btn",
            user_facing_label="Test Button",
        )
        
        assert element.element_id == "test_btn"
        assert element.lqs_score >= 90
        assert element.lqs_category == LQSCategory.BEST
        assert element.user_facing_label == "Test Button"
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        elements = [
            score_locator(
                strategy=LocatorStrategy.GET_BY_ROLE,
                value="button",
                role=ElementRole.BUTTON,
                element_id="btn1",
            ),
            score_locator(
                strategy=LocatorStrategy.XPATH,
                value="/html/body/div[1]",
                role=ElementRole.BUTTON,
                element_id="btn2",
            ),
        ]
        
        recommendations = LQSStandard.generate_recommendations(elements)
        
        assert len(recommendations) > 0
        assert isinstance(recommendations[0], str)
