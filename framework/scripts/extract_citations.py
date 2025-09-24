#!/usr/bin/env python3
"""
Extract Citations - Main script to pre-extract all citations from repomix-summary.md
This runs once after repomix to create a searchable citation index.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import argparse

# Add framework scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from repomix_parser import RepomixParser


def assign_ref_ids(components):
    """Assign unique REF-XXXXX IDs to all components"""
    ref_counter = 0
    export_data = {}
    ref_index = {}  # Maps REF-XXXXX to component details for quick lookup

    # Process each component type
    for comp_type, comp_list in components.items():
        export_data[comp_type] = []

        for comp in comp_list:
            ref_counter += 1
            ref_id = f"REF-{ref_counter:05d}"

            # Convert component to dict (if it's a dataclass)
            if hasattr(comp, '__dict__'):
                comp_dict = comp.__dict__.copy()
            else:
                comp_dict = comp

            # Add REF-ID to the component
            comp_dict['ref_id'] = ref_id

            # Add to export data
            export_data[comp_type].append(comp_dict)

            # Create index entry for quick lookup
            ref_index[ref_id] = {
                'name': comp_dict.get('name'),
                'type': comp_dict.get('type'),
                'file_path': comp_dict.get('file_path'),
                'line': comp_dict.get('original_line')
            }

    # Include the ref_index for quick lookups
    export_data['ref_index'] = ref_index

    print(f"✅ Assigned {ref_counter} REF-XXXXX identifiers")

    return export_data


def main(args):
    """Main extraction process"""
    print("=" * 80)
    print("📚 CITATION EXTRACTION TOOL")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check if repomix file exists
    repomix_path = Path(args.input)
    if not repomix_path.exists():
        print(f"❌ ERROR: Repomix file not found: {repomix_path}")
        print("\n💡 Please run repomix first:")
        print("   repomix --config .repomix.config.json codebase/daytrader/")
        sys.exit(1)

    print(f"📖 Input: {repomix_path}")
    print(f"📝 Output: {args.output}")
    print()

    # Initialize parser
    print("🔄 Initializing repomix parser...")
    parser = RepomixParser(str(repomix_path))

    # Load the file
    if not parser.load():
        print("❌ Failed to load repomix file")
        sys.exit(1)

    # Extract all components
    print("\n🔍 Extracting code components...")
    print("-" * 40)
    components = parser.extract_all_components()

    # Export to JSON
    print("\n💾 Saving to JSON...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to JSON with REF-XXXXX IDs
    print("\n📝 Assigning REF-XXXXX identifiers...")
    export_data = assign_ref_ids(components)

    # Add metadata
    export_data["metadata"] = {
        "generated": datetime.now().isoformat(),
        "source": str(repomix_path),
        "version": "1.2",  # Updated version with REF-XXXXX
        "total_components": sum(len(v) for k, v in export_data.items() if k != 'metadata' and k != 'ref_index')
    }

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)

    print(f"✅ Exported citations to {output_path}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 80)
    total_components = sum(len(v) for k, v in export_data.items() if k != 'metadata' and isinstance(v, list))
    print(f"📊 Total components extracted: {total_components}")
    print(f"📁 Output file: {output_path}")
    print(f"📏 Output size: {output_path.stat().st_size / 1024:.1f} KB")
    print()

    # Usage instructions
    print("🎯 Next Steps:")
    print("1. Agents can now load this file for citations")
    print("2. Use CitationManager in agents to lookup components")
    print("3. Example usage in agent:")
    print()
    print("   from framework.scripts.citation_manager import CitationManager")
    print("   manager = CitationManager()")
    print("   manager.load_citations()")
    print("   ref_id = manager.lookup_citation('TradeServices')")
    print()

    return 0


def validate_extraction(citations_path: str):
    """Validate the extracted citations"""
    path = Path(citations_path)
    if not path.exists():
        print(f"❌ Citations file not found: {path}")
        return False

    with open(path, 'r') as f:
        data = json.load(f)

    print("\n🔍 Validation Results:")
    print("-" * 40)

    # Check for required keys
    required_keys = ['classes', 'interfaces', 'methods', 'metadata']
    for key in required_keys:
        if key in data:
            if key == 'metadata':
                print(f"✅ Metadata present")
            else:
                count = len(data[key])
                print(f"✅ {key}: {count} items")
        else:
            print(f"❌ Missing: {key}")

    # Sample some entries
    if 'classes' in data and data['classes']:
        print("\n📋 Sample Classes:")
        for cls in data['classes'][:3]:
            if isinstance(cls, dict) and 'name' in cls:
                name = cls.get('name', 'unnamed')
                file_path = cls.get('file_path', 'unknown')
                print(f"  - {name} ({file_path})")

    if 'methods' in data and data['methods']:
        print("\n📋 Sample Methods:")
        for method in data['methods'][:3]:
            if isinstance(method, dict) and 'name' in method:
                name = method.get('name', 'unnamed')
                parent_class = method.get('parent_class', 'global')
                print(f"  - {name} ({parent_class})")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract citations from repomix-summary.md'
    )
    parser.add_argument(
        '-i', '--input',
        default='output/reports/repomix-summary.md',
        help='Path to repomix-summary.md (default: output/reports/repomix-summary.md)'
    )
    parser.add_argument(
        '-o', '--output',
        default='output/context/codebase-citations.json',
        help='Output path for citations JSON (default: output/context/codebase-citations.json)'
    )
    parser.add_argument(
        '-v', '--validate',
        action='store_true',
        help='Validate the output after extraction'
    )

    args = parser.parse_args()

    # Run extraction
    result = main(args)

    # Optional validation
    if result == 0 and args.validate:
        validate_extraction(args.output)

    sys.exit(result)