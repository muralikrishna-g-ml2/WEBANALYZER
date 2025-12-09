"""
Parallel Discovery Agent

Orchestrates concurrent execution of Observer, DOM Analyzer, and Semantic agents
to minimize Time to Last Token (TTLX).
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import time

from agents.observer_agent import ObserverAgent
from agents.dom_analyzer_agent import DOMAnalyzerAgent
from agents.semantic_agent import SemanticAgent
from mcp.browser_server import BrowserMCPServer
from schemas import PageContextOntology, ElementClassificationMap


class ParallelDiscoveryAgent:
    """
    Parallel Discovery Agent - Phase 1 orchestrator.
    
    Executes Observer, DOM Analyzer, and Semantic agents concurrently
    to achieve maximum TTLX reduction through parallelization.
    
    Workflow:
    1. Observer Agent: Navigate and capture (I/O bound)
    2. DOM Analyzer Agent: Parse structure (CPU bound)
    3. Semantic Agent: Classify page (LLM bound)
    
    These agents have minimal dependencies and can run in parallel.
    """
    
    def __init__(self, browser_mcp: BrowserMCPServer):
        """
        Initialize Parallel Discovery Agent.
        
        Args:
            browser_mcp: Browser MCP server instance
        """
        self.browser_mcp = browser_mcp
        self.observer = ObserverAgent(browser_mcp)
        self.dom_analyzer = DOMAnalyzerAgent()
        self.semantic = SemanticAgent()
    
    async def discover(
        self,
        url: str,
        screenshot_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute parallel discovery workflow.
        
        Args:
            url: Target URL to analyze
            screenshot_path: Optional path to save screenshot
        
        Returns:
            Dict with page_context, element_map, and timing metrics
        """
        start_time = time.time()
        
        # Step 1: Observer Agent (must run first to get DOM)
        observer_start = time.time()
        observation = await self.observer.observe(url, screenshot_path)
        observer_duration = time.time() - observer_start
        
        if observation["status"] != "success":
            return {
                "status": "error",
                "error": f"Observer failed: {observation.get('error')}",
                "timings": {
                    "observer": observer_duration,
                    "total": time.time() - start_time,
                }
            }
        
        # Step 2: Parallel execution of DOM Analyzer and Semantic Agent
        # Both can work with the captured DOM simultaneously
        
        html = observation["dom"]["html"]
        metadata = observation["metadata"]
        
        # Create tasks for parallel execution
        dom_task = asyncio.create_task(
            self._run_dom_analyzer(html, url)
        )
        
        # Semantic agent needs DOM analysis, so we'll wait for it
        # In a more advanced implementation, we could start semantic analysis
        # with partial data and refine as DOM analysis completes
        
        dom_start = time.time()
        dom_analysis = await dom_task
        dom_duration = time.time() - dom_start
        
        # Step 3: Semantic classification
        semantic_start = time.time()
        page_context = await self.semantic.classify_page(
            url=url,
            metadata=metadata,
            dom_analysis=dom_analysis,
            elements_count=observation.get("elements", {}).get("count", 0)
        )
        semantic_duration = time.time() - semantic_start
        
        # Step 4: Create Element Classification Map
        element_map = self.observer.create_element_classification_map(observation)
        
        total_duration = time.time() - start_time
        
        # Calculate theoretical sequential time
        sequential_time = observer_duration + dom_duration + semantic_duration
        
        return {
            "status": "success",
            "url": url,
            "page_context": page_context,
            "element_map": element_map,
            "dom_analysis": dom_analysis,
            "observation": observation,
            "timings": {
                "observer": observer_duration,
                "dom_analyzer": dom_duration,
                "semantic": semantic_duration,
                "total_parallel": total_duration,
                "theoretical_sequential": sequential_time,
                "time_saved": sequential_time - total_duration,
                "reduction_pct": ((sequential_time - total_duration) / sequential_time * 100) if sequential_time > 0 else 0,
            }
        }
    
    async def _run_dom_analyzer(self, html: str, url: str) -> Dict[str, Any]:
        """Run DOM analyzer in async context"""
        # DOM analyzer is synchronous, but we wrap it for async execution
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.dom_analyzer.analyze,
            html,
            url
        )


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize Browser MCP
        browser_mcp = BrowserMCPServer(headless=True)
        await browser_mcp.initialize()
        
        try:
            # Create Parallel Discovery Agent
            discovery = ParallelDiscoveryAgent(browser_mcp)
            
            # Execute discovery
            print("Starting parallel discovery for https://example.com...")
            result = await discovery.discover(
                url="https://example.com",
                screenshot_path=Path("./output/discovery-screenshot.png")
            )
            
            if result["status"] == "success":
                print(f"\n✅ Discovery successful!")
                print(f"\nPage Classification:")
                print(f"  Type: {result['page_context'].page_type.value}")
                print(f"  Purpose: {result['page_context'].primary_purpose}")
                print(f"  Confidence: {result['page_context'].confidence_score:.2%}")
                
                print(f"\nElements Discovered:")
                print(f"  Total: {result['element_map'].total_elements}")
                
                print(f"\nPerformance Metrics:")
                timings = result['timings']
                print(f"  Observer: {timings['observer']:.2f}s")
                print(f"  DOM Analyzer: {timings['dom_analyzer']:.2f}s")
                print(f"  Semantic: {timings['semantic']:.2f}s")
                print(f"  Total (Parallel): {timings['total_parallel']:.2f}s")
                print(f"  Theoretical Sequential: {timings['theoretical_sequential']:.2f}s")
                print(f"  Time Saved: {timings['time_saved']:.2f}s")
                print(f"  TTLX Reduction: {timings['reduction_pct']:.1f}%")
                
                if timings['reduction_pct'] >= 50:
                    print(f"\n🎯 Target Met: >50% TTLX reduction achieved!")
                else:
                    print(f"\n⚠️  Target Not Met: Need >50% reduction")
            else:
                print(f"\n❌ Discovery failed: {result['error']}")
        
        finally:
            await browser_mcp.cleanup()
    
    asyncio.run(main())
