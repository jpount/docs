# Visual Indicators Standard

## Required Indicators for All Agents

Always use these indicators to highlight findings:

- 🔴 **Critical**: Blocking issues, showstoppers, critical failures
- 🟠 **High**: Significant issues needing urgent attention
- 🟡 **Medium**: Notable issues requiring planning
- ⚠️ **Warning**: Potential problems or risks
- ✅ **Good**: Well-implemented patterns, best practices
- 🚨 **Security**: Security vulnerabilities or concerns
- ⚡ **Performance**: Performance bottlenecks or optimizations
- 🏗️ **Technical Debt**: Legacy code, maintenance issues
- 🔄 **Migration**: Modernization or migration considerations

## Usage Guidelines

1. **Consistency**: Use the same indicators across all agents
2. **Visibility**: Place indicators at the start of findings for quick scanning
3. **Context**: Always explain why an indicator was chosen
4. **Balance**: Include positive (✅) findings, not just problems

## Examples

```markdown
🔴 **Critical: SQL Injection vulnerability** in UserDAO.java:145
🟠 **High: Circular dependency** between OrderService and PaymentService
✅ **Good: Proper use of dependency injection** in ServiceConfiguration
⚡ **Performance: N+1 query pattern** detected in ProductRepository
```

## Special Context Indicators

- 📊 **Metrics**: For quantitative data (when available from code)
- 🔍 **Investigation Needed**: Requires deeper analysis
- 📝 **Documentation**: Documentation gaps or needs
- 🎯 **Quick Win**: Easy improvements with high impact