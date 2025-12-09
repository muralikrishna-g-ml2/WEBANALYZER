"""
Test Generator Agent

Generates executable Playwright test files from test plans and POMs.
Creates .spec.ts files with proper fixtures and assertions.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from schemas import (
    TestPlan,
    GeneratedPOM,
    GeneratedTest,
    TestScenario,
    PageType,
)


class TestGeneratorAgent:
    """
    Test Generator Agent - Executable test creation specialist.
    
    Responsibilities:
    - Convert test plans to executable Playwright tests
    - Import and use generated POMs
    - Create proper test fixtures
    - Add assertions based on expected outcomes
    - Follow Playwright testing best practices
    - Generate TypeScript test files
    """
    
    def __init__(self):
        """Initialize Test Generator Agent"""
        pass
    
    def generate_tests(
        self,
        test_plan: TestPlan,
        generated_poms: List[GeneratedPOM],
    ) -> List[GeneratedTest]:
        """
        Generate executable test files from test plan.
        
        Args:
            test_plan: Test plan with scenarios
            generated_poms: List of generated POMs to import
        
        Returns:
            List of GeneratedTest objects
        """
        generated_tests = []
        
        # Group scenarios by priority for organization
        high_priority = [s for s in test_plan.scenarios if s.priority == "high"]
        medium_priority = [s for s in test_plan.scenarios if s.priority == "medium"]
        low_priority = [s for s in test_plan.scenarios if s.priority == "low"]
        
        # Generate test file for high priority scenarios
        if high_priority:
            test = self._generate_test_file(
                scenarios=high_priority,
                poms=generated_poms,
                test_plan=test_plan,
                file_suffix="critical"
            )
            generated_tests.append(test)
        
        # Generate test file for medium/low priority scenarios
        other_scenarios = medium_priority + low_priority
        if other_scenarios:
            test = self._generate_test_file(
                scenarios=other_scenarios,
                poms=generated_poms,
                test_plan=test_plan,
                file_suffix="standard"
            )
            generated_tests.append(test)
        
        return generated_tests
    
    def _generate_test_file(
        self,
        scenarios: List[TestScenario],
        poms: List[GeneratedPOM],
        test_plan: TestPlan,
        file_suffix: str
    ) -> GeneratedTest:
        """Generate a single test file"""
        # Generate file name
        page_name = self._get_page_name(test_plan.page_type)
        file_name = f"{page_name}.{file_suffix}.spec.ts"
        
        # Generate imports
        imports = self._generate_imports(poms)
        
        # Generate test suite
        test_suite = self._generate_test_suite(
            scenarios=scenarios,
            poms=poms,
            page_type=test_plan.page_type,
            page_name=page_name
        )
        
        # Combine into full code
        code = f"""{imports}

{test_suite}
"""
        
        return GeneratedTest(
            test_name=file_name.replace(".spec.ts", ""),
            url=test_plan.url,
            file_path=f"tests/{file_name}",
            code=code,
            scenarios_covered=[s.scenario_id for s in scenarios],
            assertions_count=self._count_assertions(scenarios),
        )
    
    def _generate_imports(self, poms: List[GeneratedPOM]) -> str:
        """Generate import statements"""
        imports = ["import { test, expect } from '@playwright/test';"]
        
        # Import POMs
        for pom in poms:
            class_name = pom.class_name
            # Convert file path to import path
            import_path = f"../{pom.file_path.replace('.ts', '')}"
            imports.append(f"import {{ {class_name} }} from '{import_path}';")
        
        return "\n".join(imports)
    
    def _generate_test_suite(
        self,
        scenarios: List[TestScenario],
        poms: List[GeneratedPOM],
        page_type: PageType,
        page_name: str
    ) -> str:
        """Generate test suite with all scenarios"""
        # Get POM class name
        pom_class = poms[0].class_name if poms else "Page"
        pom_var = pom_class[0].lower() + pom_class[1:]  # camelCase
        
        # Generate test cases
        test_cases = []
        for scenario in scenarios:
            test_case = self._generate_test_case(scenario, pom_class, pom_var)
            test_cases.append(test_case)
        
        test_cases_str = "\n\n".join(test_cases)
        
        return f"""test.describe('{page_name} Tests', () => {{
  let {pom_var}: {pom_class};

  test.beforeEach(async ({{ page }}) => {{
    {pom_var} = new {pom_class}(page);
    await {pom_var}.navigate();
  }});

{test_cases_str}
}});"""
    
    def _generate_test_case(
        self,
        scenario: TestScenario,
        pom_class: str,
        pom_var: str
    ) -> str:
        """Generate a single test case"""
        # Convert steps to test code
        test_steps = self._steps_to_code(scenario.steps, pom_var)
        
        # Add assertion based on expected outcome
        assertion = self._generate_assertion(scenario.expected_outcome, pom_var)
        
        # Combine steps and assertion
        test_body = "\n".join([f"    {step}" for step in test_steps])
        if assertion:
            test_body += f"\n    {assertion}"
        
        return f"""  test('{scenario.scenario_name}', async ({{ page }}) => {{
{test_body}
  }});"""
    
    def _steps_to_code(self, steps: List[str], pom_var: str) -> List[str]:
        """Convert test steps to executable code"""
        code_lines = []
        
        for step in steps:
            step_lower = step.lower()
            
            # Navigate steps
            if "navigate" in step_lower:
                # Already done in beforeEach
                continue
            
            # Fill/Enter steps
            elif "enter" in step_lower or "fill" in step_lower:
                if "username" in step_lower:
                    if "valid" in step_lower:
                        code_lines.append(f"await {pom_var}.usernameTextbox.fill('testuser');")
                    else:
                        code_lines.append(f"await {pom_var}.usernameTextbox.fill('invalid');")
                elif "password" in step_lower:
                    if "valid" in step_lower:
                        code_lines.append(f"await {pom_var}.passwordTextbox.fill('Test123!');")
                    else:
                        code_lines.append(f"await {pom_var}.passwordTextbox.fill('wrong');")
                elif "form" in step_lower or "fields" in step_lower:
                    code_lines.append(f"// TODO: Fill form fields")
            
            # Click steps
            elif "click" in step_lower:
                if "login" in step_lower or "submit" in step_lower or "button" in step_lower:
                    code_lines.append(f"await {pom_var}.loginButton.click();")
                else:
                    code_lines.append(f"// TODO: Click element")
            
            # Verify steps
            elif "verify" in step_lower or "check" in step_lower:
                # Will be handled by assertion
                continue
            
            # Leave empty steps
            elif "leave" in step_lower and "empty" in step_lower:
                # Don't fill fields
                continue
            
            else:
                # Generic step
                code_lines.append(f"// {step}")
        
        return code_lines
    
    def _generate_assertion(self, expected_outcome: str, pom_var: str) -> str:
        """Generate assertion based on expected outcome"""
        outcome_lower = expected_outcome.lower()
        
        # Redirect/navigation assertions
        if "redirect" in outcome_lower or "navigate" in outcome_lower:
            if "dashboard" in outcome_lower:
                return "await expect(page).toHaveURL(/dashboard/);"
            else:
                return "await expect(page).toHaveURL(/.*/);"
        
        # Error message assertions
        elif "error" in outcome_lower:
            return "await expect(page.locator('.error, [role=\"alert\"]')).toBeVisible();"
        
        # Validation assertions
        elif "validation" in outcome_lower:
            return "await expect(page.locator('.error, .invalid')).toBeVisible();"
        
        # Success assertions
        elif "success" in outcome_lower or "created" in outcome_lower:
            return "await expect(page.locator('.success, [role=\"status\"]')).toBeVisible();"
        
        # Cart/product assertions
        elif "cart" in outcome_lower:
            return "await expect(page.locator('.cart-count')).not.toHaveText('0');"
        
        # Visibility assertions
        elif "visible" in outcome_lower or "display" in outcome_lower:
            return "await expect(page.locator('main')).toBeVisible();"
        
        # Generic assertion
        else:
            return f"// TODO: Assert - {expected_outcome}"
    
    def _count_assertions(self, scenarios: List[TestScenario]) -> int:
        """Count total assertions in scenarios"""
        return len(scenarios)  # At least one assertion per scenario
    
    def _get_page_name(self, page_type: PageType) -> str:
        """Get readable page name from page type"""
        name_map = {
            PageType.AUTH_LOGIN: "login",
            PageType.AUTH_SIGNUP: "signup",
            PageType.AUTH_FORGOT_PASSWORD: "forgot-password",
            PageType.ECOMMERCE_PRODUCT: "product",
            PageType.ECOMMERCE_CART: "cart",
            PageType.ECOMMERCE_CHECKOUT: "checkout",
            PageType.SAAS_DASHBOARD: "dashboard",
            PageType.SAAS_SETTINGS: "settings",
            PageType.ADMIN_PANEL: "admin",
            PageType.CONTENT_ARTICLE: "article",
            PageType.CONTENT_LANDING: "landing",
            PageType.SEARCH_RESULTS: "search",
            PageType.USER_PROFILE: "profile",
        }
        return name_map.get(page_type, "page")


# Example usage
if __name__ == "__main__":
    from schemas import ElementRole, LocatorStrategy, LQSCategory, ElementLocator
    
    # Create sample POM
    pom = GeneratedPOM(
        url="https://example.com/login",
        page_type=PageType.AUTH_LOGIN,
        file_path="pages/LoginPage.ts",
        class_name="LoginPage",
        code="// POM code here",
        elements_used=3,
        methods_generated=3,
    )
    
    # Create sample test plan
    test_plan = TestPlan(
        url="https://example.com/login",
        page_type=PageType.AUTH_LOGIN,
        scenarios=[
            TestScenario(
                scenario_id="login_success",
                scenario_name="Successful Login",
                description="User can log in with valid credentials",
                steps=[
                    "Navigate to login page",
                    "Enter valid username",
                    "Enter valid password",
                    "Click login button",
                ],
                priority="high",
                expected_outcome="User is logged in and redirected to dashboard"
            ),
            TestScenario(
                scenario_id="login_invalid",
                scenario_name="Invalid Credentials",
                description="System rejects invalid credentials",
                steps=[
                    "Navigate to login page",
                    "Enter invalid username",
                    "Enter invalid password",
                    "Click login button",
                ],
                priority="high",
                expected_outcome="Error message shown"
            ),
        ],
        required_fixtures={}
    )
    
    # Generate tests
    generator = TestGeneratorAgent()
    tests = generator.generate_tests(test_plan, [pom])
    
    print(f"Generated {len(tests)} test file(s)")
    for test in tests:
        print(f"\nFile: {test.file_path}")
        print(f"Scenarios: {test.scenarios_covered}")
        print(f"Assertions: {test.assertions_count}")
        print("\nCode:")
        print("=" * 80)
        print(test.code)
