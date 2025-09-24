# Citation System Scalability Design

## Current Limitations (JSON-based)

For codebases with **1,000-5,000 classes**:
- JSON file: ~45-200 MB
- Memory usage: ~70-300 MB
- Load time: 100-500ms
- Lookup time: 75-300ms (linear search)
- **Verdict**: Still manageable but approaching limits

For codebases with **10,000+ classes**:
- JSON file: 400+ MB
- Memory usage: 600+ MB
- Load time: 1-2 seconds
- Lookup time: 600ms+ per lookup
- **Verdict**: Not viable - need database

## Recommended Architecture for Large Codebases

### Option 1: SQLite Database (Recommended for 5K-50K classes)

```python
# framework/scripts/citation_manager_db.py
import sqlite3
from pathlib import Path
import json

class CitationManagerDB:
    def __init__(self, db_path="output/context/citations.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS citations (
                ref_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                file_path TEXT,
                line_number INTEGER,
                signature TEXT,
                snippet TEXT,
                metadata JSON
            )
        ''')
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_name ON citations(name)
        ''')
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_type ON citations(type)
        ''')
        self.conn.commit()

    def lookup_citation(self, name, component_type=None):
        """O(log n) lookup with index"""
        query = "SELECT ref_id FROM citations WHERE name = ?"
        params = [name]

        if component_type:
            query += " AND type = ?"
            params.append(component_type)

        result = self.conn.execute(query, params).fetchone()
        return result['ref_id'] if result else None

    def get_citation_details(self, ref_id):
        """Direct primary key lookup - O(1)"""
        result = self.conn.execute(
            "SELECT * FROM citations WHERE ref_id = ?", [ref_id]
        ).fetchone()
        return dict(result) if result else None
```

**Migration script:**
```python
# framework/scripts/migrate_to_db.py
def migrate_json_to_sqlite():
    """One-time migration from JSON to SQLite"""
    import json
    import sqlite3

    # Load existing JSON
    with open('output/context/codebase-citations.json') as f:
        data = json.load(f)

    # Create database
    db = CitationManagerDB()

    # Batch insert for performance
    citations_to_insert = []
    for ref_id, details in data['ref_index'].items():
        citations_to_insert.append((
            ref_id,
            details['name'],
            details.get('type'),
            details.get('file_path'),
            details.get('line_number'),
            details.get('signature'),
            details.get('snippet'),
            json.dumps(details)  # Store full details as JSON
        ))

    db.conn.executemany(
        '''INSERT INTO citations
           (ref_id, name, type, file_path, line_number, signature, snippet, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        citations_to_insert
    )
    db.conn.commit()
    print(f"✅ Migrated {len(citations_to_insert)} citations to SQLite")
```

### Option 2: Redis/KeyDB (For 50K+ classes, distributed teams)

```python
# framework/scripts/citation_manager_redis.py
import redis
import json

class CitationManagerRedis:
    def __init__(self, host='localhost', port=6379):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.name_index = "citation:names"  # Hash for name->ref_id
        self.details_prefix = "citation:detail:"  # Key prefix for details

    def lookup_citation(self, name, component_type=None):
        """O(1) hash lookup"""
        key = f"{name}:{component_type}" if component_type else name
        return self.r.hget(self.name_index, key)

    def get_citation_details(self, ref_id):
        """O(1) key-value lookup"""
        details = self.r.get(f"{self.details_prefix}{ref_id}")
        return json.loads(details) if details else None

    def bulk_load(self, citations_json):
        """Efficient bulk loading with pipeline"""
        pipe = self.r.pipeline()

        for ref_id, details in citations_json['ref_index'].items():
            # Store name->ref_id mapping
            name_key = details['name']
            pipe.hset(self.name_index, name_key, ref_id)

            # Store full details
            pipe.set(
                f"{self.details_prefix}{ref_id}",
                json.dumps(details)
            )

        pipe.execute()
```

### Option 3: Elasticsearch (For complex searches, 100K+ classes)

```python
# framework/scripts/citation_manager_elastic.py
from elasticsearch import Elasticsearch

class CitationManagerElastic:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.index = 'code-citations'
        self._ensure_index()

    def _ensure_index(self):
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index, body={
                'mappings': {
                    'properties': {
                        'ref_id': {'type': 'keyword'},
                        'name': {'type': 'keyword'},
                        'type': {'type': 'keyword'},
                        'file_path': {'type': 'text'},
                        'snippet': {'type': 'text'},
                        'signature': {'type': 'text'}
                    }
                }
            })

    def lookup_citation(self, name, fuzzy=False):
        """Support fuzzy matching for typos"""
        query = {
            'match': {'name': name}
        } if not fuzzy else {
            'fuzzy': {'name': {'value': name, 'fuzziness': 'AUTO'}}
        }

        result = self.es.search(index=self.index, body={'query': query})
        hits = result['hits']['hits']
        return hits[0]['_source']['ref_id'] if hits else None
```

## Hybrid Approach (Recommended for Growth)

```python
# framework/scripts/citation_manager_hybrid.py
class CitationManagerHybrid:
    """
    Hybrid approach that scales with your codebase:
    - < 5K citations: Use in-memory JSON (current)
    - 5K-50K: Automatically switch to SQLite
    - > 50K: Prompt to setup Redis/Elastic
    """

    def __init__(self):
        citations_count = self._count_citations()

        if citations_count < 5000:
            self.backend = CitationManagerJSON()
            print(f"📚 Using JSON backend ({citations_count} citations)")
        elif citations_count < 50000:
            self.backend = CitationManagerDB()
            print(f"📚 Using SQLite backend ({citations_count} citations)")
        else:
            print(f"⚠️  Large codebase detected ({citations_count} citations)")
            print("   Consider setting up Redis or Elasticsearch")
            print("   Falling back to SQLite (may be slow)")
            self.backend = CitationManagerDB()

    def lookup_citation(self, name, component_type=None):
        return self.backend.lookup_citation(name, component_type)

    def get_citation_details(self, ref_id):
        return self.backend.get_citation_details(ref_id)
```

## Performance Comparison

| Backend | 1K Citations | 10K Citations | 100K Citations | 1M Citations |
|---------|-------------|---------------|----------------|--------------|
| **JSON** | ✅ 2ms load<br>✅ 1ms lookup | ⚠️ 20ms load<br>⚠️ 10ms lookup | ❌ 200ms load<br>❌ 100ms lookup | ❌ 2s load<br>❌ 1s lookup |
| **SQLite** | ✅ 5ms connect<br>✅ 1ms lookup | ✅ 5ms connect<br>✅ 1ms lookup | ✅ 5ms connect<br>✅ 2ms lookup | ✅ 5ms connect<br>✅ 3ms lookup |
| **Redis** | ✅ 1ms connect<br>✅ 0.1ms lookup | ✅ 1ms connect<br>✅ 0.1ms lookup | ✅ 1ms connect<br>✅ 0.1ms lookup | ✅ 1ms connect<br>✅ 0.1ms lookup |
| **Elastic** | ✅ 10ms connect<br>✅ 5ms lookup | ✅ 10ms connect<br>✅ 5ms lookup | ✅ 10ms connect<br>✅ 5ms lookup | ✅ 10ms connect<br>✅ 5ms lookup |

## Implementation Steps

### Step 1: Measure Your Codebase
```bash
# Count potential citations
find codebase -name "*.java" -o -name "*.cs" -o -name "*.py" | xargs wc -l
# Rule of thumb: ~1 citation per 50 lines of code
```

### Step 2: Choose Backend
- **< 5K classes**: Keep current JSON approach
- **5K-50K classes**: Migrate to SQLite
- **50K+ classes**: Setup Redis or Elasticsearch
- **Distributed teams**: Use Redis/Elasticsearch for sharing

### Step 3: Update Agent Include
The shared include (`citation-manager-setup.md`) would detect and use appropriate backend:

```python
# Auto-detect best backend
from citation_manager_hybrid import CitationManagerHybrid
manager = CitationManagerHybrid()  # Automatically chooses best backend
```

### Step 4: Migration Path
1. Keep generating JSON (compatibility)
2. Run migration script to populate database
3. Agents automatically use optimal backend
4. No changes needed to agent code!

## Additional Optimizations for Large Codebases

### 1. Lazy Loading
```python
class LazyloadingCitationManager:
    def __init__(self):
        self.cache = {}  # LRU cache for recent lookups
        self.db = None    # Connect only when needed

    def _ensure_connected(self):
        if not self.db:
            self.db = CitationManagerDB()
```

### 2. Sharding by Package/Module
```python
class ShardedCitationManager:
    def __init__(self):
        # Separate databases per major module
        self.shards = {
            'ui': CitationManagerDB('citations-ui.db'),
            'business': CitationManagerDB('citations-business.db'),
            'data': CitationManagerDB('citations-data.db'),
        }
```

### 3. Async Loading for Agents
```python
# Load citations in background while agent initializes
import asyncio

async def load_citations_async():
    manager = await CitationManagerAsync.create()
    return manager
```

## Recommendations by Scale

| Codebase Size | Recommended Setup | Load Time | Lookup Time | Infrastructure |
|---------------|------------------|-----------|-------------|----------------|
| **Small** (< 1K classes) | Current JSON | < 5ms | < 1ms | None |
| **Medium** (1K-5K) | JSON with indexes | < 50ms | < 5ms | None |
| **Large** (5K-50K) | SQLite | < 10ms | < 2ms | Local file |
| **XLarge** (50K-200K) | Redis | < 5ms | < 0.5ms | Redis server |
| **Enterprise** (200K+) | Elasticsearch | < 20ms | < 5ms | ES cluster |

---

## Summary

The current JSON approach works well up to ~5,000 classes. Beyond that:
1. **SQLite** is the easiest upgrade path (no infrastructure needed)
2. **Redis** offers best performance for large teams
3. **Elasticsearch** enables fuzzy search and complex queries
4. **Hybrid approach** automatically scales with your codebase

The beauty is that agents don't need to change - just the CitationManager backend!