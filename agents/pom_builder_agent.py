"""
POM Builder Agent

Generates Playwright Page Object Model classes from LQS-approved elements.
Follows best practices: DRY, reusability, semantic naming.
"""

from typing import List, Dict, Any
from pathlib import Path

from schemas import (
    LQSReport,
    PageContextOntology,
    ElementLocator,
    GeneratedPOM,
    LQSCategory,
    ElementRole,
    LocatorStrategy,
)


class POMBuilderAgent:
    """
    POM Builder Agent - Code generation specialist.
    
    Responsibilities:
    - Generate Playwright Page Object Model classes
    - Use only LQS-approved elements (BEST/GOOD)
    - Follow Playwright best practices
    - Create reusable, maintainable code
    - Generate TypeScript with proper typing
    """
    
    def __init__(self):
        """Initialize POM Builder Agent"""
        pass
    
    def build_pom(
        self,
        page_context: PageContextOntology,
        lqs_report: LQSReport,
    ) -> GeneratedPOM:
        """
        Build Page Object Model from analyzed page.
        
        Args:
            page_context: Page classification and context
            lqs_report: LQS report with approved elements
        
        Returns:
            GeneratedPOM with TypeScript code
        """
        # Use only approved elements (BEST/GOOD)
        approved_elements = lqs_report.approved_elements
        
        # Generate class name from URL
        class_name = self._generate_class_name(page_context.url)
        
        # Generate imports
        imports = self._generate_imports()
        
        # Generate class definition
        class_def = self._generate_class_definition(class_name)
        
        # Generate locator properties
        locators = self._generate_locators(approved_elements)
        
        # Generate action methods
        methods = self._generate_methods(approved_elements, page_context)
        
        # Combine into full code
        code = self._assemble_code(
            imports=imports,
            class_def=class_def,
            locators=locators,
            methods=methods,
            class_name=class_name
        )
        
        return GeneratedPOM(
            url=page_context.url,
            page_type=page_context.page_type,
            class_name=class_name,
            file_path=f"pages/{class_name}.ts",
            code=code,
            elements_used=len(approved_elements),
            methods_generated=len(methods),
        )
    
    def _generate_class_name(self, url: str) -> str:
        """Generate PascalCase class name from URL"""
        import re
        
        # Extract path or domain
        parts = url.split("//")[-1].split("/")
        
        # Use path if available, otherwise domain
        if len(parts) > 1 and parts[1]:
            name_part = parts[1]
        else:
            name_part = parts[0].split(".")[0]
        
        # Convert to PascalCase
        name = re.sub(r'[^a-zA-Z0-9]', ' ', name_part)
        name = ''.join(word.capitalize() for word in name.split())
        
        return f"{name}Page" if name else "HomePage"
    
    def _generate_imports(self) -> str:
        """Generate TypeScript imports"""
        return """import { Page, Locator } from '@playwright/test';"""
    
    def _generate_class_definition(self, class_name: str) -> str:
        """Generate class definition with constructor"""
        return f"""
export class {class_name} {{
  constructor(private page: Page) {{}}"""
    
    def _generate_locators(self, elements: List[ElementLocator]) -> List[str]:
        """Generate locator getter methods"""
        locators = []
        
        for element in elements:
            # Generate method name from element
            method_name = self._element_to_method_name(element)
            
            # Generate Playwright locator code
            locator_code = self._element_to_playwright_locator(element)
            
            # Create getter method
            locator = f"""
  get {method_name}(): Locator {{
    return {locator_code};
  }}"""
            locators.append(locator)
        
        return locators
    
    def _generate_methods(
        self,
        elements: List[ElementLocator],
        page_context: PageContextOntology
    ) -> List[str]:
        """Generate high-level action methods"""
        methods = []
        
        # Group elements by role
        buttons = [e for e in elements if e.semantic_role == ElementRole.BUTTON]
        textboxes = [e for e in elements if e.semantic_role == ElementRole.TEXTBOX]
        links = [e for e in elements if e.semantic_role == ElementRole.LINK]
        
        # Generate navigation method
        methods.append(self._generate_navigate_method(page_context.url))
        
        # Generate form fill method if we have inputs
        if textboxes:
            methods.append(self._generate_form_fill_method(textboxes, buttons))
        
        # Generate click methods for important buttons
        for button in buttons[:3]:  # Limit to top 3 buttons
            methods.append(self._generate_click_method(button))
        
        return methods
    
    def _generate_navigate_method(self, url: str) -> str:
        """Generate navigation method"""
        # Extract base path
        path = "/" + "/".join(url.split("//")[-1].split("/")[1:])
        if path == "/":
            path = "/"
        
        return f"""
  async navigate() {{
    await this.page.goto('{path}');
  }}"""
    
    def _generate_form_fill_method(
        self,
        textboxes: List[ElementLocator],
        buttons: List[ElementLocator]
    ) -> str:
        """Generate form filling method"""
        params = []
        fills = []
        
        for textbox in textboxes:
            param_name = self._element_to_param_name(textbox)
            method_name = self._element_to_method_name(textbox)
            
            params.append(f"{param_name}: string")
            fills.append(f"    await this.{method_name}.fill({param_name});")
        
        # Add submit if we have a button
        if buttons:
            submit_method = self._element_to_method_name(buttons[0])
            fills.append(f"    await this.{submit_method}.click();")
        
        params_str = ", ".join(params)
        fills_str = "\n".join(fills)
        
        return f"""
  async fillForm({params_str}) {{
{fills_str}
  }}"""
    
    def _generate_click_method(self, button: ElementLocator) -> str:
        """Generate click method for a button"""
        method_name = self._element_to_method_name(button)
        action_name = method_name.replace("Button", "").replace("Link", "")
        
        return f"""
  async click{action_name.capitalize()}() {{
    await this.{method_name}.click();
  }}"""
    
    def _element_to_method_name(self, element: ElementLocator) -> str:
        """Convert element to camelCase method name"""
        import re
        
        # Use label if available
        if element.user_facing_label:
            name = element.user_facing_label
        else:
            name = element.element_id
        
        # Clean and convert to camelCase
        name = re.sub(r'[^a-zA-Z0-9]', ' ', name)
        words = name.split()
        
        if not words:
            return f"{element.semantic_role.value.lower()}Element"
        
        # First word lowercase, rest capitalized
        camel = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        
        # Add role suffix if not already present
        role_suffix = element.semantic_role.value.lower()
        if role_suffix not in camel.lower():
            camel += role_suffix.capitalize()
        
        return camel
    
    def _element_to_param_name(self, element: ElementLocator) -> str:
        """Convert element to parameter name"""
        method_name = self._element_to_method_name(element)
        # Remove role suffix for cleaner param names
        for role in ["Button", "Textbox", "Link", "Checkbox"]:
            method_name = method_name.replace(role, "")
        return method_name or "value"
    
    def _element_to_playwright_locator(self, element: ElementLocator) -> str:
        """Convert ElementLocator to Playwright locator code"""
        strategy = element.locator_strategy
        value = element.locator_value
        
        if strategy == LocatorStrategy.GET_BY_ROLE:
            # Extract role and name if present
            if "name:" in value or "'" in value:
                return f"this.page.{value}"
            else:
                return f"this.page.getByRole('{value}')"
        
        elif strategy == LocatorStrategy.GET_BY_LABEL:
            return f"this.page.getByLabel('{value}')"
        
        elif strategy == LocatorStrategy.GET_BY_TEXT:
            return f"this.page.getByText('{value}')"
        
        elif strategy == LocatorStrategy.GET_BY_PLACEHOLDER:
            return f"this.page.getByPlaceholder('{value}')"
        
        elif strategy == LocatorStrategy.GET_BY_TEST_ID:
            return f"this.page.getByTestId('{value}')"
        
        elif strategy == LocatorStrategy.CSS_SELECTOR:
            return f"this.page.locator('{value}')"
        
        elif strategy == LocatorStrategy.XPATH:
            return f"this.page.locator('{value}')"
        
        else:
            return f"this.page.locator('{value}')"
    
    def _assemble_code(
        self,
        imports: str,
        class_def: str,
        locators: List[str],
        methods: List[str],
        class_name: str
    ) -> str:
        """Assemble complete POM code"""
        locators_str = "\n".join(locators)
        methods_str = "\n".join(methods)
        
        code = f"""{imports}

{class_def}
{locators_str}
{methods_str}
}}
"""
        return code


# Example usage
if __name__ == "__main__":
    from schemas import PageType
    from datetime import datetime
    
    # Create sample data
    page_context = PageContextOntology(
        url="https://example.com/login",
        page_type=PageType.AUTH_LOGIN,
        primary_purpose="Authenticate user credentials",
        confidence_score=0.95
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
                stability_rationale="Label-based locator",
                user_facing_label="Username",
            ),
            ElementLocator(
                element_id="password",
                semantic_role=ElementRole.TEXTBOX,
                locator_strategy=LocatorStrategy.GET_BY_LABEL,
                locator_value="Password",
                lqs_score=95,
                lqs_category=LQSCategory.BEST,
                stability_rationale="Label-based locator",
                user_facing_label="Password",
            ),
            ElementLocator(
                element_id="submit",
                semantic_role=ElementRole.BUTTON,
                locator_strategy=LocatorStrategy.GET_BY_ROLE,
                locator_value="button",
                lqs_score=95,
                lqs_category=LQSCategory.BEST,
                stability_rationale="Role-based locator",
                user_facing_label="Login",
            ),
        ],
        flagged_elements=[],
        rejected_elements=[],
        overall_quality_score=95.0,
        recommendations=[]
    )
    
    # Build POM
    builder = POMBuilderAgent()
    pom = builder.build_pom(page_context, lqs_report)
    
    print(f"Generated: {pom.file_path}")
    print(f"Class: {pom.class_name}")
    print(f"Elements: {pom.elements_used}")
    print(f"Methods: {pom.methods_generated}")
    print("\nCode:")
    print("=" * 80)
    print(pom.code)
