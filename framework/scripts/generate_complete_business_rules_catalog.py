#!/usr/bin/env python3
"""
Generate COMPLETE Business Rules Catalog with incremental writing
Ensures ALL rules are documented without memory issues
Version 2.0 - Enhanced with batch processing and progress tracking
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import traceback

def load_extracted_rules(json_path: str) -> Dict[str, Any]:
    """Load the extracted business rules JSON"""
    with open(json_path, 'r') as f:
        return json.load(f)

def generate_rule_markdown(rule: Dict[str, Any], index: int) -> str:
    """Generate markdown for a single rule with full details"""
    rule_id = rule.get('business_rule_id', f'BR-{index:05d}')
    description = rule.get('business_rule_description', 'No description')
    rule_type = rule.get('rule_type', 'unknown')
    file_path = rule.get('file_path', 'Unknown')
    lines = rule.get('lines', 'Unknown')
    complexity = rule.get('complexity_score', 0)
    logic_types = rule.get('business_logic_types', [])

    # Build markdown section
    section = f"### {rule_id}: {description}\n\n"
    section += f"**Type**: {rule_type}  \n"
    section += f"**Location**: `{file_path}:{lines}`  \n"

    # Add method-specific details
    if rule_type == 'method':
        method_sig = rule.get('method_signature', '')
        class_name = rule.get('class_name', '')
        if class_name:
            section += f"**Class**: `{class_name}`  \n"
        if method_sig:
            section += f"**Method Signature**: `{method_sig}`  \n"

    # Add static-specific details
    elif rule_type in ['static_variable', 'static_constant', 'static_block']:
        name = rule.get('name', '')
        data_type = rule.get('data_type', '')
        if name:
            section += f"**Name**: `{name}`  \n"
        if data_type:
            section += f"**Data Type**: `{data_type}`  \n"

    # Add complexity and logic types
    if complexity > 0:
        section += f"**Complexity Score**: {complexity}  \n"

    if logic_types:
        section += f"**Business Logic Categories**: {', '.join(logic_types)}  \n"

    # Add code implementation
    section += "\n#### Implementation\n\n```java\n"

    # Get the actual code
    if rule_type == 'method':
        code = rule.get('full_method_source', '')
    else:
        code = rule.get('code_snippet', '')

    if code:
        # Ensure code is properly formatted
        section += code.rstrip() + "\n"
    else:
        section += "// Source code not available\n"

    section += "```\n\n"

    # Add business significance for static rules
    if rule_type in ['static_variable', 'static_constant', 'static_block']:
        significance = rule.get('business_significance', '')
        if significance:
            section += f"**Business Significance**: {significance}\n\n"

    # Add extraction metadata
    section += f"*Extracted via: Deterministic pattern matching (Python)*\n\n"
    section += "---\n\n"

    return section

def write_rules_incrementally(rules: List[Dict[str, Any]], output_path: str,
                            rule_type: str, batch_size: int = 5):
    """Write rules incrementally in batches to avoid memory issues"""

    total_rules = len(rules)
    print(f"📝 Writing {total_rules} {rule_type} rules to {output_path}")

    # Initialize file with header
    with open(output_path, 'w') as f:
        f.write(f"# Complete Business Rules Catalog - {rule_type}\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Total Rules**: {total_rules}  \n")
        f.write(f"**Source**: Automated extraction from DayTrader codebase  \n\n")
        f.write("---\n\n")

    # Process rules in batches
    rules_written = 0
    for batch_start in range(0, total_rules, batch_size):
        batch_end = min(batch_start + batch_size, total_rules)
        batch = rules[batch_start:batch_end]

        print(f"  Processing batch {batch_start//batch_size + 1}: rules {batch_start+1} to {batch_end}")

        # Generate markdown for batch
        batch_content = ""
        for i, rule in enumerate(batch, start=batch_start+1):
            try:
                batch_content += generate_rule_markdown(rule, i)
                rules_written += 1
            except Exception as e:
                print(f"  ⚠️ Warning: Error processing rule {i}: {e}")
                continue

        # Append batch to file
        with open(output_path, 'a') as f:
            f.write(batch_content)

        print(f"  ✅ Written {rules_written}/{total_rules} rules")

    # Add footer
    with open(output_path, 'a') as f:
        f.write("\n---\n\n")
        f.write("## Summary\n\n")
        f.write(f"Successfully documented **{rules_written}** out of **{total_rules}** {rule_type} rules.\n\n")
        f.write("All rules include:\n")
        f.write("- Complete source code implementation\n")
        f.write("- Location and context information\n")
        f.write("- Complexity scoring and categorization\n")
        f.write("- Business significance annotations\n\n")
        f.write(f"*Document generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    return rules_written

def generate_distribution_summary(rules: List[Dict[str, Any]]) -> str:
    """Generate distribution summary for rules"""

    # Calculate distribution
    distribution = {}
    for rule in rules:
        if rule.get('rule_type') == 'method':
            for logic_type in rule.get('business_logic_types', []):
                distribution[logic_type] = distribution.get(logic_type, 0) + 1

    # Build summary
    summary = "## Business Logic Distribution\n\n"
    summary += "*Note: Rules can belong to multiple categories*\n\n"

    for logic_type, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        logic_name = logic_type.replace('_', ' ').title()
        summary += f"- **{logic_name}**: {count} occurrences\n"

    return summary

def main():
    """Main function with comprehensive error handling"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Complete Business Rules Catalog')
    parser.add_argument('--input', '-i',
                       default='output/context/business-rules-extracted.json',
                       help='Input JSON file with extracted rules')
    parser.add_argument('--output-dir', '-o',
                       default='output/docs',
                       help='Output directory for markdown files')
    parser.add_argument('--batch-size', '-b',
                       type=int, default=5,
                       help='Batch size for incremental writing (default: 5)')

    args = parser.parse_args()

    # Resolve paths
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    # Check input file exists
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📊 Loading business rules from: {input_path}")

    try:
        # Load rules
        data = load_extracted_rules(str(input_path))
        all_rules = data.get('business_rules', [])
        stats = data.get('statistics', {})

        print(f"✅ Loaded {len(all_rules)} total rules")

        # Separate rules by type
        method_rules = [r for r in all_rules if r.get('rule_type') == 'method']
        static_rules = [r for r in all_rules if r.get('rule_type') in
                       ['static_variable', 'static_constant', 'static_block']]

        print(f"   - Method rules: {len(method_rules)}")
        print(f"   - Static rules: {len(static_rules)}")

        # Generate complete deterministic catalog
        deterministic_output = output_dir / 'business-rules-deterministic-complete.md'

        print(f"\n📝 Generating complete deterministic catalog...")

        # Write header with statistics
        with open(deterministic_output, 'w') as f:
            f.write("# Complete Deterministic Business Rules Catalog\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Source**: Automated Python extraction from DayTrader codebase  \n")
            f.write(f"**Total Rules**: {len(all_rules)}  \n")
            f.write(f"**Method Rules**: {len(method_rules)}  \n")
            f.write(f"**Static Rules**: {len(static_rules)}  \n\n")

            # Add distribution summary
            f.write(generate_distribution_summary(method_rules))
            f.write("\n---\n\n")

        # Process ALL rules together to maintain original BR-XXXXX IDs
        print(f"\n📝 Writing all {len(all_rules)} rules to complete catalog...")

        method_written = 0
        static_written = 0

        # Write method rules section header
        if method_rules:
            with open(deterministic_output, 'a') as f:
                f.write("## Part 1: Method-Based Business Rules\n\n")
                f.write(f"Total: {len(method_rules)} rules\n\n")

            # Write method rules
            method_written = 0
            for batch_start in range(0, len(method_rules), args.batch_size):
                batch_end = min(batch_start + args.batch_size, len(method_rules))
                batch = method_rules[batch_start:batch_end]

                print(f"  Processing method batch {batch_start//args.batch_size + 1}: rules {batch_start+1} to {batch_end}")

                batch_content = ""
                for rule in batch:
                    try:
                        # Keep original rule ID
                        rule_id = rule.get('business_rule_id', '')
                        idx = int(rule_id.split('-')[-1]) if rule_id else batch_start + 1
                        batch_content += generate_rule_markdown(rule, idx)
                        method_written += 1
                    except Exception as e:
                        print(f"  ⚠️ Warning: Error processing rule: {e}")
                        continue

                with open(deterministic_output, 'a') as f:
                    f.write(batch_content)

                print(f"  ✅ Written {method_written}/{len(method_rules)} method rules")

        # Write static rules section header
        if static_rules:
            with open(deterministic_output, 'a') as f:
                f.write("\n## Part 2: Static Business Rules\n\n")
                f.write("These rules represent business constants, thresholds, and initialization logic.\n\n")
                f.write(f"Total: {len(static_rules)} rules\n\n")

            # Write static rules
            static_written = 0
            for batch_start in range(0, len(static_rules), args.batch_size * 2):
                batch_end = min(batch_start + args.batch_size * 2, len(static_rules))
                batch = static_rules[batch_start:batch_end]

                print(f"  Processing static batch: rules {batch_start+1} to {batch_end}")

                batch_content = ""
                for rule in batch:
                    try:
                        # Keep original rule ID
                        rule_id = rule.get('business_rule_id', '')
                        idx = int(rule_id.split('-')[-1]) if rule_id else len(method_rules) + batch_start + 1
                        batch_content += generate_rule_markdown(rule, idx)
                        static_written += 1
                    except Exception as e:
                        print(f"  ⚠️ Warning: Error processing rule: {e}")
                        continue

                with open(deterministic_output, 'a') as f:
                    f.write(batch_content)

                print(f"  ✅ Written {static_written}/{len(static_rules)} static rules")

        rules_written = method_written + static_written
        print(f"✅ Total rules written: {rules_written}")

        # Verify all rules were written
        total_expected = len(all_rules)

        # Count rules in output file
        with open(deterministic_output, 'r') as f:
            content = f.read()
            rule_count = content.count('### BR-')

        print(f"\n📊 Final Verification:")
        print(f"   Expected rules: {total_expected}")
        print(f"   Rules written: {rule_count}")

        if rule_count == total_expected:
            print(f"   ✅ SUCCESS: All {total_expected} rules documented!")
        else:
            print(f"   ⚠️ WARNING: Only {rule_count} of {total_expected} rules written")

        # Add complexity analysis
        with open(deterministic_output, 'a') as f:
            f.write("\n## Complexity Analysis\n\n")
            f.write(f"- **High Complexity (50+)**: {stats.get('high_complexity_methods', 0)} methods\n")
            f.write(f"- **Medium Complexity (20-49)**: {stats.get('medium_complexity_methods', 0)} methods\n")
            f.write(f"- **Low Complexity (<20)**: {stats.get('low_complexity_methods', 0)} methods\n")
            f.write(f"- **Average Complexity**: {stats.get('average_complexity', 0):.1f}\n\n")

        print(f"\n✅ Complete catalog written to: {deterministic_output}")
        print(f"   File size: {deterministic_output.stat().st_size:,} bytes")

        return 0

    except Exception as e:
        print(f"❌ Error generating catalog: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())