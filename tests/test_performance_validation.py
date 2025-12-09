"""
Performance Validation Tests for Parallel Discovery

Tests TTLX reduction against real-world websites to validate
the >50% reduction target.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from agents.parallel_discovery import ParallelDiscoveryAgent
from mcp.browser_server import BrowserMCPServer


class PerformanceValidator:
    """
    Validates parallel discovery performance against real-world sites.
    """
    
    # Test URLs representing different page types and complexities
    TEST_URLS = [
        {
            "url": "https://example.com",
            "name": "Simple Static Page",
            "expected_complexity": "LOW",
        },
        {
            "url": "https://github.com",
            "name": "GitHub Homepage",
            "expected_complexity": "HIGH",
        },
        {
            "url": "https://news.ycombinator.com",
            "name": "Hacker News",
            "expected_complexity": "MEDIUM",
        },
        {
            "url": "https://www.wikipedia.org",
            "name": "Wikipedia Portal",
            "expected_complexity": "MEDIUM",
        },
    ]
    
    def __init__(self, output_dir: Path):
        """
        Initialize Performance Validator.
        
        Args:
            output_dir: Directory to save test results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []
    
    async def run_validation(self):
        """
        Run performance validation against all test URLs.
        """
        print("=" * 80)
        print("Performance Validation - TTLX Reduction Testing")
        print("=" * 80)
        print()
        
        # Initialize Browser MCP
        browser_mcp = BrowserMCPServer(headless=True)
        await browser_mcp.initialize()
        
        try:
            discovery = ParallelDiscoveryAgent(browser_mcp)
            
            for test_case in self.TEST_URLS:
                print(f"Testing: {test_case['name']}")
                print(f"URL: {test_case['url']}")
                print("-" * 80)
                
                try:
                    # Create output directory for this test
                    test_output = self.output_dir / test_case['name'].replace(" ", "_").lower()
                    test_output.mkdir(parents=True, exist_ok=True)
                    
                    # Run discovery
                    result = await discovery.discover(
                        url=test_case['url'],
                        screenshot_path=test_output / "screenshot.png"
                    )
                    
                    if result["status"] == "success":
                        # Extract metrics
                        timings = result["timings"]
                        page_context = result["page_context"]
                        element_map = result["element_map"]
                        dom_analysis = result["dom_analysis"]
                        
                        test_result = {
                            "name": test_case['name'],
                            "url": test_case['url'],
                            "status": "success",
                            "page_type": page_context.page_type.value,
                            "confidence": page_context.confidence_score,
                            "elements_discovered": element_map.total_elements,
                            "complexity": dom_analysis.get("complexity", {}).get("complexity_score", "UNKNOWN"),
                            "timings": timings,
                            "ttlx_reduction_pct": timings["reduction_pct"],
                            "target_met": timings["reduction_pct"] >= 50.0,
                        }
                        
                        self.results.append(test_result)
                        
                        # Print results
                        print(f"✅ Status: Success")
                        print(f"   Page Type: {test_result['page_type']}")
                        print(f"   Confidence: {test_result['confidence']:.1%}")
                        print(f"   Elements: {test_result['elements_discovered']}")
                        print(f"   Complexity: {test_result['complexity']}")
                        print(f"   Observer: {timings['observer']:.2f}s")
                        print(f"   DOM Analyzer: {timings['dom_analyzer']:.2f}s")
                        print(f"   Semantic: {timings['semantic']:.2f}s")
                        print(f"   Total (Parallel): {timings['total_parallel']:.2f}s")
                        print(f"   Theoretical Sequential: {timings['theoretical_sequential']:.2f}s")
                        print(f"   TTLX Reduction: {timings['reduction_pct']:.1f}%")
                        
                        if test_result['target_met']:
                            print(f"   🎯 Target Met: >50% reduction achieved!")
                        else:
                            print(f"   ⚠️  Target Not Met: Need >50% reduction")
                    else:
                        test_result = {
                            "name": test_case['name'],
                            "url": test_case['url'],
                            "status": "error",
                            "error": result.get("error"),
                            "target_met": False,
                        }
                        self.results.append(test_result)
                        print(f"❌ Error: {result.get('error')}")
                
                except Exception as e:
                    test_result = {
                        "name": test_case['name'],
                        "url": test_case['url'],
                        "status": "error",
                        "error": str(e),
                        "target_met": False,
                    }
                    self.results.append(test_result)
                    print(f"❌ Exception: {str(e)}")
                
                print()
        
        finally:
            await browser_mcp.cleanup()
        
        # Generate summary
        self._print_summary()
        self._save_results()
    
    def _print_summary(self):
        """Print validation summary"""
        print("=" * 80)
        print("Validation Summary")
        print("=" * 80)
        print()
        
        successful = [r for r in self.results if r["status"] == "success"]
        targets_met = [r for r in successful if r["target_met"]]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(self.results) - len(successful)}")
        print(f"Targets Met (>50% TTLX reduction): {len(targets_met)}/{len(successful)}")
        print()
        
        if successful:
            avg_reduction = sum(r["ttlx_reduction_pct"] for r in successful) / len(successful)
            print(f"Average TTLX Reduction: {avg_reduction:.1f}%")
            print()
            
            print("Results by Page:")
            print("-" * 80)
            for result in successful:
                status = "✅" if result["target_met"] else "⚠️"
                print(f"{status} {result['name']}: {result['ttlx_reduction_pct']:.1f}% reduction")
                print(f"   Elements: {result['elements_discovered']}, Complexity: {result['complexity']}")
            print()
        
        # Overall assessment
        if len(targets_met) >= len(successful) * 0.5:
            print("🎯 OVERALL: Performance targets validated!")
        else:
            print("⚠️  OVERALL: Performance targets need improvement")
            print("   Note: Simple pages may not show significant parallel benefits")
    
    def _save_results(self):
        """Save results to JSON file"""
        results_file = self.output_dir / "validation_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "results": self.results,
                "summary": {
                    "total_tests": len(self.results),
                    "successful": len([r for r in self.results if r["status"] == "success"]),
                    "targets_met": len([r for r in self.results if r.get("target_met", False)]),
                }
            }, f, indent=2)
        
        print(f"Results saved to: {results_file}")


async def main():
    """Run performance validation"""
    validator = PerformanceValidator(
        output_dir=Path("./output/performance_validation")
    )
    
    await validator.run_validation()


if __name__ == "__main__":
    asyncio.run(main())
