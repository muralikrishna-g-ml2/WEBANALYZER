"""
JSON Schemas for Inter-Agent Communication

Defines the structured data formats used for communication between agents
in the Autonomous QA Modeler system.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from enum import Enum


class LocatorStrategy(str, Enum):
    """Playwright locator strategies with quality tiers"""
    GET_BY_ROLE = "getByRole"
    GET_BY_LABEL = "getByLabel"
    GET_BY_TEST_ID = "getByTestId"
    GET_BY_TEXT = "getByText"
    GET_BY_PLACEHOLDER = "getByPlaceholder"
    CSS_SELECTOR = "css"
    XPATH = "xpath"


class LQSCategory(str, Enum):
    """Locator Quality Score categories"""
    BEST = "BEST"  # 90-100
    GOOD = "GOOD"  # 70-89
    OK = "OK"      # 30-69
    FAIL = "FAIL"  # 0-29


class ElementRole(str, Enum):
    """Semantic element roles based on ARIA standards"""
    BUTTON = "button"
    TEXTBOX = "textbox"
    COMBOBOX = "combobox"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    LINK = "link"
    HEADING = "heading"
    IMAGE = "img"
    LIST = "list"
    LISTITEM = "listitem"
    NAVIGATION = "navigation"
    MAIN = "main"
    FORM = "form"
    DIALOG = "dialog"
    ALERT = "alert"
    UNKNOWN = "unknown"


class PageType(str, Enum):
    """Common web application page types"""
    ECOMMERCE_PRODUCT = "E-commerce Product Page"
    ECOMMERCE_LISTING = "E-commerce Listing Page"
    ECOMMERCE_CART = "Shopping Cart"
    ECOMMERCE_CHECKOUT = "Checkout Page"
    SAAS_DASHBOARD = "SaaS Dashboard"
    SAAS_SETTINGS = "Settings Page"
    AUTH_LOGIN = "Login Page"
    AUTH_SIGNUP = "Signup Page"
    AUTH_FORGOT_PASSWORD = "Password Recovery"
    CONTENT_ARTICLE = "Article/Blog Post"
    CONTENT_LANDING = "Landing Page"
    SEARCH_RESULTS = "Search Results"
    USER_PROFILE = "User Profile"
    ADMIN_PANEL = "Admin Panel"
    UNKNOWN = "Unknown Page Type"


class ElementLocator(BaseModel):
    """Represents a single element locator with quality metrics"""
    element_id: str = Field(description="Unique identifier for this element")
    semantic_role: ElementRole = Field(description="ARIA-based semantic role")
    locator_strategy: LocatorStrategy = Field(description="Playwright locator method")
    locator_value: str = Field(description="The actual locator string")
    lqs_score: int = Field(ge=0, le=100, description="Locator Quality Score (0-100)")
    lqs_category: LQSCategory = Field(description="Quality category")
    stability_rationale: str = Field(description="Why this locator is/isn't stable")
    alternative_locators: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Backup locators if primary fails"
    )
    user_facing_label: Optional[str] = Field(
        default=None,
        description="Human-readable label for this element"
    )
    is_interactive: bool = Field(default=True, description="Whether element accepts user input")


class ComponentClassification(BaseModel):
    """Represents a reusable UI component"""
    component_type: str = Field(description="Type of component (e.g., 'LoginForm', 'Navigation')")
    elements: List[str] = Field(description="List of element_ids belonging to this component")
    is_reusable: bool = Field(description="Whether this should be abstracted in POM")
    page_location: str = Field(description="Where on page this component appears")


class PageContextOntology(BaseModel):
    """
    Semantic classification of the analyzed web page.
    Output of Phase 1 Parallel Discovery.
    """
    url: str = Field(description="Target URL analyzed")
    page_type: PageType = Field(description="Classified page type")
    primary_purpose: str = Field(description="Main user goal on this page")
    secondary_purposes: List[str] = Field(
        default_factory=list,
        description="Additional user goals"
    )
    identified_components: List[ComponentClassification] = Field(
        default_factory=list,
        description="Reusable UI components discovered"
    )
    navigation_paths: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Links and navigation targets"
    )
    requires_authentication: bool = Field(
        default=False,
        description="Whether page requires login"
    )
    dynamic_content: bool = Field(
        default=False,
        description="Whether page has significant dynamic/AJAX content"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in classification (0.0-1.0)"
    )


class ElementClassificationMap(BaseModel):
    """
    Comprehensive list of discovered interactive elements.
    Output of Phase 1 Parallel Discovery, input to Phase 2 Element Classifier.
    """
    url: str = Field(description="Target URL")
    total_elements: int = Field(description="Total interactive elements found")
    elements: List[ElementLocator] = Field(description="All discovered elements")
    timestamp: str = Field(description="When analysis was performed")


class LQSReport(BaseModel):
    """
    Locator Quality Score Report.
    Output of Phase 2 Element Classifier Agent.
    """
    url: str = Field(description="Target URL")
    total_elements_analyzed: int
    approved_elements: List[ElementLocator] = Field(
        description="Elements with LQS >= 70 (GOOD or BEST)"
    )
    flagged_elements: List[ElementLocator] = Field(
        description="Elements with LQS 30-69 (OK) - use with caution"
    )
    rejected_elements: List[ElementLocator] = Field(
        description="Elements with LQS < 30 (FAIL) - must be replaced"
    )
    overall_quality_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Average LQS across all elements"
    )
    recommendations: List[str] = Field(
        description="Specific recommendations for improving locator quality"
    )


class TestScenario(BaseModel):
    """Represents a single test scenario"""
    scenario_id: str
    scenario_name: str
    description: str
    preconditions: List[str] = Field(default_factory=list)
    steps: List[str]
    expected_outcome: str
    required_fixtures: List[str] = Field(
        default_factory=list,
        description="Test data needed (e.g., 'valid_username', 'valid_password')"
    )
    priority: Literal["high", "medium", "low"] = "medium"


class TestPlan(BaseModel):
    """
    Comprehensive test plan in structured format.
    Output of Phase 2 Test Planner Agent.
    """
    url: str
    page_type: PageType
    scenarios: List[TestScenario]
    required_fixtures: Dict[str, str] = Field(
        description="Map of fixture name to description of what data is needed"
    )
    execution_strategy: str = Field(
        default="parallel",
        description="How tests should be executed (parallel/sequential)"
    )


class UserInputFixtures(BaseModel):
    """
    Test data provided by user during Phase 3 interaction.
    Input to Phase 4 Test Generator Agent.
    """
    url: str
    confirmed_page_purpose: str = Field(
        description="User-confirmed primary purpose of the page"
    )
    fixture_data: Dict[str, str] = Field(
        description="Map of fixture name to actual test data value"
    )
    additional_scenarios: List[str] = Field(
        default_factory=list,
        description="Any additional test scenarios user wants to add"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Any constraints or special requirements"
    )


class GeneratedPOM(BaseModel):
    """Represents a generated Page Object Model file"""
    url: str
    page_type: PageType
    file_path: str
    class_name: str
    code: str
    elements_used: int = 0
    methods_generated: int = 0
    dependencies: List[str] = Field(default_factory=list)


class GeneratedTest(BaseModel):
    """Represents a generated test file"""
    url: str
    file_path: str
    test_name: str
    code: str
    dependencies: List[str] = Field(default_factory=list)
    scenarios_covered: List[str]
    assertions_count: int = 0


class CodeReviewResult(BaseModel):
    """Output of Code Review Agent"""
    passed: bool
    violations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of violations found (type, description, location)"
    )
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class HealerResult(BaseModel):
    """Output of Healer Agent execution"""
    test_file: str
    initial_failures: int
    healed_failures: int
    remaining_failures: int
    healing_iterations: int
    success_rate: float = Field(ge=0.0, le=1.0)
    updated_locators: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Locators that were updated"
    )


class AQMSessionState(BaseModel):
    """
    Centralized Knowledge Base state.
    Managed by Host Agent throughout workflow.
    """
    session_id: str
    url: str
    current_phase: Literal["P1", "P2", "P3", "P4", "COMPLETE"]
    
    # Phase 1 outputs
    page_context: Optional[PageContextOntology] = None
    element_map: Optional[ElementClassificationMap] = None
    
    # Phase 2 outputs
    lqs_report: Optional[LQSReport] = None
    test_plan: Optional[TestPlan] = None
    generated_poms: List[GeneratedPOM] = Field(default_factory=list)
    
    # Phase 3 outputs
    user_fixtures: Optional[UserInputFixtures] = None
    
    # Phase 4 outputs
    generated_tests: List[GeneratedTest] = Field(default_factory=list)
    code_review: Optional[CodeReviewResult] = None
    healer_results: List[HealerResult] = Field(default_factory=list)
    
    # Performance metrics
    phase_timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Execution time for each phase in seconds"
    )
    total_execution_time: Optional[float] = None
