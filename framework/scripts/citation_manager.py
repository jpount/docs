#!/usr/bin/env python3
"""
Citation Manager - Manages code citations and references for documentation
Provides REF-XXXXX style citations and tracks usage across documents.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime


class CitationManager:
    """Manages citations for code components in documentation"""

    def __init__(self, citations_json_path: str = "output/context/codebase-citations.json"):
        self.citations_json_path = Path(citations_json_path)
        self.citations: Dict[str, Dict] = {}
        self.ref_counter = 0
        self.ref_mapping: Dict[str, Dict] = {}  # REF-XXXXX -> component details
        self.usage_tracking: Dict[str, Set[str]] = {}  # REF-XXXXX -> set of files using it
        self.agent_name: Optional[str] = None

    def load_citations(self) -> bool:
        """Load pre-extracted citations from JSON"""
        if not self.citations_json_path.exists():
            print(f"⚠️  Citations file not found: {self.citations_json_path}")
            print("   Run 'python extract_citations.py' first to generate citations")
            return False

        with open(self.citations_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Store the full citation data
        self.citations = data

        # Load the pre-assigned REF-XXXXX mappings
        if 'ref_index' in data:
            # Build reverse index for quick lookups
            for ref_id, details in data['ref_index'].items():
                self.ref_mapping[ref_id] = details

        # Count total components (excluding metadata and ref_index)
        total = sum(len(v) for k, v in data.items() if k not in ['metadata', 'ref_index'] and isinstance(v, list))
        print(f"✅ Loaded {total} citations from {self.citations_json_path}")
        return True

    def set_agent_name(self, agent_name: str):
        """Set the current agent name for tracking"""
        self.agent_name = agent_name
        print(f"📝 Citation manager initialized for agent: {agent_name}")

    def find_component(self, name: str, component_type: Optional[str] = None) -> Optional[Tuple[str, Dict]]:
        """
        Find a component by name and optionally type.
        Returns (ref_id, component_details) or None
        """
        # Search in specified type or all types
        search_types = [component_type + 's'] if component_type else [k for k in self.citations.keys() if k not in ['metadata', 'ref_index']]

        for type_key in search_types:
            if type_key not in self.citations or not isinstance(self.citations[type_key], list):
                continue

            for component in self.citations[type_key]:
                if component.get('name') == name:
                    # Use the pre-assigned REF-ID
                    ref_id = component.get('ref_id')
                    if ref_id:
                        # Update ref_mapping if needed
                        if ref_id not in self.ref_mapping:
                            self.ref_mapping[ref_id] = component
                        return ref_id, component

        return None

    def lookup_citation(self, name: str, component_type: Optional[str] = None) -> Optional[str]:
        """
        Simple lookup - returns just the REF-XXXXX for a component.
        This is what agents will primarily use.
        """
        result = self.find_component(name, component_type)
        return result[0] if result else None

    def get_citation_details(self, ref_id: str) -> Optional[Dict]:
        """Get full details for a REF-XXXXX citation"""
        return self.ref_mapping.get(ref_id)

    def _get_or_create_ref(self, component: Dict, type_key: str) -> str:
        """Get existing REF-ID or create new one"""
        # Create unique key for component
        comp_key = f"{type_key}:{component['file_path']}:{component['name']}:{component.get('repomix_line', 0)}"

        # Check if already has REF-ID
        for ref_id, details in self.ref_mapping.items():
            if details.get('_key') == comp_key:
                return ref_id

        # Create new REF-ID
        self.ref_counter += 1
        ref_id = f"REF-{self.ref_counter:05d}"

        # Store mapping with component details
        self.ref_mapping[ref_id] = {
            **component,
            '_key': comp_key,
            'type_category': type_key
        }

        return ref_id

    def track_usage(self, ref_id: str, file_name: str):
        """Track that a REF-ID is used in a specific file"""
        if ref_id not in self.usage_tracking:
            self.usage_tracking[ref_id] = set()
        self.usage_tracking[ref_id].add(file_name)

    def add_citation(self, component: str, file_path: str,
                     original_line: Optional[int] = None,
                     repomix_line: Optional[int] = None,
                     code_snippet: Optional[str] = None) -> str:
        """
        Add a custom citation not in the pre-extracted list.
        Returns the REF-ID.
        """
        self.ref_counter += 1
        ref_id = f"REF-{self.ref_counter:05d}"

        self.ref_mapping[ref_id] = {
            'name': component,
            'file_path': file_path,
            'original_line': original_line,
            'repomix_line': repomix_line,
            'snippet': code_snippet,
            'type': 'custom',
            '_custom': True
        }

        return ref_id

    def generate_citations_file(self, output_dir: str = "output/citations") -> str:
        """Generate the citations.md file for the current agent"""
        if not self.agent_name:
            print("⚠️  No agent name set. Call set_agent_name() first.")
            return ""

        output_path = Path(output_dir) / f"{self.agent_name}-citations.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._format_citations_content()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Generated citations file: {output_path}")
        return str(output_path)

    def _format_citations_content(self) -> str:
        """Format the citations content for markdown output"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Code Citations Reference - {self.agent_name}

This document contains all code citations referenced in the {self.agent_name} documentation.
Each reference ID maps to specific code locations in the codebase.

Generated: {timestamp}
Agent: {self.agent_name}

---

## Citation Format

Each citation follows this format:
- **REF-XXXXX** in documentation/diagrams → Details below
- Minimal in diagrams: `%% ComponentName: REF-XXXXX`
- Clean in docs: `ComponentName [REF-XXXXX]`

---

## Citations

"""

        # Sort REF-IDs numerically
        sorted_refs = sorted(self.ref_mapping.keys(), key=lambda x: int(x.split('-')[1]))

        for ref_id in sorted_refs:
            details = self.ref_mapping[ref_id]
            content += self._format_single_citation(ref_id, details)

        # Add special references section
        content += """
---

## Special References

### External Systems
- **External**: Third-party services not in codebase

### Not Found
- **NOT FOUND**: Components mentioned but not detected in code

---

## Usage

1. In documentation: `The UserService [REF-00001] handles authentication`
2. In diagrams:
   ```mermaid
   sequenceDiagram
       %% Component Citations
       %% UserService: REF-00001
       %% AuthController: REF-00002
   ```

---
"""

        return content

    def _format_single_citation(self, ref_id: str, details: Dict) -> str:
        """Format a single citation entry"""
        name = details.get('name', 'Unknown')
        file_path = details.get('file_path', 'Unknown')
        original_line = details.get('original_line')
        repomix_line = details.get('repomix_line')
        component_type = details.get('type', details.get('type_category', 'Unknown'))
        snippet = details.get('snippet', details.get('signature', ''))

        # Get usage tracking
        used_in = self.usage_tracking.get(ref_id, set())
        used_in_str = ', '.join(f"`{f}`" for f in sorted(used_in)) if used_in else "Not yet referenced"

        # Format line number
        line_str = f":{original_line}" if original_line else ""

        entry = f"""### {ref_id}: {name}
- **File**: `{file_path}{line_str}`
"""

        if repomix_line:
            entry += f"- **Repomix Line**: {repomix_line}\n"

        entry += f"""- **Type**: {component_type}
- **Context**: {snippet[:100] + '...' if snippet and len(snippet) > 100 else snippet if snippet else 'N/A'}
- **Used in**: {used_in_str}

"""
        return entry

    def update_document_with_references(self, content: str, doc_name: str) -> Tuple[str, int]:
        """
        Update a document to use REF-XXXXX format for any inline citations.
        Also tracks usage for each REF-ID.
        Returns (updated_content, count_of_citations_added)
        """
        # Pattern to find inline citations like (ClassName.java:123)
        pattern = r'`?(\w+)`?\s*\(([^:)]+\.\w+):?(\d+)?\)'
        count = 0

        def replace_with_ref(match):
            nonlocal count
            component_name = match.group(1)
            file_name = match.group(2)

            # Try to find this component
            result = self.find_component(component_name)
            if result:
                ref_id, _ = result
                self.track_usage(ref_id, doc_name)
                count += 1
                return f"`{component_name}` [{ref_id}]"

            return match.group(0)  # Keep original if not found

        updated = re.sub(pattern, replace_with_ref, content)
        return updated, count

    def generate_diagram_citations(self, component_names: List[str]) -> str:
        """
        Generate citation comments for Mermaid diagrams.
        Given a list of component names used in a diagram, returns the citation comment block.
        """
        citations = []
        for name in component_names:
            ref_id = self.lookup_citation(name)
            if ref_id:
                citations.append(f"    %% {name}: {ref_id}")

        if citations:
            return "    %% Component Citations\n" + "\n".join(citations)
        return "    %% Component Citations\n    %% No components requiring citation"

    def validate_citations_in_document(self, file_path: str) -> Dict:
        """Validate that all REF-XXXXX in a document are valid"""
        path = Path(file_path)
        if not path.exists():
            return {"valid": False, "error": f"File not found: {file_path}"}

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all REF-XXXXX patterns
        refs = re.findall(r'REF-\d{5}', content)

        invalid_refs = []
        valid_refs = []

        for ref in set(refs):  # Use set to avoid duplicates
            if ref in self.ref_mapping:
                valid_refs.append(ref)
                self.track_usage(ref, path.name)
            else:
                invalid_refs.append(ref)

        return {
            "valid": len(invalid_refs) == 0,
            "valid_refs": valid_refs,
            "invalid_refs": invalid_refs,
            "total_refs": len(set(refs))
        }

    def get_stats(self) -> Dict:
        """Get statistics about citations"""
        return {
            "total_citations": len(self.ref_mapping),
            "citations_used": len(self.usage_tracking),
            "citations_by_type": {
                type_key: len([r for r in self.ref_mapping.values()
                             if r.get('type_category') == type_key])
                for type_key in self.citations.keys()
            },
            "most_referenced": sorted(
                [(ref, len(files)) for ref, files in self.usage_tracking.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


if __name__ == "__main__":
    # Test the citation manager
    manager = CitationManager()

    if manager.load_citations():
        # Test finding a component
        manager.set_agent_name("test-agent")

        # Example lookups
        test_names = ["TradeServices", "buy", "OrderDataBean"]

        print("\n🔍 Testing component lookups:")
        for name in test_names:
            ref_id = manager.lookup_citation(name)
            if ref_id:
                print(f"  ✓ {name} -> {ref_id}")
            else:
                print(f"  ✗ {name} -> Not found")

        # Generate sample citations file
        manager.track_usage("REF-001", "test-doc.md")
        manager.generate_citations_file()

        # Show stats
        print("\n📊 Citation Stats:")
        stats = manager.get_stats()
        print(f"  Total citations available: {stats['total_citations']}")
        print(f"  Citations by type: {stats['citations_by_type']}")