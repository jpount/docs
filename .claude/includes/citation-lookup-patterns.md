# Citation Lookup Patterns

## Citation Lookup Patterns

### Looking Up Components for Documentation

When you need to cite components in your documentation, use this pattern:

```python
# Look up specific components you're documenting
python3 -c "
import sys
sys.path.append('framework/scripts')
from citation_manager import CitationManager

manager = CitationManager()
manager.load_citations()

# List the components you need to cite
components_to_cite = [
    'ComponentName1',
    'ComponentName2',
    'MethodName',
    # Add your specific components here
]

print('Component Citation Lookups:')
for comp in components_to_cite:
    ref_id = manager.lookup_citation(comp)
    if ref_id:
        details = manager.get_citation_details(ref_id)
        file_path = details.get('file_path', 'unknown')
        line = details.get('original_line', '')
        print(f'{comp}: [{ref_id}] at {file_path}:{line}')
    else:
        print(f'{comp}: No citation found - may need manual REF assignment')
"
```

### Common Usage Examples

1. **For Class Documentation:**
   - Replace components_to_cite with your class names
   - Use the returned REF-XXXXX in your documentation

2. **For Method Documentation:**
   - Include method names in the lookup
   - Citations work for both classes and methods

3. **For Diagram Components:**
   - Look up all components before creating diagrams
   - Use returned REF-XXXXX in `%% Component Citations` blocks