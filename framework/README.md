# Framework Documentation

## Overview
This framework provides tools for analyzing and documenting codebases, specifically designed for the DayTrader application analysis. It includes citation management, business rule extraction, diagram validation, and comprehensive testing utilities.

## Directory Structure

```
framework/
├── scripts/           # Core functionality scripts
├── templates/         # Documentation and validation templates
├── tests/            # Test suites for all components
├── document-viewer.html  # HTML viewer for documentation
└── run_tests.py      # Test runner with colored output
```

## Scripts Directory

### Core Parser
- **`repomix_parser.py`** ✅ **ACTIVELY USED**
  - Parses repomix-summary.md files to extract code components
  - Extracts classes, methods, interfaces, configurations, API endpoints
  - Used by: `extract_citations.py`, `extract_business_rules.py`
  - Foundation for all code analysis

### Citation Management
- **`extract_citations.py`** ✅ **ACTIVELY USED**
  - Extracts all code components from repomix and assigns REF-XXXXX IDs
  - Creates `output/context/codebase-citations.json`
  - Must be run first before agents can use citations
  - Usage: `python framework/scripts/extract_citations.py`

- **`citation_manager.py`** ✅ **ACTIVELY USED**
  - Core citation management class used by agents
  - Loads citations, tracks usage, generates citation files
  - Used by agents to lookup REF-XXXXX citations
  - Provides methods for document reference updates

- **`generate_agent_citations.py`** ⚠️ **STANDALONE/OPTIONAL**
  - Generates consolidated citation files for specific agents
  - Combines REF-XXXXX and BR-XXXXX citations
  - Not integrated into main workflow
  - Usage: `python framework/scripts/generate_agent_citations.py --agent-name <name>`

### Business Rule Extraction
- **`extract_business_rules.py`** ✅ **ACTIVELY USED**
  - Extracts business rules from code using pattern matching
  - Identifies financial, state, validation, and operation rules
  - Creates `output/context/business-rules-extracted.json`
  - Usage: `python framework/scripts/extract_business_rules.py`

### Diagram Validation

- **`simple_mermaid_validator.py`** ✅ **VALIDATION TOOL**
  - Validates Mermaid diagram syntax using mermaid-cli
  - Can fix common formatting issues
  - Supports both .md and .mmd files
  - Usage: `python framework/scripts/simple_mermaid_validator.py [path] [--fix] [--json]`

- **`diagram_component_validator.py`** 🔧 **STANDALONE UTILITY**
  - Validates components in Mermaid diagrams exist in codebase
  - Not integrated into workflow but functional
  - Usage: `python framework/scripts/diagram_component_validator.py output/diagrams/*.mmd`

### Citation Validation Tools

- **`validate_all_citations.py`** 🔧 **MANUAL VALIDATION**
  - Universal citation validator for REF-XXXXX and agent-specific patterns
  - Checks documentation and diagrams for proper citations
  - Not automatically run, must be invoked manually
  - Usage: `python framework/scripts/validate_all_citations.py [--agent <agent-name>]`

- **`validate_br_citations.py`** 🔧 **MANUAL VALIDATION**
  - Specialized validator for business rule citations (BR-XXXXX, BR-LLM-XXXXX)
  - Validates business logic documentation and diagrams
  - Generates citation map (`br-citation-map.json`)
  - Usage: `python framework/scripts/validate_br_citations.py`

### Deprecated/Unused Scripts

- **`update_agent_fallbacks.py`** 🗑️ **DEPRECATED**
  - Outdated script for updating agent fallback mechanisms
  - References non-existent files and outdated structure
  - Not functional with current architecture
  - Should be removed or archived

- **`validate_all_diagrams.sh`** 🗑️ **REDUNDANT**
  - Simple bash wrapper for `simple_mermaid_validator.py`
  - Adds no additional functionality
  - Not referenced or used anywhere
  - Can be removed

## Templates Directory

### Citation Rules
- **`CITATION_RULES.md`** ✅ **CRITICAL**
  - Defines citation requirements for all agents
  - Specifies REF-XXXXX format and usage
  - Must be followed by all documentation agents

- **`citations_template.md`** ✅ **TEMPLATE**
  - Template for generating agent citation files
  - Defines structure for citation documentation

### Validation Rules
- **`CRITICAL_RULES.md`** ✅ **CRITICAL**
  - Core rules all agents must follow
  - No hardcoded data, proper validation requirements
  - Foundational document for agent behavior

- **`DIAGRAM_VALIDATION_RULES.md`** ✅ **CRITICAL**
  - Rules for creating valid Mermaid diagrams
  - Component naming conventions
  - Citation requirements for diagrams

- **`MERMAID_RULES.md`** ✅ **CRITICAL**
  - Mermaid syntax and structure rules
  - Best practices for diagram creation
  - Validation requirements

### Documentation Templates
- **`BUSINESS_RULE_CATALOG_TEMPLATE.md`** ✅ **TEMPLATE**
  - Template for business rule documentation
  - Structure for cataloging discovered rules

- **`DATA_SOURCE_PRIORITY.md`** ✅ **GUIDANCE**
  - Defines priority of data sources for agents
  - Repomix summary > Raw codebase hierarchy

- **`SECURITY_VIOLATION_TEMPLATE.md`** ✅ **TEMPLATE**
  - Template for documenting security violations
  - Structure for security analysis reports

- **`VISUAL_INDICATORS.md`** ✅ **REFERENCE**
  - Defines visual indicators for diagrams
  - Icons, colors, and formatting conventions

### Backup Files
- **`CITATION_RULES.md.backup-with-agent-citations`** 📁 **BACKUP**
  - Backup version of citation rules
  - Contains additional agent-specific examples

## Tests Directory

### Core Test Files
- **`test_repomix_parser.py`** ✅ **COMPREHENSIVE**
  - Tests for RepomixParser class
  - Covers file parsing, component extraction, edge cases

- **`test_citation_manager.py`** ✅ **COMPREHENSIVE**
  - Tests for CitationManager class
  - 40+ test cases covering all functionality
  - Tests loading, tracking, generation, validation

- **`test_extract_citations.py`** ✅ **COMPREHENSIVE**
  - Tests citation extraction from repomix
  - Tests REF-XXXXX ID assignment
  - Covers edge cases and error handling

- **`test_extract_business_rules.py`** ✅ **COMPREHENSIVE**
  - Tests business rule extraction patterns
  - Validates rule identification and classification

- **`test_simple_mermaid_validator.py`** ✅ **COMPREHENSIVE**
  - Tests for Mermaid diagram validation
  - 43 test cases covering all functionality
  - Tests extraction, validation, fixing, CLI interface

- **`test_citation_validation.py`** ✅ **VALIDATION TESTS**
  - Tests citation validation functionality
  - Validates document and diagram citations

- **`test_helpers.py`** ✅ **UTILITY**
  - Helper functions for test suites
  - Shared test utilities and fixtures

### Test Statistics
- **Total Tests**: 217 across all test files
- **Pass Rate**: 100% (all tests passing)
- **Coverage**: Comprehensive coverage of all major components

## Key Files

### Test Runner
- **`run_tests.py`** ✅ **TEST EXECUTION**
  - Professional test runner with colored output
  - Features:
    - Colored test results (green=pass, red=fail, yellow=skip)
    - Coverage analysis with `--coverage`
    - JSON output with `--json` for CI/CD
    - Verbose modes with `-v` and `-vv`
    - Fail-fast mode with `--failfast`
  - Usage: `python framework/run_tests.py [options]`

### Documentation Viewer
- **`document-viewer.html`** ✅ **VISUALIZATION**
  - HTML viewer for rendered documentation
  - Supports Markdown and Mermaid diagrams
  - Useful for reviewing generated docs
  - Open in browser to view documentation with rendered diagrams

## Workflow Integration

### Typical Usage Flow
1. **Generate Repomix Summary**:
   ```bash
   repomix --config .repomix.config.json codebase/daytrader/
   ```

2. **Extract Citations**:
   ```bash
   python framework/scripts/extract_citations.py
   ```

3. **Extract Business Rules**:
   ```bash
   python framework/scripts/extract_business_rules.py
   ```

4. **Run Agents**: Agents use citation_manager.py to lookup citations

5. **Validate Diagrams** (Optional):
   ```bash
   python framework/scripts/simple_mermaid_validator.py output/diagrams
   ```

6. **Validate Citations** (Optional):
   ```bash
   python framework/scripts/validate_all_citations.py
   python framework/scripts/validate_br_citations.py  # For business rules
   ```

7. **Run Tests**:
   ```bash
   python framework/run_tests.py
   ```

### Dependencies Between Scripts
```
repomix_parser.py
    ├── extract_citations.py → codebase-citations.json
    │       └── citation_manager.py (used by agents)
    └── extract_business_rules.py → business-rules-extracted.json
```

## Testing

### Running Tests
```bash
# Run all tests with colored output
python framework/run_tests.py

# Run with coverage analysis
python framework/run_tests.py --coverage

# Run specific test file
python framework/run_tests.py test_citation_manager

# Run with maximum verbosity
python framework/run_tests.py -vv

# Run with JSON output for CI/CD
python framework/run_tests.py --json results.json

# Run quietly with minimal output
python framework/run_tests.py -q
```

### Test Coverage
- **Current Status**: 100% pass rate (217/217 tests passing)
- **Files Tested**: All core scripts have comprehensive test coverage
- **Edge Cases**: Extensive edge case testing for parsers and validators

## Usage Status Legend
- ✅ **ACTIVELY USED** - Core functionality, regularly used in workflow
- 🔧 **STANDALONE UTILITY** - Functional but must be run manually
- ⚠️ **OPTIONAL** - Available but not in main workflow
- 🗑️ **DEPRECATED/REDUNDANT** - No longer relevant, can be removed
- 📁 **BACKUP** - Backup/archive file

## Requirements
- Python 3.6+
- Optional: `mermaid-cli` for diagram validation
- See `requirements.txt` for Python package dependencies

## Notes
- All scripts assume working directory is project root (`/Users/jp/work/docs`)
- Output files go to `output/` directory structure
- Citations use REF-XXXXX format for code components, BR-XXXXX for business rules
- Framework designed for DayTrader but extensible to other codebases
- Test runner requires `__init__.py` files in `framework/scripts/` and `framework/tests/`

## Recent Updates
- Added comprehensive test suite with 217 tests
- Created professional test runner with colored output and coverage
- Added test files for `simple_mermaid_validator.py` and other components
- Updated status indicators to reflect actual usage patterns
- Identified deprecated/redundant scripts for cleanup