"""
Example: Analyze AutomationExercise.com Login Page
"""
import asyncio
from pathlib import Path
from agents.host_agent import HostAgent


async def main():
    # Initialize the Host Agent
    print("🚀 Initializing Autonomous QA Modeler...")
    host = HostAgent(
        output_dir=Path("./output"),
        session_storage_dir=Path("./output/sessions")
    )
    
    # Analyze the login page
    print("\n📊 Analyzing Login Page...")
    print("URL: https://automationexercise.com/login")
    
    result = await host.analyze_and_generate(
        url="https://automationexercise.com/login",
        goal="Generate comprehensive login and signup test suite"
    )
    
    # Display results
    if result["status"] == "success":
        print("\n✅ Analysis Complete!")
        print(f"📁 Output Directory: {result['output_directory']}")
        print(f"🆔 Session ID: {result['session_id']}")
        
        # Show summary
        summary = result["session_summary"]
        print(f"\n⏱️  Total Time: {summary.get('total_execution_time', 0):.2f}s")
        print(f"📈 Current Phase: {summary['current_phase']}")
        
        # Show artifacts
        print("\n📦 Generated Artifacts:")
        artifacts = summary.get('artifacts', {})
        for artifact, exists in artifacts.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {artifact}")
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
