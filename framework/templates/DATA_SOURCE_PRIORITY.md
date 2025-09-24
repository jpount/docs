# 📊 Data Source Priority - ALL AGENTS

⚠️ **CRITICAL**: This pattern applies to ALL specialist agents (except repomix-analyzer which is the lightweight router).

## Standard Data Source Priority

**ALL agents MUST read data in this order:**

1. **PRIMARY**: `output/reports/repomix-summary.md` (compressed codebase)
2. **FALLBACK**: Raw codebase access (`codebase/`) if Repomix insufficient

**NO JSON summary dependencies** - read the source data directly.

## Implementation Pattern

```python
# Try Repomix summary first (PRIMARY source)
repomix_content = None
if Path("output/reports/repomix-summary.md").exists():
    repomix_content = Read("output/reports/repomix-summary.md")
    if len(repomix_content) > 1000:
        print("✅ Using Repomix summary")
        data_source = "repomix"
    else:
        print("⚠️ Repomix summary insufficient, using raw codebase")
        data_source = "raw"
else:
    print("⚠️ No Repomix summary found, using raw codebase")
    data_source = "raw"

# Extract information based on data source
if data_source == "repomix":
    extracted_data = extract_from_repomix(repomix_content)
else:
    extracted_data = extract_from_raw_codebase()
```

## Why This Pattern

### ✅ Benefits
- **80% token reduction** when Repomix available
- **No information loss** - specialists read source data directly
- **Parallel execution** - no JSON dependency chains
- **Robust fallback** - always works even without Repomix

### ❌ What NOT to do
- Read JSON summary files from other agents
- Create dependency chains between agents
- Assume other agents have run first
- Use complex multi-step data source hierarchies

## Agent Independence

Each agent should be **completely independent** and able to run in any order or in parallel. The only shared resource is:

1. **Repomix summary** (if available)
2. **Raw codebase** (always available)

## Agent Independence

Each agent operates independently without creating or reading context files. Agents only read from:
1. The Repomix summary (if available)
2. The raw codebase (as fallback)

---
**Applied to**: solution-architect, technical-architect, business-logic-analyst, performance-analyst, security-analyst, integration-specialist, ui-analyst