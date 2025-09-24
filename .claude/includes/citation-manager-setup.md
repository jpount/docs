# Citation Manager Initialization

Execute this code block to initialize the CitationManager:

```bash
# Initialize CitationManager for citation lookups
python3 -c "
import sys
sys.path.append('framework/scripts')
from citation_manager import CitationManager

# Initialize CitationManager
manager = CitationManager()
if manager.load_citations():
    # Save success status
    with open('/tmp/citations_loaded.txt', 'w') as f:
        f.write('SUCCESS')

    # Confirm ready
    print('📚 CitationManager initialized successfully')
    print('   ✓ Ready for component lookups')
    print('   ✓ Use: manager.lookup_citation(\"ComponentName\") → REF-XXXXX')
else:
    print('❌ Failed to load citations - run extract_citations.py first')
    with open('/tmp/citations_loaded.txt', 'w') as f:
        f.write('FAILED')
"

# Verify citations loaded
if [ -f /tmp/citations_loaded.txt ] && grep -q "SUCCESS" /tmp/citations_loaded.txt; then
    echo "✅ Citation system ready"
else
    echo "❌ CRITICAL: Citations not loaded - agent cannot continue"
    echo "   Run: python3 framework/scripts/extract_citations.py"
    exit 1
fi
```