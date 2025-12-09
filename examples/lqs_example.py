"""
Example: Using the LQS Standard to score locators

Demonstrates how to use the Locator Quality Score system to evaluate
and compare different locator strategies.
"""

from schemas import LocatorStrategy, ElementRole
from core import LQSStandard, score_locator


def main():
    print("=" * 70)
    print("Locator Quality Score (LQS) Standard - Example")
    print("=" * 70)
    print()
    
    # Example 1: Semantic locator (BEST)
    print("Example 1: Semantic Locator (getByRole)")
    print("-" * 70)
    
    login_button = score_locator(
        strategy=LocatorStrategy.GET_BY_ROLE,
        value="button",
        role=ElementRole.BUTTON,
        element_id="login_btn",
        user_facing_label="Login",
        is_unique=True,
    )
    
    print(f"Element: {login_button.user_facing_label}")
    print(f"Strategy: {login_button.locator_strategy.value}")
    print(f"Locator: page.getByRole('{login_button.locator_value}')")
    print(f"LQS Score: {login_button.lqs_score}/100")
    print(f"Category: {login_button.lqs_category.value}")
    print(f"Rationale: {login_button.stability_rationale}")
    print()
    
    # Example 2: Test ID locator (BEST)
    print("Example 2: Test ID Locator (getByTestId)")
    print("-" * 70)
    
    username_field = score_locator(
        strategy=LocatorStrategy.GET_BY_TEST_ID,
        value="username-input",
        role=ElementRole.TEXTBOX,
        element_id="username_field",
        user_facing_label="Username",
        is_unique=True,
    )
    
    print(f"Element: {username_field.user_facing_label}")
    print(f"Strategy: {username_field.locator_strategy.value}")
    print(f"Locator: page.getByTestId('{username_field.locator_value}')")
    print(f"LQS Score: {username_field.lqs_score}/100")
    print(f"Category: {username_field.lqs_category.value}")
    print(f"Rationale: {username_field.stability_rationale}")
    print()
    
    # Example 3: CSS selector (GOOD)
    print("Example 3: CSS Selector (Stable Class)")
    print("-" * 70)
    
    submit_btn = score_locator(
        strategy=LocatorStrategy.CSS_SELECTOR,
        value=".submit-button",
        role=ElementRole.BUTTON,
        element_id="submit_btn",
        user_facing_label="Submit",
        is_unique=True,
        has_stable_attributes=True,
    )
    
    print(f"Element: {submit_btn.user_facing_label}")
    print(f"Strategy: {submit_btn.locator_strategy.value}")
    print(f"Locator: page.locator('{submit_btn.locator_value}')")
    print(f"LQS Score: {submit_btn.lqs_score}/100")
    print(f"Category: {submit_btn.lqs_category.value}")
    print(f"Rationale: {submit_btn.stability_rationale}")
    print()
    
    # Example 4: Complex CSS (OK - Flagged)
    print("Example 4: Complex CSS Selector (Deep Nesting)")
    print("-" * 70)
    
    nested_element = score_locator(
        strategy=LocatorStrategy.CSS_SELECTOR,
        value="div.container > div.row > div.col > div.card > button.action",
        role=ElementRole.BUTTON,
        element_id="nested_btn",
        user_facing_label="Action Button",
        is_unique=True,
        has_stable_attributes=False,
    )
    
    print(f"Element: {nested_element.user_facing_label}")
    print(f"Strategy: {nested_element.locator_strategy.value}")
    print(f"Locator: page.locator('{nested_element.locator_value}')")
    print(f"LQS Score: {nested_element.lqs_score}/100")
    print(f"Category: {nested_element.lqs_category.value}")
    print(f"Rationale: {nested_element.stability_rationale}")
    print()
    
    # Example 5: XPath (FAIL - Rejected)
    print("Example 5: XPath Locator (Absolute Path)")
    print("-" * 70)
    
    xpath_element = score_locator(
        strategy=LocatorStrategy.XPATH,
        value="/html/body/div[1]/div[2]/form/button[1]",
        role=ElementRole.BUTTON,
        element_id="xpath_btn",
        user_facing_label="Submit Form",
        is_unique=True,
    )
    
    print(f"Element: {xpath_element.user_facing_label}")
    print(f"Strategy: {xpath_element.locator_strategy.value}")
    print(f"Locator: page.locator('{xpath_element.locator_value}')")
    print(f"LQS Score: {xpath_element.lqs_score}/100")
    print(f"Category: {xpath_element.lqs_category.value}")
    print(f"Should Reject: {LQSStandard.should_reject(xpath_element.lqs_score, xpath_element.lqs_category)}")
    print(f"Rationale: {xpath_element.stability_rationale}")
    print()
    
    # Generate recommendations
    print("=" * 70)
    print("Recommendations")
    print("=" * 70)
    
    all_elements = [
        login_button,
        username_field,
        submit_btn,
        nested_element,
        xpath_element,
    ]
    
    recommendations = LQSStandard.generate_recommendations(all_elements)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    print()
    
    # Show recommended strategies by role
    print("=" * 70)
    print("Recommended Strategies by Element Role")
    print("=" * 70)
    
    roles_to_check = [
        ElementRole.BUTTON,
        ElementRole.TEXTBOX,
        ElementRole.CHECKBOX,
        ElementRole.LINK,
    ]
    
    for role in roles_to_check:
        recommended = LQSStandard.get_recommended_strategy(role)
        print(f"{role.value:15} -> {recommended.value}")
    print()


if __name__ == "__main__":
    main()
