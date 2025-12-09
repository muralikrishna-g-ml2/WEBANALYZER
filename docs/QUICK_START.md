# AQM System - Quick Start Guide

## Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- Git

### Setup

```bash
# Clone repository
cd /path/to/WEBANALYZER

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install Node dependencies (for running generated tests)
npm install
```

### Optional: LLM Enhancement

```bash
# Set Gemini API key for improved accuracy
export GEMINI_API_KEY="your-api-key-here"
```

---

## Basic Usage

### Analyze a Single Page

```python
from agents.host_agent import HostAgent
import asyncio

async def main():
    # Initialize Host Agent
    host = HostAgent()
    
    # Analyze URL and generate tests
    result = await host.analyze_and_generate(
        url="https://example.com/login",
        goal="Generate comprehensive login test suite"
    )
    
    print(f"✅ Session: {result['session_id']}")
    print(f"✅ Output: {result['output_directory']}")

asyncio.run(main())
```

### Command Line Usage

```bash
# Analyze a URL
python -m agents.host_agent https://example.com/login

# With custom output directory
python -m agents.host_agent https://example.com/login --output ./my-tests
```

---

## Generated Outputs

After analysis, you'll find:

```
output/example-com/
├── pages/
│   └── LoginPage.ts          # Page Object Model
├── tests/
│   └── login.critical.spec.ts # Executable tests
├── screenshots/
│   └── initial_capture.png    # Visual documentation
├── SESSION_REPORT.md          # Analysis summary
└── PERFORMANCE_REPORT.md      # Timing metrics
```

---

## Running Generated Tests

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/login.critical.spec.ts

# Run with UI
npx playwright test --ui

# Debug mode
npx playwright test --debug
```

---

## Configuration

### Custom Output Directory

```python
host = HostAgent(
    output_dir=Path("./custom-output"),
    session_storage_dir=Path("./sessions")
)
```

### Enable LLM Enhancement

```python
# Set environment variable
os.environ["GEMINI_API_KEY"] = "your-key"

# LLM will automatically be used for:
# - Page type classification
# - Element role identification
# - Improved semantic understanding
```

---

## Examples

### Example 1: Login Page

```python
result = await host.analyze_and_generate(
    url="https://app.example.com/login"
)

# Generates:
# - LoginPage.ts with username, password, submit methods
# - login.critical.spec.ts with success/failure scenarios
```

### Example 2: E-commerce Product

```python
result = await host.analyze_and_generate(
    url="https://shop.example.com/product/123"
)

# Generates:
# - ProductPage.ts with add-to-cart, quantity methods
# - product.critical.spec.ts with purchase scenarios
```

### Example 3: Dashboard

```python
result = await host.analyze_and_generate(
    url="https://app.example.com/dashboard"
)

# Generates:
# - DashboardPage.ts with widget interaction methods
# - dashboard.critical.spec.ts with loading scenarios
```

---

## Understanding Quality Scores

### LQS (Locator Quality Score)

| Score | Category | Meaning | Action |
|-------|----------|---------|--------|
| 95-100 | BEST | Production-ready | ✅ Use in POMs |
| 80-94 | GOOD | Acceptable | ✅ Use in POMs |
| 60-79 | OK | Needs review | ⚠️ Review alternatives |
| 0-59 | FAIL | Rejected | ❌ Exclude from POMs |

### Improving Quality Scores

**Add test IDs** (Best):
```html
<button data-testid="submit-button">Submit</button>
```

**Use ARIA labels** (Best):
```html
<input aria-label="Username" />
```

**Avoid dynamic IDs** (Bad):
```html
<div id="random-123456">...</div>
```

---

## Troubleshooting

### No Elements Discovered

**Problem**: Page has no interactive elements  
**Solution**: Check if page requires authentication or JavaScript

```python
# For authenticated pages
# 1. Login manually first
# 2. Save session state
# 3. Reuse session for analysis
```

### Low Quality Scores

**Problem**: Overall quality score < 60  
**Solution**: Improve HTML with semantic attributes

```html
<!-- Before (LQS: 40) -->
<div class="btn-123" onclick="submit()">Click</div>

<!-- After (LQS: 95) -->
<button data-testid="submit-btn" aria-label="Submit Form">Submit</button>
```

### Tests Failing

**Problem**: Generated tests fail on execution  
**Solution**: Update selectors or add wait strategies

```typescript
// Add explicit waits
await page.waitForLoadState('networkidle');
await expect(loginPage.usernameTextbox).toBeVisible();
```

---

## Best Practices

### 1. Use Semantic HTML

```html
✅ Good:
<button aria-label="Submit">Submit</button>
<input type="text" aria-label="Username" />

❌ Bad:
<div class="btn" onclick="submit()">Submit</div>
<input type="text" id="field-12345" />
```

### 2. Add Test IDs

```html
<button data-testid="login-submit">Login</button>
<input data-testid="username-input" />
```

### 3. Review Generated Code

- Check assertions match expected behavior
- Add custom validations as needed
- Refactor for your specific use cases

### 4. Maintain POMs

- Keep POMs in sync with UI changes
- Re-run analysis when pages change significantly
- Version control generated code

---

## Advanced Usage

### Batch Processing

```python
urls = [
    "https://example.com/login",
    "https://example.com/signup",
    "https://example.com/dashboard"
]

for url in urls:
    result = await host.analyze_and_generate(url)
    print(f"✅ Processed: {url}")
```

### Custom Test Scenarios

```python
# Extend generated test plan
test_plan = ckb.get_test_plan()
test_plan.scenarios.append(
    TestScenario(
        scenario_id="custom_flow",
        scenario_name="Custom User Flow",
        steps=["Step 1", "Step 2"],
        priority="high"
    )
)
```

### Integration with CI/CD

```yaml
# .github/workflows/generate-tests.yml
name: Generate Tests
on: [push]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Generate tests
        run: python -m agents.host_agent ${{ secrets.APP_URL }}
      - name: Commit generated code
        run: |
          git add pages/ tests/
          git commit -m "Auto-generated tests"
          git push
```

---

## Performance Tips

### 1. Use Headless Mode (Default)

```python
# Headless is faster
browser_mcp = BrowserMCPServer(headless=True)
```

### 2. Limit Screenshot Size

```python
# Smaller screenshots = faster
screenshot_result = await browser_mcp.capture_screenshot(
    full_page=False  # Only viewport
)
```

### 3. Parallel Analysis

```python
# Analyze multiple pages concurrently
import asyncio

async def analyze_all(urls):
    tasks = [host.analyze_and_generate(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Support & Resources

- **Documentation**: `/docs/`
- **Architecture**: `/docs/architecture.md`
- **Examples**: `/examples/`
- **Tests**: `/tests/`

---

## Next Steps

1. ✅ Run your first analysis
2. ✅ Review generated POMs
3. ✅ Execute generated tests
4. ✅ Customize for your needs
5. ✅ Integrate into CI/CD

**Happy Testing!** 🎉
