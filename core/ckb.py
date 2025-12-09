"""
Centralized Knowledge Base (CKB)

Manages session state and artifacts throughout the AQM workflow.
Provides centralized storage and retrieval for inter-agent communication.
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from schemas.schemas import (
    AQMSessionState,
    PageContextOntology,
    ElementClassificationMap,
    LQSReport,
    TestPlan,
    UserInputFixtures,
    GeneratedPOM,
    GeneratedTest,
    CodeReviewResult,
    HealerResult,
)


class CentralizedKnowledgeBase:
    """
    Manages the centralized state for an AQM session.
    
    Provides methods for storing and retrieving artifacts between
    workflow phases, with automatic persistence and timing tracking.
    """
    
    def __init__(self, session_id: str, url: str, storage_dir: Optional[Path] = None):
        """
        Initialize a new CKB session.
        
        Args:
            session_id: Unique identifier for this session
            url: Target URL being analyzed
            storage_dir: Optional directory for persisting state
        """
        self.session_id = session_id
        self.url = url
        self.storage_dir = storage_dir or Path("./output/sessions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.state = AQMSessionState(
            session_id=session_id,
            url=url,
            current_phase="P1"
        )
        
        # Phase timing
        self._phase_start_times: Dict[str, float] = {}
        self._start_phase_timer("P1")
    
    def _start_phase_timer(self, phase: str):
        """Start timing for a phase"""
        self._phase_start_times[phase] = time.time()
    
    def _end_phase_timer(self, phase: str):
        """End timing for a phase and record duration"""
        if phase in self._phase_start_times:
            duration = time.time() - self._phase_start_times[phase]
            self.state.phase_timings[phase] = duration
            return duration
        return 0.0
    
    def advance_phase(self, next_phase: str):
        """
        Advance to the next workflow phase.
        
        Args:
            next_phase: The phase to advance to (P1, P2, P3, P4, COMPLETE)
        """
        # End current phase timer
        self._end_phase_timer(self.state.current_phase)
        
        # Advance
        self.state.current_phase = next_phase
        
        # Start new phase timer (unless complete)
        if next_phase != "COMPLETE":
            self._start_phase_timer(next_phase)
        else:
            # Calculate total execution time
            self.state.total_execution_time = sum(self.state.phase_timings.values())
        
        # Persist
        self.save()
    
    # Phase 1 artifacts
    def set_page_context(self, context: PageContextOntology):
        """Store Page Context Ontology from Phase 1"""
        self.state.page_context = context
        self.save()
    
    def get_page_context(self) -> Optional[PageContextOntology]:
        """Retrieve Page Context Ontology"""
        return self.state.page_context
    
    def set_element_map(self, element_map: ElementClassificationMap):
        """Store Element Classification Map from Phase 1"""
        self.state.element_map = element_map
        self.save()
    
    def get_element_map(self) -> Optional[ElementClassificationMap]:
        """Retrieve Element Classification Map"""
        return self.state.element_map
    
    # Phase 2 artifacts
    def set_lqs_report(self, report: LQSReport):
        """Store LQS Report from Phase 2"""
        self.state.lqs_report = report
        self.save()
    
    def get_lqs_report(self) -> Optional[LQSReport]:
        """Retrieve LQS Report"""
        return self.state.lqs_report
    
    def set_test_plan(self, plan: TestPlan):
        """Store Test Plan from Phase 2"""
        self.state.test_plan = plan
        self.save()
    
    def get_test_plan(self) -> Optional[TestPlan]:
        """Retrieve Test Plan"""
        return self.state.test_plan
    
    def add_generated_pom(self, pom: GeneratedPOM):
        """Add a generated POM to the collection"""
        self.state.generated_poms.append(pom)
        self.save()
    
    def get_generated_poms(self) -> list[GeneratedPOM]:
        """Retrieve all generated POMs"""
        return self.state.generated_poms
    
    # Phase 3 artifacts
    def set_user_fixtures(self, fixtures: UserInputFixtures):
        """Store User Input Fixtures from Phase 3"""
        self.state.user_fixtures = fixtures
        self.save()
    
    def get_user_fixtures(self) -> Optional[UserInputFixtures]:
        """Retrieve User Input Fixtures"""
        return self.state.user_fixtures
    
    # Phase 4 artifacts
    def add_generated_test(self, test: GeneratedTest):
        """Add a generated test to the collection"""
        self.state.generated_tests.append(test)
        self.save()
    
    def get_generated_tests(self) -> list[GeneratedTest]:
        """Retrieve all generated tests"""
        return self.state.generated_tests
    
    def set_code_review(self, review: CodeReviewResult):
        """Store Code Review result"""
        self.state.code_review = review
        self.save()
    
    def get_code_review(self) -> Optional[CodeReviewResult]:
        """Retrieve Code Review result"""
        return self.state.code_review
    
    def add_healer_result(self, result: HealerResult):
        """Add a Healer execution result"""
        self.state.healer_results.append(result)
        self.save()
    
    def get_healer_results(self) -> list[HealerResult]:
        """Retrieve all Healer results"""
        return self.state.healer_results
    
    # Persistence
    def save(self):
        """Persist current state to disk"""
        state_file = self.storage_dir / f"{self.session_id}.json"
        with open(state_file, 'w') as f:
            json.dump(self.state.model_dump(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, session_id: str, storage_dir: Optional[Path] = None) -> 'CentralizedKnowledgeBase':
        """
        Load an existing session from disk.
        
        Args:
            session_id: Session ID to load
            storage_dir: Directory where session is stored
            
        Returns:
            Loaded CKB instance
        """
        storage_dir = storage_dir or Path("./output/sessions")
        state_file = storage_dir / f"{session_id}.json"
        
        if not state_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        ckb = cls(
            session_id=state_data['session_id'],
            url=state_data['url'],
            storage_dir=storage_dir
        )
        ckb.state = AQMSessionState(**state_data)
        
        return ckb
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session state.
        
        Returns:
            Dictionary with key metrics and status
        """
        return {
            "session_id": self.session_id,
            "url": self.url,
            "current_phase": self.state.current_phase,
            "phase_timings": self.state.phase_timings,
            "total_execution_time": self.state.total_execution_time,
            "artifacts": {
                "page_context": self.state.page_context is not None,
                "element_map": self.state.element_map is not None,
                "lqs_report": self.state.lqs_report is not None,
                "test_plan": self.state.test_plan is not None,
                "user_fixtures": self.state.user_fixtures is not None,
                "generated_poms": len(self.state.generated_poms),
                "generated_tests": len(self.state.generated_tests),
                "code_review": self.state.code_review is not None,
                "healer_results": len(self.state.healer_results),
            }
        }
    
    def export_report(self) -> str:
        """
        Export a human-readable report of the session.
        
        Returns:
            Markdown-formatted report
        """
        report = f"""# AQM Session Report

**Session ID**: {self.session_id}
**Target URL**: {self.url}
**Current Phase**: {self.state.current_phase}
**Total Execution Time**: {self.state.total_execution_time:.2f}s

## Phase Timings

"""
        for phase, duration in self.state.phase_timings.items():
            report += f"- **{phase}**: {duration:.2f}s\n"
        
        if self.state.page_context:
            report += f"""
## Page Analysis

- **Page Type**: {self.state.page_context.page_type.value}
- **Primary Purpose**: {self.state.page_context.primary_purpose}
- **Requires Authentication**: {self.state.page_context.requires_authentication}
- **Dynamic Content**: {self.state.page_context.dynamic_content}
- **Confidence Score**: {self.state.page_context.confidence_score:.2%}
"""
        
        if self.state.lqs_report:
            report += f"""
## Locator Quality Analysis

- **Total Elements Analyzed**: {self.state.lqs_report.total_elements_analyzed}
- **Approved Elements**: {len(self.state.lqs_report.approved_elements)}
- **Flagged Elements**: {len(self.state.lqs_report.flagged_elements)}
- **Rejected Elements**: {len(self.state.lqs_report.rejected_elements)}
- **Overall Quality Score**: {self.state.lqs_report.overall_quality_score:.1f}/100

### Recommendations
"""
            for rec in self.state.lqs_report.recommendations:
                report += f"- {rec}\n"
        
        if self.state.generated_poms:
            report += f"""
## Generated Artifacts

- **Page Object Models**: {len(self.state.generated_poms)}
- **Test Files**: {len(self.state.generated_tests)}
"""
        
        if self.state.healer_results:
            total_healed = sum(r.healed_failures for r in self.state.healer_results)
            total_remaining = sum(r.remaining_failures for r in self.state.healer_results)
            avg_success = sum(r.success_rate for r in self.state.healer_results) / len(self.state.healer_results)
            
            report += f"""
## Self-Healing Results

- **Total Failures Healed**: {total_healed}
- **Remaining Failures**: {total_remaining}
- **Average Success Rate**: {avg_success:.1%}
"""
        
        return report
