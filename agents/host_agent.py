"""
Host Agent - Orchestrator for the AQM System

Manages the entire workflow across all four phases, delegates to
specialized agents, and maintains session state via the CKB.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from core import CentralizedKnowledgeBase, PerformanceMonitor
from schemas import (
    PageContextOntology,
    ElementClassificationMap,
    LQSReport,
    TestPlan,
    UserInputFixtures,
    AQMSessionState,
)
from mcp.browser_server import BrowserMCPServer
from mcp.filesystem_server import FileSystemMCPServer


class HostAgent:
    """
    Host Agent - Root orchestrator for the AQM system.
    
    Responsibilities:
    - Session state management via CKB
    - Workflow delegation to ParallelAgent and SequentialAgent
    - Phase transitions and timing
    - User interaction synthesis
    - Final framework export
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        session_storage_dir: Optional[Path] = None
    ):
        """
        Initialize Host Agent.
        
        Args:
            output_dir: Directory for generated frameworks
            session_storage_dir: Directory for session persistence
        """
        self.output_dir = output_dir or Path("./output")
        self.session_storage_dir = session_storage_dir or Path("./output/sessions")
        
        # Will be initialized per session
        self.ckb: Optional[CentralizedKnowledgeBase] = None
        self.performance: Optional[PerformanceMonitor] = None
        self.browser_mcp: Optional[BrowserMCPServer] = None
        self.fs_mcp: Optional[FileSystemMCPServer] = None
    
    async def analyze_and_generate(
        self,
        url: str,
        goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Analyze URL and generate Playwright framework.
        
        Args:
            url: Target web application URL
            goal: Optional user-specified goal/purpose
        
        Returns:
            Dict with session results and generated framework location
        """
        # Initialize session
        session_id = self._generate_session_id()
        self.ckb = CentralizedKnowledgeBase(
            session_id=session_id,
            url=url,
            storage_dir=self.session_storage_dir
        )
        self.performance = PerformanceMonitor(session_id=session_id)
        
        # Initialize MCP servers
        project_output_dir = self.output_dir / self._url_to_dirname(url)
        self.browser_mcp = BrowserMCPServer()
        self.fs_mcp = FileSystemMCPServer(
            base_dir=project_output_dir,
            allowed_extensions=['.ts', '.js', '.json', '.md']
        )
        
        try:
            # Phase 1: Parallel Discovery
            await self._execute_phase_1(url)
            
            # Phase 2: Sequential Modeling
            await self._execute_phase_2()
            
            # Phase 3: User Synthesis Gate
            user_fixtures = await self._execute_phase_3(goal)
            
            # Phase 4: Generation & Validation
            await self._execute_phase_4(user_fixtures)
            
            # Mark complete
            self.ckb.advance_phase("COMPLETE")
            
            # Generate reports
            session_report = self.ckb.export_report()
            performance_report = self.performance.export_report()
            
            # Save reports
            self.fs_mcp.write_file("SESSION_REPORT.md", session_report, overwrite=True)
            self.fs_mcp.write_file("PERFORMANCE_REPORT.md", performance_report, overwrite=True)
            
            return {
                "status": "success",
                "session_id": session_id,
                "url": url,
                "output_directory": str(project_output_dir),
                "session_summary": self.ckb.get_summary(),
                "performance_targets_met": self.performance.check_performance_targets(),
            }
        
        except Exception as e:
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__,
            }
        
        finally:
            # Cleanup
            if self.browser_mcp:
                await self.browser_mcp.cleanup()
    
    async def _execute_phase_1(self, url: str):
        """
        Phase 1: Parallel Discovery
        
        Executes Observer, DOM Analyzer, and Semantic agents concurrently
        to minimize TTLX.
        """
        from agents.parallel_discovery import ParallelDiscoveryAgent
        
        self.performance.start_phase("P1", parallel=True)
        
        # Create ParallelDiscoveryAgent
        discovery = ParallelDiscoveryAgent(self.browser_mcp)
        
        # Create screenshot path
        project_output_dir = self.output_dir / self._url_to_dirname(url)
        screenshot_path = project_output_dir / "screenshots" / "initial_capture.png"
        
        # Execute parallel discovery
        discovery_result = await discovery.discover(url, screenshot_path)
        
        if discovery_result["status"] != "success":
            raise Exception(f"Discovery failed: {discovery_result.get('error')}")
        
        # Extract results
        page_context = discovery_result["page_context"]
        element_map = discovery_result["element_map"]
        
        # Record agent timings
        timings = discovery_result["timings"]
        self.performance.record_agent_timing("Observer", timings["observer"])
        self.performance.record_agent_timing("DOM_Analyzer", timings["dom_analyzer"])
        self.performance.record_agent_timing("Semantic", timings["semantic"])
        
        # Store in CKB
        self.ckb.set_page_context(page_context)
        self.ckb.set_element_map(element_map)
        
        self.performance.end_phase()
        self.ckb.advance_phase("P2")
    
    async def _execute_phase_2(self):
        """
        Phase 2: Sequential Modeling
        
        Executes Element Classifier, POM Builder, and Test Planner
        in sequence with quality gates.
        """
        from agents.element_classifier_agent import ElementClassifierAgent
        from agents.pom_builder_agent import POMBuilderAgent
        from agents.test_planner_agent import TestPlannerAgent
        
        self.performance.start_phase("P2", parallel=False)
        
        # Step 1: Element Classifier - Apply LQS scoring
        element_map = self.ckb.get_element_map()
        
        if element_map and element_map.total_elements > 0:
            classifier = ElementClassifierAgent()
            lqs_report = classifier.classify_elements(element_map)
            self.ckb.set_lqs_report(lqs_report)
        else:
            # No elements to classify
            from schemas import LQSReport
            lqs_report = LQSReport(
                url=self.ckb.url,
                total_elements_analyzed=0,
                approved_elements=[],
                flagged_elements=[],
                rejected_elements=[],
                overall_quality_score=0.0,
                recommendations=["No interactive elements discovered"]
            )
            self.ckb.set_lqs_report(lqs_report)
        
        # Step 2: POM Builder - Generate Page Object Model
        page_context = self.ckb.get_page_context()
        
        if lqs_report.approved_elements:
            pom_builder = POMBuilderAgent()
            generated_pom = pom_builder.build_pom(page_context, lqs_report)
            
            # Save POM to file system
            self.fs_mcp.write_file(
                generated_pom.file_path,
                generated_pom.code,
                overwrite=True
            )
            
            # Store in CKB (store as list for consistency)
            self.ckb.state.generated_poms = [generated_pom]
        
        # Step 3: Test Planner - Generate test scenarios
        test_planner = TestPlannerAgent()
        test_plan = test_planner.plan_tests(page_context, lqs_report)
        
        self.ckb.set_test_plan(test_plan)
        
        self.performance.end_phase()
        self.ckb.advance_phase("P3")
    
    async def _execute_phase_3(self, goal: Optional[str]) -> UserInputFixtures:
        """
        Phase 3: User Synthesis Gate
        
        Synthesizes findings and requests user input for fixtures.
        """
        self.performance.start_phase("P3", parallel=False)
        
        # TODO: Implement User Synthesis logic
        # For now, return placeholder fixtures
        
        user_fixtures = UserInputFixtures(
            url=self.ckb.url,
            confirmed_page_purpose=goal or "User goal not specified",
            fixture_data={},
            additional_scenarios=[],
            constraints=[]
        )
        
        self.ckb.set_user_fixtures(user_fixtures)
        
        self.performance.end_phase()
        self.ckb.advance_phase("P4")
        
        return user_fixtures
    
    async def _execute_phase_4(self, user_fixtures: UserInputFixtures):
        """
        Phase 4: Generation & Validation
        
        Generates tests, reviews code, and executes self-healing loop.
        """
        from agents.test_generator_agent import TestGeneratorAgent
        
        self.performance.start_phase("P4", parallel=False)
        
        # Step 1: Test Generator - Create executable tests
        test_plan = self.ckb.get_test_plan()
        generated_poms = self.ckb.state.generated_poms or []
        
        if generated_poms and test_plan and test_plan.scenarios:
            test_generator = TestGeneratorAgent()
            generated_tests = test_generator.generate_tests(test_plan, generated_poms)
            
            # Save tests to file system
            for test in generated_tests:
                self.fs_mcp.write_file(
                    test.file_path,
                    test.code,
                    overwrite=True
                )
            
            # Store in CKB
            self.ckb.state.generated_tests = generated_tests
        
        # Step 2: Code Review (TODO - placeholder)
        # Step 3: Healer Agent (TODO - placeholder)
        
        self.performance.end_phase()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"aqm-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    def _url_to_dirname(self, url: str) -> str:
        """Convert URL to safe directory name"""
        import re
        # Extract domain
        domain = url.split("//")[-1].split("/")[0]
        # Remove special characters
        safe_name = re.sub(r'[^\w\-]', '-', domain)
        return safe_name


# Example usage
if __name__ == "__main__":
    async def main():
        host = HostAgent()
        
        result = await host.analyze_and_generate(
            url="https://example.com",
            goal="Generate comprehensive test suite for example website"
        )
        
        import json
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
