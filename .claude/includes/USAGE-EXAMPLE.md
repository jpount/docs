# Example: How to Add Citation Support to Any Agent

## For a New Agent

Add this to your agent's initialization section:

```markdown
---
name: your-agent-name
description: Your agent description
tools: Read, Write, Glob, Grep, Bash
---

## Initialization

### Step 1: Initialize Citation System

<!-- Include shared citation setup -->
**Using shared include from**: `.claude/includes/citation-manager-setup.md`

[Copy the initialization code from citation-manager-setup.md here]

### Step 2: Your Agent-Specific Setup
[Continue with your agent-specific initialization...]
```

## For Existing Agents

Replace any existing citation loading code with:

```markdown
### Initialize Citations

**See**: `.claude/includes/citation-manager-setup.md`

[Copy initialization code from the shared include]
```

## Example Integration in Different Agent Types

### Security Analyst Example
```python
# After initialization, look up security-relevant components
python3 -c "
import sys; sys.path.append('framework/scripts')
from citation_manager import CitationManager
m = CitationManager(); m.load_citations()

# Security components to analyze
security_components = [
    'authenticate', 'authorize', 'login',
    'logout', 'validateUser', 'checkPermission'
]

for comp in security_components:
    ref_id = m.lookup_citation(comp)
    if ref_id:
        print(f'Security component {comp}: [{ref_id}]')
"
```

### Performance Analyst Example
```python
# Look up performance-critical components
python3 -c "
import sys; sys.path.append('framework/scripts')
from citation_manager import CitationManager
m = CitationManager(); m.load_citations()

# Performance bottleneck candidates
perf_components = [
    'executeQuery', 'processTransaction',
    'calculateTotal', 'loadData'
]

for comp in perf_components:
    ref_id = m.lookup_citation(comp)
    if ref_id:
        details = m.get_citation_details(ref_id)
        print(f'Performance point {comp} [{ref_id}]: {details.get(\"file_path\")}'')
"
```

### UI Analyst Example
```python
# Look up UI components and pages
python3 -c "
import sys; sys.path.append('framework/scripts')
from citation_manager import CitationManager
m = CitationManager(); m.load_citations()

# UI components
ui_components = [
    'LoginServlet', 'AccountBean', 'QuoteBean',
    'displayQuote', 'portfolio', 'tradehome'
]

for comp in ui_components:
    ref_id = m.lookup_citation(comp)
    if ref_id:
        print(f'UI component {comp}: [{ref_id}]')
"
```

## Benefits of Using Shared Include

1. **Consistency**: All agents use same citation system
2. **Maintenance**: Update once in shared file
3. **Reliability**: Tested code reused everywhere
4. **Speed**: No need to rewrite for each agent
5. **Standards**: Enforces citation best practices

## Quick Checklist for Agents

- [ ] Include citation-manager-setup.md initialization
- [ ] Run initialization code at agent startup
- [ ] Use `manager.lookup_citation()` for all component references
- [ ] Include REF-XXXXX in all documentation
- [ ] Add citation comments to all diagrams

---
*Remember: The shared include ensures all agents have consistent citation handling!*