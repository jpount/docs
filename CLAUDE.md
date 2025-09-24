# Project Configuration for Claude Code

## Project Overview
- **Project Name:** daytrader
- **Framework Mode:** Enhanced Documentation & Diagram Generation
- **Codebase Location:** codebase/daytrader
- **Framework Version:** 2.1 (Enhanced)

## Core Workflow

### 🔴 STEP 1: Generate Repomix Summary (REQUIRED)
```bash
# Generate compressed codebase summary (80% token reduction)
repomix --config .repomix.config.json codebase/daytrader/

# Verify output exists
ls -la output/reports/repomix-summary.md
```

### ⚡ STEP 2: Run Analysis Agents
# Run agents individually:

## Available Agents

## Agent Data Flow Rules

### 🔴 CRITICAL: All Agents Must Follow This Priority
1. **PRIMARY**: Read `output/reports/repomix-summary.md` (compressed codebase)
3. **FALLBACK**: Access raw codebase only if needed

### Critical Rules for ALL Agents
⚠️ **SEE**: `framework/templates/CRITICAL_RULES.md` for complete rules

**Key requirements:**
- NO hardcoded data or fabricated metrics
- ALL Mermaid diagrams MUST validate with zero errors before completion
- State "Not detected" for missing information

### Required Agent Outputs
Each agent MUST produce:
- `output/docs/agent-{agent-name}.md` - Documentation
- `output/diagrams/{agent-name}-*.mmd` - Diagrams (if applicable)

## Output Locations
- **Documentation:** `output/docs/`
- **Diagrams:** `output/diagrams/`
- **Reports:** `output/reports/`

---
*Generated dynamically on 2025-09-21 16:43*
