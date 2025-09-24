# Initial commit

# Documentation & Diagram Generation Framework

A streamlined framework for analyzing codebases and generating comprehensive documentation, architecture diagrams, and technical insights. Optimized for Claude Code with intelligent agent orchestration.

## Overview

This framework analyzes your codebase using specialized AI agents to produce:
- **Technical Documentation**: Complete system analysis and architecture documentation
- **Visual Diagrams**: Mermaid-based architecture, flow, and component diagrams  
- **Business Logic Analysis**: Extracted business rules and domain insights
- **Performance & Security Analysis**: Bottlenecks, vulnerabilities, and optimization opportunities

### Key Features
- **Intelligent Agent System**: Specialized agents for different analysis tasks
- **Token Optimization**: 80% token reduction via Repomix compression
- **Progressive Analysis**: Agents build context from previous outputs
- **Automated Workflow**: Hands-off execution with progress tracking

## 🚀 Quick Start

### 1. Place Your Code
```bash
# Copy your codebase to the analysis directory
cp -r /path/to/your/code/codebase/project-name/
```

### 2. Generate Repomix Summary (Required)
```bash
# Create compressed codebase summary (80% token reduction)
repomix --config .repomix.config.json codebase/project-name/

# Verify output exists
ls -la output/reports/repomix-summary.md
```

### 3. Extract Citations & Business Rules (Optional)
```bash
# Extract citations from repomix output for agent reference
python3 framework/scripts/extract_citations.py

# Extract business rules from repomix output
python3 framework/scripts/extract_business_rules.py
```

### 4. Run Analysis Agents
```bash
# Run agents individually in Claude Code:
@performance-analyst
```


## Project Structure

```
├── CLAUDE.md                   # Project configuration for Claude Code
├── .repomix.config.json        # Repomix compression configuration
│
├── .claude/agents/             # AI agent definitions
│   ├── business-logic-analyst.md
│   └── [other-agents].md
│
├── codebase/                   # YOUR CODE GOES HERE
│   └── daytrader/             # Target project (configurable)
│
├── output/                     # GENERATED OUTPUT
│   ├── docs/                  # Generated documentation
│   ├── diagrams/              # Mermaid diagrams
│   ├── context/               # Agent context files
│   └── reports/               # Analysis reports
│
└── framework/                  # Framework components
    ├── scripts/               # Automation scripts  
    └── templates/             # Configuration templates
```

## Expected Outputs

### Documentation (`output/docs/`)
- **Business Logic Documentation**: Extracted rules and domain processes

### Diagrams (`output/diagrams/`)
- **Process Flow Diagrams**: Business workflows and data flows

### Context Files (`output/context/`)
- **Codebase Citations**: JSON index of all classes, methods, and functions
- **Business Rules**: Extracted business logic and validation rules

### `CLAUDE.md`
Contains agent execution instructions and workflow rules.

### `.repomix.config.json`
Configures which files to include/exclude during compression.

## Troubleshooting

### Common Issues

1. **Missing Repomix Summary**
   ```
   ❌ Repomix summary not found: output/reports/repomix-summary.md
   ```
   **Solution**: Run `repomix --config .repomix.config.json codebase/daytrader/`

2. **Agent Execution Failures**
   - Ensure Claude Code is installed and accessible
   - Verify agent names match those in `.claude/agents/`
   - Check that `output/` directories exist

3. **Large Codebase Issues**
   - Ensure Repomix summary was generated successfully
   - Check `.repomix.config.json` excludes unnecessary files
   - Consider running agents individually rather than in batch

## Requirements

- **Claude Code CLI**: [Installation guide](https://claude.ai/code)
- **Python 3.7+**: For automation scripts
- **Repomix**: `npm install -g repomix` (for token optimization)
- **Your codebase**: Place in `codebase/[project-name]/`

## Citation System

### Workflow Order
1. **Run Repomix FIRST** - Creates `output/reports/repomix-summary.md`
2. **Extract Citations** - Creates `output/context/codebase-citations.json`
3. **Extract Business Rules** - Creates `output/context/business-rules-extracted.json`
4. **Run Analysis** - Agents can now reference citations

### Complete Pipeline
```bash
# Full order:
repomix --config .repomix.config.json codebase/daytrader/  # MUST BE FIRST
python3 framework/scripts/extract_citations.py             # Extract citations
python3 framework/scripts/extract_business_rules.py        # Extract business rules
python3 setup.py                                           # Configure agents
python3 run_analysis.py                                    # Run analysis
```

### Testing Citation Scripts
```bash
# Test the parser:
python3 framework/scripts/repomix_parser.py

# Test the citation manager:
python3 framework/scripts/citation_manager.py

# Test full extraction with validation:
python3 framework/scripts/extract_citations.py --validate
```

### Citation Files Created
- `framework/scripts/repomix_parser.py` - Parses repomix-summary.md
- `framework/scripts/citation_manager.py` - Manages citations and REF-XXXXX IDs
- `framework/scripts/extract_citations.py` - Main extraction script
- `output/context/codebase-citations.json` - Extracted citations index
- `output/citations/{agent-name}-citations.md` - Per-agent citation references

**Key Point**: The repomix-summary.md file MUST exist before citations can be extracted!

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Mermaid Diagram Syntax](https://mermaid.js.org)
- [Repomix Documentation](https://github.com/repomix/repomix)

---

**Framework Focus**: Documentation and diagram generation
**Automation**: Python scripts  
