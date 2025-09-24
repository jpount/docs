# Business Logic Analyst Agent - README

## Overview
The Business Logic Analyst is a specialized agent that uses a **HYBRID approach** combining deterministic Python-based extraction with semantic LLM analysis to comprehensively identify and document business rules from codebases.

## What This Agent Does

### 1. Two-Phase Business Rule Extraction

#### Phase 1: Deterministic Extraction (Python-Based)
- **Runs**: `python3 framework/scripts/extract_business_rules.py`
- **Reads**: `output/context/business-rules-extracted.json`
- **Produces**: BR-00001 to BR-99999 rules
- **Characteristics**:
  - Consistent results every run
  - Pattern-based detection (BigDecimal calculations, state changes, validations)
  - Includes code snippets from actual implementation

#### Phase 2: LLM Semantic Analysis
- **Analyzes**: `output/reports/repomix-summary.md`
- **Produces**: BR-LLM-001 to BR-LLM-999 rules
- **Finds patterns Python can't detect**:
  - Business logic in comments (e.g., "// TODO: Reject orders over $1M")
  - Complex conditional flows across methods
  - Configuration-based rules
  - Domain-specific patterns requiring context understanding
  - Implicit rules in variable names

### 2. Documentation Generation

The agent creates three main documentation outputs:

#### A. Main Analysis Document (`output/docs/agent-business-logic-analyst.md`)
- Overview of business logic architecture
- Key business processes identified
- Summary of both deterministic and LLM-discovered rules

#### B. Business Rules Catalog (`output/docs/business-rules-catalog.md`)
**Structure:**
```markdown
# Business Rules Catalog

## Summary
- Deterministic Rules (Python): X rules
- Additional LLM-Discovered Rules: Y rules
- Total Business Rules: Z rules

## Part 1: Automated Extraction (Deterministic)
### BR-001: Rule Name
- Type: financial/state/validation/operation
- File: path/to/file.java:lineNumber [REF-XXXXX]
- Method: methodSignature
- Pattern: pattern_that_matched
- Code Implementation: [actual code snippet]
- LLM Analysis: [explanation of what the code does]
- Key Business Logic: [business implications]

## Part 2: Additional LLM-Identified Rules
### BR-LLM-001: Rule Name
- Type: [rule type]
- Confidence: high/medium/low
- Evidence Location: [file location] [REF-XXXXX]
- Code Context: [relevant code]
- LLM Analysis: [why this is a business rule]
- Business Impact: [implications]
- Reasoning: [why LLM identified this]
```

#### C. Context Summary (`output/context/business-logic-analyst-summary.json`)
- JSON format for other agents to consume
- Summary of findings
- Key patterns identified

### 3. Diagram Generation

The agent creates three types of diagrams with business rule annotations:

#### A. Domain Model (`output/diagrams/business-logic-domain.mmd`)
- Business entities and relationships
- Methods annotated with [BR-XXXXX] rules
- Class relationships

#### B. Process Flow (`output/diagrams/business-logic-process-flow.mmd`)
- Business process workflows
- Decision points labeled with BR-XXXXX rules
- State transitions

#### C. Sequence Diagrams (`output/diagrams/sequence-*.mmd`)
- Major business flow interactions
- Each step annotated with applicable BR-XXXXX rules
- Shows actual method calls with rule applications

**All diagrams include:**
```
%% Component Citations (MANDATORY)
%% ComponentName: REF-XXXXX
%% Business Rules Applied:
%% BR-XXXXX: Deterministic rule
%% BR-LLM-XXX: LLM-discovered rule
```

## How The Agent Works

### Step 1: Initialize Citation System
- Executes `.claude/includes/citation-manager-setup.md`
- Loads citation mappings for REF-XXXXX references

### Step 2: Load Deterministic Rules
```python
# Runs Python extraction
python3 framework/scripts/extract_business_rules.py

# Loads results
with open("output/context/business-rules-extracted.json", 'r') as f:
    deterministic_rules = json.load(f)
```

### Step 3: Analyze for Additional Rules
- Reads `output/reports/repomix-summary.md`
- Performs semantic analysis
- Identifies patterns Python regex cannot detect

### Step 4: Generate Documentation
- Creates comprehensive catalog with ALL rules (not truncated)
- Each rule includes:
  - Actual code snippet
  - LLM explanation of business logic
  - Business implications
  - Citations to source locations

### Step 5: Create Diagrams
- Generates visual representations
- Annotates with BR-XXXXX references
- Links diagrams to documented rules

### Step 6: Validation
- All Mermaid diagrams must pass syntax validation
- References `framework/templates/MERMAID_RULES.md`

## Key Features

### Business Rule Types Detected

1. **Financial/Calculations**
   - BigDecimal operations
   - Price/fee/tax calculations
   - Financial arithmetic

2. **Transaction Operations**
   - Buy/sell/trade operations
   - Order processing
   - Payment handling

3. **State Management**
   - Status changes
   - Workflow transitions
   - Lifecycle methods

4. **Validation Rules**
   - Input validation
   - Business constraints
   - Limit checks

5. **Business Operations**
   - CRUD operations
   - Authentication/authorization
   - Event handling

### What Makes This Agent Unique

1. **Hybrid Approach**: Combines deterministic and AI-powered detection
2. **Complete Documentation**: Every rule found is documented (no truncation)
3. **Clear Separation**: BR-XXXXX (deterministic) vs BR-LLM-XXX (AI-discovered)
4. **Confidence Levels**: LLM rules include confidence ratings
5. **Code-to-Documentation Traceability**: Every rule links back to source code
6. **Visual Representation**: Diagrams show rule applications in context

## Required Inputs

1. **Primary**: `output/reports/repomix-summary.md` (compressed codebase)
2. **Generated**: `output/context/business-rules-extracted.json` (from Python script)
3. **Citations**: `output/context/codebase-citations.json` (for REF-XXXXX lookups)

## Dependencies

### Templates (in `framework/templates/`)
- `CRITICAL_RULES.md` - Core validation rules
- `DATA_SOURCE_PRIORITY.md` - Data reading order
- `DIAGRAM_VALIDATION_RULES.md` - Component verification
- `MERMAID_RULES.md` - Diagram syntax validation
- `CITATION_RULES.md` - Citation format requirements

### Includes (in `.claude/includes/`)
- `citation-manager-setup.md` - Citation system initialization
- `citation-lookup-patterns.md` - Component lookup patterns

### Scripts (in `framework/scripts/`)
- `extract_business_rules.py` - Deterministic rule extraction
- `simple_mermaid_validator.py` - Diagram validation
- `citation_manager.py` - Citation management

## Success Criteria

The agent is successful when:
1. ✅ All deterministic rules (BR-XXXXX) are documented
2. ✅ Additional LLM rules (BR-LLM-XXX) include confidence and reasoning
3. ✅ Total rule count matches actual rules displayed
4. ✅ All diagrams include BR-XXXXX/BR-LLM-XXX annotations
5. ✅ All Mermaid diagrams validate without errors
6. ✅ Citations link all findings to source code
7. ✅ No fabricated or placeholder data

## Common Issues

1. **Missing Deterministic Rules**: Run `python3 framework/scripts/extract_business_rules.py` first
2. **Citation Errors**: Run `python3 framework/scripts/extract_citations.py` first
3. **Diagram Validation Failures**: Check `framework/templates/MERMAID_RULES.md`
4. **Truncated Output**: Ensure ALL rules are documented, not just examples

## Output Quality Indicators

- **Good**: "Found 67 deterministic rules + 23 LLM rules = 90 total rules documented"
- **Bad**: "Showing first 10 rules..." (truncation)
- **Good**: "BR-LLM-001: Confidence: Medium - Found in comment at line 234"
- **Bad**: "BR-LLM-001: General business rule" (no evidence)

## Testing the Agent

To verify the agent works correctly:
1. Check that `output/context/business-rules-extracted.json` exists
2. Verify rule counts match between summary and detailed listings
3. Confirm all BR-XXXXX rules have code snippets
4. Validate all diagrams with `python3 framework/scripts/simple_mermaid_validator.py output/diagrams/`
5. Check that BR-LLM-XXX rules have confidence levels and reasoning

---

*This agent is essential for modernization projects as it ensures no business logic is lost during system rewrites or migrations.*