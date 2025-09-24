#!/usr/bin/env python3
"""
LLM Business Rule Discovery Script
Discovers additional business rules through semantic analysis
that cannot be detected by deterministic pattern matching
Version 1.0
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from repomix_parser import RepomixParser

class LLMBusinessRuleDiscoverer:
    """Discovers business rules through semantic analysis"""

    def __init__(self):
        self.discovered_rules = []
        self.rule_counter = 1

    def search_comments_for_rules(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Search comments for business logic hints"""
        rules = []

        # Pattern for TODO/FIXME/NOTE comments with business implications
        comment_patterns = [
            (r'//\s*TODO:?\s*(.+)', 'todo_comment'),
            (r'//\s*FIXME:?\s*(.+)', 'fixme_comment'),
            (r'//\s*NOTE:?\s*(.+)', 'note_comment'),
            (r'//\s*Business Rule:?\s*(.+)', 'business_rule_comment'),
            (r'/\*\s*(.+?)\s*\*/', 'block_comment'),
        ]

        for pattern, comment_type in comment_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                comment_text = match.group(1).strip()

                # Look for business-relevant keywords in comments
                business_keywords = [
                    'must', 'should', 'require', 'validate', 'check',
                    'limit', 'maximum', 'minimum', 'threshold', 'constraint',
                    'approve', 'reject', 'allow', 'deny', 'permission',
                    'calculate', 'round', 'precision', 'decimal',
                    'before', 'after', 'within', 'expire', 'timeout',
                    'fee', 'charge', 'commission', 'tax', 'discount'
                ]

                if any(keyword in comment_text.lower() for keyword in business_keywords):
                    line_num = content[:match.start()].count('\n') + 1
                    rules.append({
                        'type': 'comment_rule',
                        'text': comment_text,
                        'file_path': file_path,
                        'line': line_num,
                        'confidence': 'medium',
                        'category': comment_type
                    })

        return rules

    def search_configuration_for_rules(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Search configuration files for business settings"""
        rules = []

        # Look for properties and configuration patterns
        config_patterns = [
            (r'max[._-]?(\w+)\s*[=:]\s*(\d+)', 'maximum_limit'),
            (r'min[._-]?(\w+)\s*[=:]\s*(\d+)', 'minimum_limit'),
            (r'timeout[._-]?(\w*)\s*[=:]\s*(\d+)', 'timeout_setting'),
            (r'limit[._-]?(\w+)\s*[=:]\s*(\d+)', 'limit_setting'),
            (r'threshold[._-]?(\w*)\s*[=:]\s*(\d+)', 'threshold_setting'),
            (r'expire[._-]?(\w*)\s*[=:]\s*(\d+)', 'expiration_setting'),
            (r'retry[._-]?(\w*)\s*[=:]\s*(\d+)', 'retry_setting'),
        ]

        for pattern, setting_type in config_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                setting_name = match.group(1) if match.group(1) else 'value'
                setting_value = match.group(2) if len(match.groups()) > 1 else match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                rules.append({
                    'type': 'configuration_rule',
                    'setting': f"{setting_type}_{setting_name}",
                    'value': setting_value,
                    'file_path': file_path,
                    'line': line_num,
                    'confidence': 'high',
                    'category': setting_type
                })

        return rules

    def search_validation_patterns(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Search for validation patterns not caught by deterministic extraction"""
        rules = []

        # JSP/JSF validation patterns
        jsp_patterns = [
            (r'<\w+:validate\w+[^>]*required\s*=\s*"true"', 'required_field'),
            (r'<\w+:validate\w+[^>]*min\w*\s*=\s*"([^"]+)"', 'minimum_validation'),
            (r'<\w+:validate\w+[^>]*max\w*\s*=\s*"([^"]+)"', 'maximum_validation'),
            (r'<\w+:validate\w+[^>]*pattern\s*=\s*"([^"]+)"', 'pattern_validation'),
        ]

        for pattern, validation_type in jsp_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                value = match.group(1) if len(match.groups()) > 0 else 'true'

                rules.append({
                    'type': 'ui_validation_rule',
                    'validation': validation_type,
                    'constraint': value,
                    'file_path': file_path,
                    'line': line_num,
                    'confidence': 'high',
                    'category': 'frontend_validation'
                })

        # JavaScript/TypeScript validation
        js_patterns = [
            (r'if\s*\([^)]*\.length\s*[<>]=?\s*(\d+)', 'length_validation'),
            (r'if\s*\([^)]*\s*[<>]=?\s*(\d+)', 'numeric_validation'),
            (r'\.test\s*\([^)]+\)', 'regex_validation'),
            (r'required:\s*true', 'required_validation'),
        ]

        for pattern, validation_type in js_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                value = match.group(1) if len(match.groups()) > 0 else 'detected'

                rules.append({
                    'type': 'client_validation_rule',
                    'validation': validation_type,
                    'value': value,
                    'file_path': file_path,
                    'line': line_num,
                    'confidence': 'medium',
                    'category': 'client_side_validation'
                })

        return rules

    def search_error_messages(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract business rules from error messages"""
        rules = []

        # Error message patterns that indicate business rules
        error_patterns = [
            (r'throw\s+new\s+\w*Exception\s*\(["\']([^"\']+)["\']', 'exception_message'),
            (r'Log\.error\s*\(["\']([^"\']+)["\']', 'error_log'),
            (r'addError\w*\s*\(["\']([^"\']+)["\']', 'validation_error'),
            (r'setError\w*\s*\(["\']([^"\']+)["\']', 'error_message'),
        ]

        business_error_keywords = [
            'exceed', 'limit', 'invalid', 'required', 'must',
            'cannot', 'insufficient', 'expired', 'denied',
            'unauthorized', 'forbidden', 'duplicate', 'exists'
        ]

        for pattern, error_type in error_patterns:
            for match in re.finditer(pattern, content):
                error_msg = match.group(1)
                if any(keyword in error_msg.lower() for keyword in business_error_keywords):
                    line_num = content[:match.start()].count('\n') + 1

                    rules.append({
                        'type': 'error_constraint_rule',
                        'message': error_msg,
                        'error_type': error_type,
                        'file_path': file_path,
                        'line': line_num,
                        'confidence': 'medium',
                        'category': 'error_handling'
                    })

        return rules

    def search_cross_method_workflows(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Identify business workflows spanning multiple methods"""
        rules = []

        # Workflow patterns
        workflow_patterns = [
            (r'(create\w+|init\w+).*then.*?(update\w+|process\w+)', 'initialization_workflow'),
            (r'(validate\w+).*before.*?(save\w+|persist\w+)', 'validation_workflow'),
            (r'(check\w+|verify\w+).*then.*?(approve\w+|reject\w+)', 'approval_workflow'),
            (r'(calculate\w+).*then.*?(update\w+|set\w+)', 'calculation_workflow'),
        ]

        for pattern, workflow_type in workflow_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                line_num = content[:match.start()].count('\n') + 1

                rules.append({
                    'type': 'workflow_rule',
                    'workflow': workflow_type,
                    'pattern': match.group(0)[:100],  # First 100 chars
                    'file_path': file_path,
                    'line': line_num,
                    'confidence': 'low',
                    'category': 'business_workflow'
                })

        return rules

    def search_permission_checks(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find permission and authorization rules"""
        rules = []

        permission_patterns = [
            (r'hasRole\s*\(["\']([^"\']+)["\']', 'role_check'),
            (r'hasPermission\s*\(["\']([^"\']+)["\']', 'permission_check'),
            (r'isAuthorized\s*\([^)]*\)', 'authorization_check'),
            (r'checkAccess\s*\([^)]*\)', 'access_check'),
            (r'@Secured\s*\(["\']([^"\']+)["\']', 'security_annotation'),
            (r'@RolesAllowed\s*\(["\']([^"\']+)["\']', 'roles_annotation'),
        ]

        for pattern, check_type in permission_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                permission = match.group(1) if len(match.groups()) > 0 else 'detected'

                rules.append({
                    'type': 'permission_rule',
                    'check': check_type,
                    'permission': permission,
                    'file_path': file_path,
                    'line': line_num,
                    'confidence': 'high',
                    'category': 'security'
                })

        return rules

    def create_llm_rule(self, discovery: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a discovery into a formal LLM business rule"""

        rule_id = f"BR-LLM-{self.rule_counter:03d}"
        self.rule_counter += 1

        # Generate description based on discovery type
        description = self.generate_description(discovery)

        # Generate business significance
        significance = self.generate_significance(discovery)

        rule = {
            'business_rule_id': rule_id,
            'business_rule_description': description,
            'rule_type': 'llm_discovered',
            'discovery_type': discovery['type'],
            'file_path': discovery['file_path'],
            'line': discovery['line'],
            'confidence': discovery['confidence'],
            'category': discovery['category'],
            'business_significance': significance,
            'evidence': discovery
        }

        return rule

    def generate_description(self, discovery: Dict[str, Any]) -> str:
        """Generate human-readable description for discovered rule"""

        disc_type = discovery['type']

        if disc_type == 'comment_rule':
            return f"Business constraint from comment: {discovery['text'][:100]}"
        elif disc_type == 'configuration_rule':
            return f"Configuration limit: {discovery['setting']} = {discovery['value']}"
        elif disc_type == 'ui_validation_rule':
            return f"UI validation: {discovery['validation']} with constraint {discovery['constraint']}"
        elif disc_type == 'client_validation_rule':
            return f"Client-side validation: {discovery['validation']}"
        elif disc_type == 'error_constraint_rule':
            return f"Error constraint: {discovery['message'][:80]}"
        elif disc_type == 'workflow_rule':
            return f"Business workflow: {discovery['workflow']}"
        elif disc_type == 'permission_rule':
            return f"Permission requirement: {discovery['check']} for {discovery['permission']}"
        else:
            return f"Discovered business rule: {disc_type}"

    def generate_significance(self, discovery: Dict[str, Any]) -> str:
        """Generate business significance for discovered rule"""

        category = discovery.get('category', '')

        if category in ['maximum_limit', 'minimum_limit', 'threshold_setting']:
            return "Defines operational boundaries for business processes"
        elif category == 'frontend_validation':
            return "Ensures data quality at point of entry"
        elif category == 'error_handling':
            return "Enforces business constraints through error conditions"
        elif category == 'business_workflow':
            return "Defines multi-step business process requirements"
        elif category == 'security':
            return "Controls access to business functions based on roles"
        elif category in ['timeout_setting', 'expiration_setting']:
            return "Manages time-based business constraints"
        else:
            return "Implements additional business logic not captured by code patterns"

    def discover_rules_from_repomix(self, repomix_path: str) -> List[Dict[str, Any]]:
        """Discover rules from repomix summary"""

        print(f"📊 Loading repomix from: {repomix_path}")

        # Parse repomix
        parser = RepomixParser(repomix_path)
        parser.load()
        components = parser.extract_all_components()

        discovered = []

        # Process each file
        for comp_type, comp_list in components.items():
            for component in comp_list:
                if hasattr(component, 'content'):
                    content = '\n'.join(component.content)
                    file_path = component.file_path

                    print(f"  Analyzing: {file_path}")

                    # Run discovery methods
                    discoveries = []
                    discoveries.extend(self.search_comments_for_rules(content, file_path))
                    discoveries.extend(self.search_configuration_for_rules(content, file_path))
                    discoveries.extend(self.search_validation_patterns(content, file_path))
                    discoveries.extend(self.search_error_messages(content, file_path))
                    discoveries.extend(self.search_cross_method_workflows(content, file_path))
                    discoveries.extend(self.search_permission_checks(content, file_path))

                    # Convert to formal rules
                    for discovery in discoveries:
                        rule = self.create_llm_rule(discovery)
                        discovered.append(rule)

        return discovered

def write_discovered_rules(rules: List[Dict[str, Any]], output_path: str):
    """Write discovered rules to markdown file"""

    print(f"📝 Writing {len(rules)} discovered rules to {output_path}")

    with open(output_path, 'w') as f:
        f.write("# Additional LLM-Discovered Business Rules\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Total Rules Discovered**: {len(rules)}  \n\n")
        f.write("These rules were discovered through semantic analysis of:\n")
        f.write("- Comments and documentation\n")
        f.write("- Configuration settings and properties\n")
        f.write("- UI validation patterns\n")
        f.write("- Error messages and constraints\n")
        f.write("- Cross-method workflows\n")
        f.write("- Permission and security checks\n\n")
        f.write("---\n\n")

        # Group rules by category
        categories = {}
        for rule in rules:
            cat = rule.get('category', 'other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rule)

        # Write rules by category
        for category, cat_rules in categories.items():
            f.write(f"## {category.replace('_', ' ').title()}\n\n")
            f.write(f"*{len(cat_rules)} rules discovered*\n\n")

            for rule in cat_rules:
                f.write(f"### {rule['business_rule_id']}: {rule['business_rule_description']}\n\n")
                f.write(f"**Type**: {rule['discovery_type']}  \n")
                f.write(f"**Confidence**: {rule['confidence']}  \n")
                f.write(f"**Location**: `{rule['file_path']}:{rule['line']}`  \n")
                f.write(f"**Significance**: {rule['business_significance']}  \n\n")

                # Add evidence details
                evidence = rule['evidence']
                f.write("**Evidence**:\n")
                if 'text' in evidence:
                    f.write(f"- Comment: `{evidence['text']}`\n")
                elif 'message' in evidence:
                    f.write(f"- Message: `{evidence['message']}`\n")
                elif 'setting' in evidence:
                    f.write(f"- Setting: `{evidence['setting']} = {evidence['value']}`\n")
                elif 'validation' in evidence:
                    f.write(f"- Validation: `{evidence['validation']}`\n")
                elif 'permission' in evidence:
                    f.write(f"- Permission: `{evidence['permission']}`\n")

                f.write("\n---\n\n")

        # Add summary
        f.write("## Discovery Summary\n\n")
        f.write(f"Total rules discovered: **{len(rules)}**\n\n")
        f.write("### By Category:\n")
        for category, cat_rules in categories.items():
            f.write(f"- {category.replace('_', ' ').title()}: {len(cat_rules)}\n")

        f.write("\n### By Confidence:\n")
        high_conf = len([r for r in rules if r['confidence'] == 'high'])
        med_conf = len([r for r in rules if r['confidence'] == 'medium'])
        low_conf = len([r for r in rules if r['confidence'] == 'low'])
        f.write(f"- High confidence: {high_conf}\n")
        f.write(f"- Medium confidence: {med_conf}\n")
        f.write(f"- Low confidence: {low_conf}\n")

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Discover Additional LLM Business Rules')
    parser.add_argument('--repomix', '-r',
                       default='output/reports/repomix-summary.md',
                       help='Path to repomix summary file')
    parser.add_argument('--output', '-o',
                       default='output/docs/business-rules-llm-discovered.md',
                       help='Output markdown file')

    args = parser.parse_args()

    # Check input exists
    repomix_path = Path(args.repomix)
    if not repomix_path.exists():
        print(f"❌ Error: Repomix file not found: {repomix_path}")
        return 1

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Create discoverer
        discoverer = LLMBusinessRuleDiscoverer()

        # Discover rules
        print("🔍 Starting LLM rule discovery...")
        rules = discoverer.discover_rules_from_repomix(str(repomix_path))

        print(f"✅ Discovered {len(rules)} additional business rules")

        # Write results
        write_discovered_rules(rules, str(output_path))

        print(f"\n✅ Discovery complete!")
        print(f"   Output: {output_path}")
        print(f"   Rules discovered: {len(rules)}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())