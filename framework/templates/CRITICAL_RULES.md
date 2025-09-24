# 🚨 CRITICAL RULES - ALL AGENTS 🚨

⚠️ **MANDATORY COMPLIANCE**: These rules apply to ALL agents in the documentation and diagram generation framework.
⚠️ **VIOLATION RESULTS IN INVALID OUTPUT**: Any agent that violates these rules produces unusable results.
⚠️ **NO EXCEPTIONS**: These rules must be followed strictly without compromise.

## Data Integrity Rules

1. **MANDATORY CITATION SYSTEM**:
   - **See**: `framework/templates/CITATION_RULES.md` for complete citation requirements
   - Key requirement: ALL agents MUST generate `output/docs/citations.md`
   - Agent CANNOT complete without citations file

2. **MANDATORY DIAGRAM COMPONENT VERIFICATION**: Every component in diagrams MUST exist in code
   - **See**: `framework/templates/DIAGRAM_VALIDATION_RULES.md` for complete verification workflow
   - Pre-diagram verification required for ALL components
   - Verification log must be created before diagram
   - Only verified components can appear in diagrams
   - Use Grep tool to confirm existence: `Grep "class UserService" output/reports/repomix-summary.md`
   - Document verification: "✅ Verified: UserService found at UserService.java:245"
   - If entity not found, explicitly state: "❌ Not found in codebase"

3. **MANDATORY SEQUENCE DIAGRAM ACCURACY**: Sequence diagrams MUST show ACTUAL method calls
   - **NO CONCEPTUAL FLOWS**: Every method call must exist in the actual code
   - **READ IMPLEMENTATION FIRST**: Must read actual method body before creating diagram
   - **TRACE REAL CALLS**: Document every method call with exact line number
   - **USE EXACT NAMES**: Method names must match code exactly (not simplified)
   - **INCLUDE SQL**: Show actual SQL statements, not conceptual database operations
   - **See**: `framework/templates/DIAGRAM_VALIDATION_RULES.md` Section 2 for requirements
   - If you cannot point to the EXACT line of code, it does NOT belong in the diagram

4. **NO HARDCODED DATA**: Never use placeholder or example data
   - Use only actual data extracted from files
   - If data is not found, explicitly state "Not detected" or "Unable to determine"
   - Never fabricate metrics, counts, names, or examples

5. **NO FABRICATED METRICS**: Only use actual data from files
   - No made-up percentages, scores, or measurements
   - No estimated timelines, dates, times, costs, or resource counts
   - Use actual file counts, sizes, and detected patterns only

6. **NO UNNECESSARY TOOLS**: Only use appropriate tools
   - Use only standard tools: Read, Write, Bash, Glob, Grep, LS
   - Use JSON context files for agent communication instead

7. **STATE UNKNOWN**: If data cannot be found, explicitly state "Not detected" or "Unable to determine"
   - Better to be honest about missing data than to guess
   - Helps users understand analysis limitations
   - Maintains framework credibility

8. **COMPLETE OUTPUT REQUIRED**: ALL findings must be documented, not summarized
   - If you count 67 rules, you MUST display ALL 67 rules
   - NO truncation or "showing top 10" - show EVERYTHING
   - Total counts MUST match actual items displayed
   - Citation numbering requirements: See `framework/templates/CITATION_RULES.md`

## Cost, Timeline, and Metrics Policy

9. **NO FABRICATED MEASUREMENTS**: NEVER generate specific measurements, dates, timelines, costs, or metrics that cannot be backed up by actual data from the codebase.

**ABSOLUTELY FORBIDDEN:**
- Specific dollar amounts ($50K, $1M, etc.)
- Specific timelines (3 months, 6 weeks, 10 days, Q1 2024, etc.)
- Precise percentages (75% improvement, 40% reduction, etc.)
- Exact dates (by December 2024, January release, etc.)
- Specific resource counts (5 developers, 2 DBAs, etc.)
- Made-up performance metrics (50ms response time, 99.9% uptime, etc.)
- Fabricated ROI calculations
- Invented team sizes or effort estimates
- Estimated completion dates
- Hypothetical performance improvements

**ALWAYS USE GENERIC QUALITATIVE TERMS:**
- **Effort Level**: Minimal/Low/Medium/High/Very High/Extreme
- **Complexity**: Simple/Moderate/Complex/Very Complex/Extremely Complex
- **Impact**: Low/Medium/High/Critical
- **Risk Level**: Low/Medium/High/Critical/Severe
- **Priority**: Low/Medium/High/Critical/Urgent
- **Timeline**: Short-term/Medium-term/Long-term/Multi-phase
- **Cost**: Low-cost/Moderate-cost/High-cost/Very High-cost
- **Performance**: Poor/Fair/Good/Excellent/Outstanding
- **Urgency**: Low/Medium/High/Critical/Immediate

## Quality Assurance Rules

6. **MERMAID VALIDATION**: ALL Mermaid diagrams MUST compile without errors
   - Validate AFTER writing diagram files: `python3 framework/scripts/simple_mermaid_validator.py output/diagrams/`
   - Check exit code: 0 = success (may show "✅ Valid" messages), non-zero = errors need fixing
   - If validation fails (exit code != 0):
     * Read the specific error message
     * Fix the identified syntax issue
     * Re-validate the corrected diagram
     * Continue with agent tasks (do NOT restart agent)
   - Agent completes when all diagrams pass validation (exit code 0)
   - Note: Success messages like "✅ Valid" are NOT errors

## Data Source Priority

ALL agents MUST read data in this strict order:

1. **PRIMARY**: `output/reports/repomix-summary.md` (compressed codebase)
2. **FALLBACK**: Raw codebase access (only if compressed data insufficient)

This hierarchy ensures:
- 80% token reduction through Repomix compression
- Raw access only when necessary

## Required Outputs

ALL agents MUST produce required outputs as specified in:
- **See**: `framework/templates/CITATION_RULES.md` for citation file requirements
- Documentation: `output/docs/agent-{agent-name}.md`
- Citations: `output/docs/citations.md` (MANDATORY)
- Diagrams: `output/diagrams/{agent-name}-*.mmd` (if applicable)

## Compliance

Violation of these rules results in:
- ❌ Invalid framework output
- ❌ Broken agent chain
- ❌ Unusable documentation
- ❌ Failed diagram rendering

These rules ensure consistent, reliable, high-quality output across all agents.