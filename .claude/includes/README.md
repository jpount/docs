# Shared Includes for Claude Agents

This directory contains reusable code snippets and configurations that can be included in multiple agents.

## Available Includes

### 1. Citation Manager Setup (`citation-manager-setup.md`)
Provides CitationManager initialization and lookup functionality for all agents.

**Usage in your agent:**
```markdown
## Step 1: Initialize Systems

<!-- Include Citation Manager Setup -->
See: `.claude/includes/citation-manager-setup.md` for citation initialization

[Then copy the initialization code from that file]
```

Or more directly in the agent instructions:

```markdown
### Initialize Citation System
**Run the code from** `.claude/includes/citation-manager-setup.md` section "Initialize CitationManager"
```

## Benefits of Using Includes

1. **Consistency**: All agents use the same citation system
2. **Maintainability**: Update once, applies to all agents
3. **DRY Principle**: Don't Repeat Yourself
4. **Standardization**: Common patterns across all agents

## How to Create New Includes

1. Create a new `.md` file in this directory
2. Add reusable code/instructions
3. Document usage in this README
4. Reference from agents as needed

## Best Practices

- Keep includes focused on a single functionality
- Document all parameters/variables that need customization
- Provide clear usage examples
- Version/date your includes for tracking changes