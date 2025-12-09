# Autonomous QA Modeler (AQM)

A multi-agent system for dynamic web application analysis and Playwright POM generation.

## Overview

The Autonomous QA Modeler ingests a target web application URL and autonomously generates a production-ready, Playwright-based test automation framework, complete with scalable Page Object Models (POMs) and a comprehensive test suite.

## Key Features

- **Semantic POM Generation**: Focus on user-centric intent and element roles for robust, maintainable locators
- **Parallel Analysis**: Minimize latency through concurrent agent execution
- **Self-Healing Tests**: Automatic locator repair and validation
- **Locator Quality Score (LQS)**: Enforce Playwright best practices for test stability
- **ADK Multi-Agent Architecture**: Hierarchical agent tree for controlled workflow
- **MCP Integration**: Secure browser and file system access

## Architecture

### Agent Hierarchy

```
Host Agent (Orchestrator)
├── Phase 1: Parallel Discovery
│   ├── Observer Agent (Browser MCP)
│   ├── DOM Analyzer Agent
│   └── Semantic Agent (LLM)
├── Phase 2: Sequential Modeling
│   ├── Element Classifier Agent (LQS)
│   ├── POM Builder Agent
│   └── Test Planner Agent
├── Phase 3: User Synthesis Gate
│   └── User Interaction Manager
└── Phase 4: Generation & Validation
    ├── Test Generator Agent
    ├── Code Review Agent
    └── Healer Agent (Loop)
```

### Workflow Phases

1. **Rapid Parallel Discovery**: Concurrent web analysis to minimize latency
2. **Sequential Modeling**: LQS validation and POM architecture
3. **Strategic Interaction Gate**: Contextual user query for required data
4. **Generation & Healing Loop**: Test creation and self-validation

## Project Structure

```
WEBANALYZER/
├── agents/              # All agent implementations
│   ├── host_agent.py
│   ├── parallel_discovery.py
│   ├── observer_agent.py
│   ├── dom_analyzer_agent.py
│   ├── semantic_agent.py
│   ├── element_classifier_agent.py
│   ├── pom_builder_agent.py
│   ├── test_planner_agent.py
│   ├── test_generator_agent.py
│   ├── code_review_agent.py
│   └── healer_agent.py
├── mcp/                 # MCP server configurations
│   ├── browser_server.py
│   └── filesystem_server.py
├── schemas/             # JSON schemas for inter-agent communication
│   └── schemas.py
├── core/                # Core utilities
│   ├── lqs_standard.py
│   ├── ckb.py
│   └── performance_monitor.py
├── templates/           # POM and test templates
│   └── pom_templates/
├── output/              # Generated Playwright frameworks
├── tests/               # Test suite
│   ├── agents/
│   ├── integration/
│   └── validation/
├── benchmarks/          # Performance benchmarks
└── docs/                # Documentation
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Playwright)
- Google ADK
- Antigravity environment

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright
npm install -D @playwright/test
npx playwright install
```

### Usage

```python
from agents.host_agent import HostAgent

# Initialize the AQM system
aqm = HostAgent()

# Generate test framework from URL
result = await aqm.analyze_and_generate(
    url="https://example.com",
    goal="Generate comprehensive test suite"
)

# Output will be in ./output/example-com/
```

## Development Roadmap

See [task.md](/.gemini/antigravity/brain/dd070dae-8572-4ad1-81fd-747880412f88/task.md) for detailed implementation tasks.

### Phase 1: Foundation (Weeks 1-4)
- Platform configuration
- MCP integration
- Host Agent development
- Data interface design

### Phase 2: Core Analysis (Weeks 5-8)
- ParallelAgent implementation
- Semantic prompt engineering
- LQS algorithm
- Performance validation

### Phase 3: Code Generation (Weeks 9-12)
- SequentialAgent pipeline
- POM templates
- User synthesis gate
- Test planning integration

### Phase 4: Validation (Weeks 13-16)
- Healer Agent integration
- Code review hardening
- Stress testing
- Launch readiness

## Success Metrics

| Metric | Target |
|--------|--------|
| Semantic Classification Accuracy | >85% |
| TTLX Reduction (Parallel vs Sequential) | >50% |
| Self-Healing Success Rate | >90% |
| Generated Test Stability | <5% flakiness |
| LQS-Approved Locators | >95% |

## Documentation

- [Implementation Plan](/.gemini/antigravity/brain/dd070dae-8572-4ad1-81fd-747880412f88/implementation_plan.md)
- [Task Breakdown](/.gemini/antigravity/brain/dd070dae-8572-4ad1-81fd-747880412f88/task.md)
- [Architecture Details](docs/architecture.md) _(coming soon)_
- [Agent Specifications](docs/agents.md) _(coming soon)_

## License

MIT
