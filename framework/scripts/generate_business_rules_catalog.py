#!/usr/bin/env python3
"""
Generate comprehensive Business Rules Catalog from extracted rules
Ensures ALL deterministic rules are included with code snippets
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def load_extracted_rules(json_path: str) -> Dict[str, Any]:
    """Load the extracted business rules JSON"""
    with open(json_path, 'r') as f:
        return json.load(f)

def generate_rule_section(rule: Dict[str, Any], index: int) -> str:
    """Generate markdown section for a single rule with code snippet"""
    rule_id = rule.get('business_rule_id', f'BR-{index:05d}')
    description = rule.get('business_rule_description', 'No description')
    rule_type = rule.get('rule_type', 'unknown')
    file_path = rule.get('file_path', 'Unknown')
    lines = rule.get('lines', 'Unknown')
    complexity = rule.get('complexity_score', 0)
    logic_types = rule.get('business_logic_types', [])

    # Create the main rule header
    section = f"### {rule_id}: {description}\n"
    section += f"- **Type**: {rule_type}\n"
    section += f"- **File**: {file_path}:{lines}\n"

    if rule_type == 'method':
        method_sig = rule.get('method_signature', '')
        class_name = rule.get('class_name', '')
        section += f"- **Class**: {class_name}\n"
        section += f"- **Method**: `{method_sig}`\n"
    elif rule_type in ['static_variable', 'static_constant', 'static_block']:
        name = rule.get('name', '')
        data_type = rule.get('data_type', '')
        section += f"- **Name**: {name}\n"
        section += f"- **Data Type**: {data_type}\n"

    section += f"- **Complexity Score**: {complexity}\n"

    if logic_types:
        section += f"- **Business Logic Types**: {', '.join(logic_types)}\n"

    # Add code implementation
    section += "\n#### Code Implementation:\n```java\n"

    # Get the actual code
    if rule_type == 'method':
        code = rule.get('full_method_source', '')
    else:
        code = rule.get('code_snippet', '')

    if code:
        section += code
    else:
        section += "// Code not available"

    section += "\n```\n\n"

    # Add business significance for static rules
    if rule_type in ['static_variable', 'static_constant', 'static_block']:
        significance = rule.get('business_significance', '')
        if significance:
            section += f"**Business Significance**: {significance}\n\n"

    return section

def calculate_accurate_distribution(rules: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate accurate distribution of business logic types"""
    distribution = {}

    for rule in rules:
        # For methods, use business_logic_types
        if rule.get('rule_type') == 'method':
            logic_types = rule.get('business_logic_types', [])
            for logic_type in logic_types:
                distribution[logic_type] = distribution.get(logic_type, 0) + 1

    return distribution

def generate_catalog(input_json: str, output_md: str):
    """Generate complete business rules catalog"""

    # Load extracted rules
    data = load_extracted_rules(input_json)

    rules = data.get('business_rules', [])
    stats = data.get('statistics', {})

    # Separate deterministic rules and static rules
    method_rules = [r for r in rules if r.get('rule_type') == 'method']
    static_rules = [r for r in rules if r.get('rule_type') in ['static_variable', 'static_constant', 'static_block']]

    # Calculate accurate distribution
    distribution = calculate_accurate_distribution(method_rules)

    # Start building the catalog
    catalog = f"""# Business Rules Catalog

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Source**: Automated extraction from DayTrader codebase
**Total Rules**: {len(rules)} (Method: {len(method_rules)}, Static: {len(static_rules)})

## Executive Summary

This catalog contains ALL business rules extracted from the DayTrader application through deterministic code analysis. Each rule includes:
- Complete description and classification
- Full source code implementation
- Complexity scoring
- Business logic categorization

## Part 1: Deterministic Rules (Automated Extraction)

✅ **{len(rules)} total rules** extracted via Python script - consistent every run
- **Method-based rules**: {len(method_rules)}
- **Static rules**: {len(static_rules)}

### Business Logic Distribution (Method Rules)
*Note: Rules can belong to multiple categories*
"""

    # Add distribution with correct counts
    for logic_type, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        logic_name = logic_type.replace('_', ' ').title()
        catalog += f"- **{logic_name}**: {count} occurrences\n"

    catalog += "\n---\n\n"

    # Add ALL method rules
    catalog += "## Method-Based Business Rules\n\n"

    for i, rule in enumerate(method_rules, 1):
        catalog += generate_rule_section(rule, i)
        catalog += "---\n\n"

    # Add ALL static rules
    catalog += "## Static Business Rules\n\n"
    catalog += "These rules represent business constants, thresholds, and initialization logic.\n\n"

    for rule in static_rules:
        catalog += generate_rule_section(rule, len(method_rules) + 1)
        catalog += "---\n\n"

    # Add complexity analysis
    catalog += "## Complexity Analysis\n\n"
    catalog += f"- **High Complexity (50+)**: {stats.get('high_complexity_methods', 0)} methods\n"
    catalog += f"- **Medium Complexity (20-49)**: {stats.get('medium_complexity_methods', 0)} methods\n"
    catalog += f"- **Low Complexity (<20)**: {stats.get('low_complexity_methods', 0)} methods\n"
    catalog += f"- **Average Complexity**: {stats.get('average_complexity', 0):.1f}\n\n"

    # Add top complex rules
    catalog += "### Top 10 Most Complex Rules\n\n"
    sorted_rules = sorted(rules, key=lambda x: x.get('complexity_score', 0), reverse=True)[:10]

    for i, rule in enumerate(sorted_rules, 1):
        rule_id = rule.get('business_rule_id', '')
        score = rule.get('complexity_score', 0)
        desc = rule.get('business_rule_description', '')
        catalog += f"{i}. **{rule_id}** (Score: {score}): {desc}\n"

    catalog += "\n---\n\n"
    catalog += "## Notes\n\n"
    catalog += "- All rules are extracted deterministically from source code\n"
    catalog += "- Complexity scores are calculated based on cyclomatic complexity, control flow, and business domain patterns\n"
    catalog += "- Static rules include business-critical constants and initialization blocks\n"
    catalog += "- Each rule includes the complete source code for reference and validation\n"

    # Write to file
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(catalog)

    print(f"✅ Generated complete business rules catalog: {output_md}")
    print(f"   Total rules documented: {len(rules)}")
    print(f"   - Method rules with code: {len(method_rules)}")
    print(f"   - Static rules with code: {len(static_rules)}")

    return len(rules)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Business Rules Catalog')
    parser.add_argument('--input', '-i',
                       default='../output/context/business-rules-extracted.json',
                       help='Input JSON file with extracted rules')
    parser.add_argument('--output', '-o',
                       default='../output/docs/business-rules-catalog.md',
                       help='Output markdown catalog file')

    args = parser.parse_args()

    # Check input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        return 1

    # Generate catalog
    try:
        count = generate_catalog(args.input, args.output)
        return 0
    except Exception as e:
        print(f"❌ Error generating catalog: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())