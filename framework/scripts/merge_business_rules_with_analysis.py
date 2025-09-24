#!/usr/bin/env python3
"""
Merge Business Rules with LLM Analysis
Combines deterministic rules with their LLM analysis into a single comprehensive file
Version 1.0
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys


class BusinessRuleMerger:
    """Merges business rules documentation with LLM analysis"""

    def __init__(self):
        self.deterministic_rules = {}
        self.llm_analysis = {}
        self.merged_rules = []

    def parse_deterministic_file(self, file_path: str) -> Dict[str, str]:
        """Parse the deterministic rules file and extract rules by ID"""

        print(f"📖 Parsing deterministic rules from: {file_path}")

        with open(file_path, 'r') as f:
            content = f.read()

        # Split by rule sections (### BR-XXXXX)
        # Look ahead for next rule OR a major section (## ) OR end of string
        rule_pattern = r'(### (BR-\d{5}):.*?)(?=### BR-\d{5}:|^## |\Z)'
        matches = re.finditer(rule_pattern, content, re.DOTALL | re.MULTILINE)

        rules = {}
        for match in matches:
            # Extract rule ID (group 2 has the ID)
            rule_id = match.group(2)
            # Get full content for this rule (group 1 has full content)
            rule_content = match.group(1)
            rules[rule_id] = rule_content

        print(f"  ✅ Found {len(rules)} deterministic rules")
        return rules

    def parse_analysis_file(self, file_path: str) -> Dict[str, str]:
        """Parse the LLM analysis file and extract analysis by rule ID"""

        print(f"📖 Parsing LLM analysis from: {file_path}")

        with open(file_path, 'r') as f:
            content = f.read()

        # Split by rule sections (## BR-XXXXX)
        # Note: Analysis uses ## instead of ###
        rule_pattern = r'## (BR-\d{5}):.*?(?=## BR-\d{5}:|## Analysis Summary|$)'
        matches = re.finditer(rule_pattern, content, re.DOTALL)

        analysis = {}
        for match in matches:
            rule_id = match.group(1)
            # Get analysis content, but skip the header line since we'll use deterministic header
            analysis_content = match.group(0)
            # Remove the ## BR-XXXXX: line to avoid duplication
            analysis_content = re.sub(r'^## BR-\d{5}:.*?\n\n', '', analysis_content)
            # Remove the **Type** line if present (already in deterministic)
            analysis_content = re.sub(r'\*\*Type\*\*:.*?\n\n', '', analysis_content)
            analysis[rule_id] = analysis_content

        print(f"  ✅ Found {len(analysis)} rule analyses")
        return analysis

    def merge_rule(self, rule_id: str, deterministic_content: str,
                   analysis_content: Optional[str]) -> str:
        """Merge a single rule with its analysis"""

        # Start with the deterministic content
        merged = deterministic_content.rstrip()

        # Remove the existing --- separator if present
        if merged.endswith('---'):
            merged = merged[:-3].rstrip()

        # Add LLM Analysis section if available
        if analysis_content:
            merged += "\n\n#### 🔍 LLM Analysis\n\n"
            merged += analysis_content.strip()
        else:
            merged += "\n\n#### 🔍 LLM Analysis\n\n"
            merged += "*No LLM analysis available for this rule*\n"

        # Add final separator
        merged += "\n\n---\n\n"

        return merged

    def merge_all_rules(self, deterministic_rules: Dict[str, str],
                       llm_analysis: Dict[str, str]) -> List[Tuple[str, str]]:
        """Merge all rules with their analysis"""

        print(f"🔄 Merging {len(deterministic_rules)} rules with analysis...")

        merged = []
        matched_count = 0

        # Sort rules by ID for consistent output
        sorted_rules = sorted(deterministic_rules.items(),
                             key=lambda x: int(x[0].split('-')[1]))

        for rule_id, det_content in sorted_rules:
            analysis = llm_analysis.get(rule_id)
            if analysis:
                matched_count += 1

            merged_content = self.merge_rule(rule_id, det_content, analysis)
            merged.append((rule_id, merged_content))

        print(f"  ✅ Matched {matched_count}/{len(deterministic_rules)} rules with analysis")
        return merged

    def write_merged_file(self, merged_rules: List[Tuple[str, str]],
                         output_path: str, batch_size: int = 5):
        """Write merged rules to file incrementally"""

        print(f"📝 Writing {len(merged_rules)} merged rules to {output_path}")

        # Initialize file with header
        with open(output_path, 'w') as f:
            f.write("# Complete Business Rules with LLM Analysis\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Total Rules**: {len(merged_rules)}  \n\n")
            f.write("This document combines deterministic rule extraction with ")
            f.write("comprehensive LLM analysis for each business rule.\n\n")
            f.write("Each rule includes:\n")
            f.write("- Complete implementation details and source code\n")
            f.write("- LLM analysis of what the code actually does\n")
            f.write("- Business significance and impact assessment\n")
            f.write("- Validation and error handling insights\n\n")
            f.write("---\n\n")

        # Write rules in batches
        written = 0
        for batch_start in range(0, len(merged_rules), batch_size):
            batch_end = min(batch_start + batch_size, len(merged_rules))
            batch = merged_rules[batch_start:batch_end]

            print(f"  Writing batch {batch_start//batch_size + 1}: rules {batch_start+1} to {batch_end}")

            batch_content = ""
            for rule_id, content in batch:
                batch_content += content
                written += 1

            # Append batch to file
            with open(output_path, 'a') as f:
                f.write(batch_content)

            print(f"  ✅ Written {written}/{len(merged_rules)} rules")

        # Add footer
        with open(output_path, 'a') as f:
            f.write("\n## Summary\n\n")
            f.write(f"Successfully merged **{len(merged_rules)}** business rules ")
            f.write("with their LLM analysis.\n\n")
            f.write("This comprehensive document provides both the implementation ")
            f.write("details and business understanding for each rule.\n\n")
            f.write(f"*Document generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        return written

    def merge(self, deterministic_path: str, analysis_path: str,
              output_path: str, batch_size: int = 5) -> int:
        """Main merge function"""

        try:
            # Parse both files
            det_rules = self.parse_deterministic_file(deterministic_path)
            llm_analysis = self.parse_analysis_file(analysis_path)

            # Merge rules with analysis
            merged = self.merge_all_rules(det_rules, llm_analysis)

            # Write merged file
            written = self.write_merged_file(merged, output_path, batch_size)

            print(f"\n✅ Merge complete!")
            print(f"   Output: {output_path}")
            print(f"   Rules merged: {written}")
            print(f"   File size: {Path(output_path).stat().st_size:,} bytes")

            return written

        except Exception as e:
            print(f"❌ Error during merge: {e}")
            import traceback
            traceback.print_exc()
            return 0


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Merge Business Rules with LLM Analysis')
    parser.add_argument('--deterministic', '-d',
                       default='output/docs/business-rules-deterministic-complete.md',
                       help='Path to deterministic rules file')
    parser.add_argument('--analysis', '-a',
                       default='output/docs/business-rules-llm-analysis.md',
                       help='Path to LLM analysis file')
    parser.add_argument('--output', '-o',
                       default='output/docs/business-rules-complete-with-analysis.md',
                       help='Output path for merged file')
    parser.add_argument('--batch-size', '-b',
                       type=int, default=5,
                       help='Batch size for incremental writing')

    args = parser.parse_args()

    # Check input files exist
    det_path = Path(args.deterministic)
    analysis_path = Path(args.analysis)

    if not det_path.exists():
        print(f"❌ Error: Deterministic rules file not found: {det_path}")
        return 1

    if not analysis_path.exists():
        print(f"❌ Error: Analysis file not found: {analysis_path}")
        return 1

    # Create merger and run
    merger = BusinessRuleMerger()
    result = merger.merge(
        str(det_path),
        str(analysis_path),
        args.output,
        args.batch_size
    )

    return 0 if result > 0 else 1


if __name__ == '__main__':
    exit(main())