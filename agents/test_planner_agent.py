"""
Test Planner Agent

Generates test scenarios and plans based on page analysis.
Creates structured test cases that cover user flows.
"""

from typing import List, Dict, Any

from schemas import (
    PageContextOntology,
    LQSReport,
    TestPlan,
    TestScenario,
    PageType,
)


class TestPlannerAgent:
    """
    Test Planner Agent - Test strategy specialist.
    
    Responsibilities:
    - Generate test scenarios based on page type
    - Identify critical user flows
    - Define required test fixtures
    - Create structured test plans
    - Prioritize test coverage
    """
    
    def __init__(self):
        """Initialize Test Planner Agent"""
        pass
    
    def plan_tests(
        self,
        page_context: PageContextOntology,
        lqs_report: LQSReport,
    ) -> TestPlan:
        """
        Generate test plan for the analyzed page.
        
        Args:
            page_context: Page classification and context
            lqs_report: LQS report with approved elements
        
        Returns:
            TestPlan with scenarios and fixtures
        """
        # Generate scenarios based on page type
        scenarios = self._generate_scenarios(page_context, lqs_report)
        
        # Identify required fixtures
        fixtures = self._identify_fixtures(page_context, scenarios)
        
        # Add coverage notes
        coverage_notes = self._generate_coverage_notes(page_context, lqs_report)
        
        return TestPlan(
            url=page_context.url,
            page_type=page_context.page_type,
            scenarios=scenarios,
            required_fixtures=fixtures,
            coverage_notes=coverage_notes,
        )
    
    def _generate_scenarios(
        self,
        page_context: PageContextOntology,
        lqs_report: LQSReport
    ) -> List[TestScenario]:
        """Generate test scenarios based on page type"""
        scenarios = []
        
        # Get page type-specific scenarios
        type_scenarios = self._get_type_specific_scenarios(page_context.page_type)
        scenarios.extend(type_scenarios)
        
        # Add element interaction scenarios
        element_scenarios = self._get_element_scenarios(lqs_report)
        scenarios.extend(element_scenarios)
        
        # Add navigation scenarios
        if page_context.navigation_paths:
            scenarios.append(TestScenario(
                scenario_id="navigation_links",
                scenario_name="Navigation Links",
                description="Verify all navigation links are functional",
                steps=[
                    "Navigate to page",
                    "Verify navigation menu is visible",
                    "Click each navigation link",
                    "Verify correct page loads"
                ],
                priority="medium",
                expected_outcome="All navigation links work correctly"
            ))
        
        return scenarios
    
    def _get_type_specific_scenarios(self, page_type: PageType) -> List[TestScenario]:
        """Get scenarios specific to page type"""
        scenarios_map = {
            PageType.AUTH_LOGIN: [
                TestScenario(
                    scenario_id="login_success",
                    scenario_name="Successful Login",
                    description="User can log in with valid credentials",
                    steps=[
                        "Navigate to login page",
                        "Enter valid username",
                        "Enter valid password",
                        "Click login button",
                        "Verify redirect to dashboard"
                    ],
                    priority="high",
                    expected_outcome="User is logged in and redirected"
                ),
                TestScenario(
                    scenario_id="login_invalid",
                    scenario_name="Failed Login - Invalid Credentials",
                    description="System rejects invalid credentials",
                    steps=[
                        "Navigate to login page",
                        "Enter invalid username",
                        "Enter invalid password",
                        "Click login button",
                        "Verify error message displayed"
                    ],
                    priority="high",
                    expected_outcome="Error message shown, user not logged in"
                ),
                TestScenario(
                    scenario_id="login_validation",
                    scenario_name="Empty Fields Validation",
                    description="System validates required fields",
                    steps=[
                        "Navigate to login page",
                        "Leave username empty",
                        "Leave password empty",
                        "Click login button",
                        "Verify validation errors"
                    ],
                    priority="medium",
                    expected_outcome="Validation errors displayed"
                ),
            ],
            PageType.AUTH_SIGNUP: [
                TestScenario(
                    scenario_id="signup_success",
                    scenario_name="Successful Registration",
                    description="User can create new account",
                    steps=[
                        "Navigate to signup page",
                        "Fill all required fields",
                        "Submit form",
                        "Verify account created"
                    ],
                    priority="high",
                    expected_outcome="Account created successfully"
                ),
            ],
            PageType.ECOMMERCE_PRODUCT: [
                TestScenario(
                    scenario_id="add_to_cart",
                    scenario_name="Add to Cart",
                    description="User can add product to cart",
                    steps=[
                        "Navigate to product page",
                        "Select product options",
                        "Click add to cart",
                        "Verify cart updated"
                    ],
                    priority="high",
                    expected_outcome="Product added to cart"
                ),
            ],
            PageType.SAAS_DASHBOARD: [
                TestScenario(
                    scenario_id="dashboard_load",
                    scenario_name="Dashboard Load",
                    description="Dashboard displays all widgets",
                    steps=[
                        "Navigate to dashboard",
                        "Verify all widgets visible",
                        "Check data loads correctly"
                    ],
                    priority="high",
                    expected_outcome="Dashboard fully functional"
                ),
            ],
            PageType.CONTENT_LANDING: [
                TestScenario(
                    scenario_id="cta_interaction",
                    scenario_name="CTA Interaction",
                    description="Call-to-action buttons work",
                    steps=[
                        "Navigate to landing page",
                        "Locate primary CTA",
                        "Click CTA button",
                        "Verify expected action"
                    ],
                    priority="high",
                    expected_outcome="CTA leads to expected page/action"
                ),
            ],
        }
        
        return scenarios_map.get(page_type, [
            TestScenario(
                scenario_id="page_load",
                scenario_name="Page Load",
                description="Page loads successfully",
                steps=[
                    "Navigate to page",
                    "Verify page title",
                    "Verify main content visible"
                ],
                priority="high",
                expected_outcome="Page loads without errors"
            ),
        ])
    
    def _get_element_scenarios(self, lqs_report: LQSReport) -> List[TestScenario]:
        """Generate scenarios based on available elements"""
        scenarios = []
        
        # If we have forms (multiple textboxes + button)
        from schemas import ElementRole
        textboxes = [e for e in lqs_report.approved_elements if e.semantic_role == ElementRole.TEXTBOX]
        buttons = [e for e in lqs_report.approved_elements if e.semantic_role == ElementRole.BUTTON]
        
        if len(textboxes) >= 2 and buttons:
            scenarios.append(TestScenario(
                scenario_id="form_submission",
                scenario_name="Form Submission",
                description="User can fill and submit form",
                steps=[
                    "Navigate to page",
                    "Fill all form fields",
                    "Click submit button",
                    "Verify form submission"
                ],
                priority="high",
                expected_outcome="Form submitted successfully"
            ))
        
        return scenarios
    
    def _identify_fixtures(
        self,
        page_context: PageContextOntology,
        scenarios: List[TestScenario]
    ) -> Dict[str, str]:
        """Identify required test fixtures"""
        fixtures = {}
        
        # Common fixtures
        fixtures["baseURL"] = "Base URL for the application"
        
        # Page type-specific fixtures
        if page_context.page_type in [PageType.AUTH_LOGIN, PageType.AUTH_SIGNUP]:
            fixtures["validUser"] = "Valid user credentials for testing"
            fixtures["invalidUser"] = "Invalid user credentials for negative testing"
        
        if page_context.page_type in [PageType.ECOMMERCE_PRODUCT, PageType.ECOMMERCE_CART]:
            fixtures["testProduct"] = "Test product data"
            fixtures["paymentInfo"] = "Test payment information"
        
        if page_context.page_type == PageType.SAAS_DASHBOARD:
            fixtures["authenticatedUser"] = "Authenticated user session"
            fixtures["testData"] = "Sample data for dashboard"
        
        return fixtures
    
    def _generate_coverage_notes(
        self,
        page_context: PageContextOntology,
        lqs_report: LQSReport
    ) -> List[str]:
        """Generate coverage analysis notes"""
        notes = []
        
        # Element coverage
        total_elements = lqs_report.total_elements_analyzed
        approved = len(lqs_report.approved_elements)
        
        if total_elements > 0:
            coverage_pct = (approved / total_elements) * 100
            notes.append(f"Element coverage: {approved}/{total_elements} ({coverage_pct:.0f}%) elements approved for testing")
        
        # Quality notes
        if lqs_report.overall_quality_score >= 80:
            notes.append("High-quality locators enable reliable test automation")
        elif lqs_report.overall_quality_score >= 60:
            notes.append("Moderate locator quality - some tests may be fragile")
        else:
            notes.append("Low locator quality - consider improving element identifiers")
        
        # Dynamic content warning
        if page_context.dynamic_content:
            notes.append("Page has dynamic content - tests may need wait strategies")
        
        # Authentication requirement
        if page_context.requires_authentication:
            notes.append("Page requires authentication - setup auth fixtures")
        
        return notes


# Example usage
if __name__ == "__main__":
    from schemas import ElementRole, LocatorStrategy, LQSCategory, ElementLocator
    
    # Create sample data
    page_context = PageContextOntology(
        url="https://example.com/login",
        page_type=PageType.AUTH_LOGIN,
        primary_purpose="Authenticate user credentials",
        confidence_score=0.95,
        requires_authentication=False,
        dynamic_content=False,
    )
    
    lqs_report = LQSReport(
        url="https://example.com/login",
        total_elements_analyzed=3,
        approved_elements=[
            ElementLocator(
                element_id="username",
                semantic_role=ElementRole.TEXTBOX,
                locator_strategy=LocatorStrategy.GET_BY_LABEL,
                locator_value="Username",
                lqs_score=95,
                lqs_category=LQSCategory.BEST,
                stability_rationale="Label-based",
                user_facing_label="Username",
            ),
            ElementLocator(
                element_id="password",
                semantic_role=ElementRole.TEXTBOX,
                locator_strategy=LocatorStrategy.GET_BY_LABEL,
                locator_value="Password",
                lqs_score=95,
                lqs_category=LQSCategory.BEST,
                stability_rationale="Label-based",
                user_facing_label="Password",
            ),
            ElementLocator(
                element_id="submit",
                semantic_role=ElementRole.BUTTON,
                locator_strategy=LocatorStrategy.GET_BY_ROLE,
                locator_value="button",
                lqs_score=95,
                lqs_category=LQSCategory.BEST,
                stability_rationale="Role-based",
                user_facing_label="Login",
            ),
        ],
        flagged_elements=[],
        rejected_elements=[],
        overall_quality_score=95.0,
        recommendations=[]
    )
    
    # Plan tests
    planner = TestPlannerAgent()
    test_plan = planner.plan_tests(page_context, lqs_report)
    
    print(f"Test Plan for: {test_plan.url}")
    print(f"Page Type: {test_plan.page_type.value}")
    print(f"\nScenarios: {len(test_plan.scenarios)}")
    for scenario in test_plan.scenarios:
        print(f"\n  {scenario.priority.upper()}: {scenario.scenario_name}")
        print(f"  {scenario.description}")
        print(f"  Steps: {len(scenario.steps)}")
    
    print(f"\nRequired Fixtures: {len(test_plan.required_fixtures)}")
    for name, desc in test_plan.required_fixtures.items():
        print(f"  - {name}: {desc}")
    
    print(f"\nCoverage Notes:")
    for note in test_plan.coverage_notes:
        print(f"  - {note}")
