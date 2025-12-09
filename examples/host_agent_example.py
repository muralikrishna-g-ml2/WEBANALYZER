"""
Integration Example: Using Host Agent to Analyze a URL

Demonstrates the end-to-end workflow of the AQM system.
"""

import asyncio
import json
from pathlib import Path

from agents.host_agent import HostAgent


async def main():
    """
    Example: Analyze a website and generate test framework
    """
    print("=" * 70)
    print("Autonomous QA Modeler - Integration Example")
    print("=" * 70)
    print()
    
    # Initialize Host Agent
    print("Initializing Host Agent...")
    host = HostAgent(
        output_dir=Path("./output"),
        session_storage_dir=Path("./output/sessions")
    )
    
    # Analyze and generate
    print("Analyzing URL: https://example.com")
    print("This will:")
    print("  1. Navigate to the URL and capture DOM")
    print("  2. Discover interactive elements")
    print("  3. Classify page type and purpose")
    print("  4. Generate quality scores for locators")
    print("  5. Create test plan and fixtures")
    print("  6. Generate Playwright POMs and tests")
    print()
    
    result = await host.analyze_and_generate(
        url="https://example.com",
        goal="Generate comprehensive test suite for example website"
    )
    
    # Display results
    print("=" * 70)
    print("Results")
    print("=" * 70)
    print()
    
    if result["status"] == "success":
        print(f"✅ Session ID: {result['session_id']}")
        print(f"✅ Output Directory: {result['output_directory']}")
        print()
        
        print("Session Summary:")
        summary = result["session_summary"]
        print(f"  - Current Phase: {summary['current_phase']}")
        print(f"  - Total Execution Time: {summary.get('total_execution_time', 0):.2f}s")
        print()
        
        print("Phase Timings:")
        for phase, duration in summary.get('phase_timings', {}).items():
            print(f"  - {phase}: {duration:.2f}s")
        print()
        
        print("Artifacts Generated:")
        artifacts = summary.get('artifacts', {})
        for artifact, exists in artifacts.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {artifact}")
        print()
        
        print("Performance Targets:")
        targets = result.get("performance_targets_met", {})
        for target, met in targets.items():
            status = "✅" if met else "❌"
            print(f"  {status} {target}")
        print()
        
        # Show generated files
        output_dir = Path(result['output_directory'])
        if output_dir.exists():
            print("Generated Files:")
            for file in output_dir.rglob("*"):
                if file.is_file():
                    rel_path = file.relative_to(output_dir)
                    size_kb = file.stat().st_size / 1024
                    print(f"  - {rel_path} ({size_kb:.1f} KB)")
        
    else:
        print(f"❌ Error: {result['error']}")
        print(f"   Type: {result['error_type']}")
    
    print()
    print("=" * 70)
    print("Example Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
