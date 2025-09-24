#!/usr/bin/env python3
"""
Advanced Business Logic Extraction from Repomix Summary - Version 4
Enhanced to capture:
- Static variables and constants (especially financial/business constants)
- Static initialization blocks
- Instance initialization blocks
- Critical class-level business rules
- Multi-language support: Java, C#/.NET, PHP
"""

import re
import json
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Protocol, NamedTuple, Tuple
from datetime import datetime
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import defaultdict

# Tree-sitter imports for AST analysis
try:
    import tree_sitter
    from tree_sitter_java import language as java_language
    try:
        from tree_sitter_c_sharp import language as csharp_language
    except ImportError:
        csharp_language = None
    try:
        from tree_sitter_php import language as php_language
    except ImportError:
        php_language = None
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    java_language = None
    csharp_language = None
    php_language = None
    print("⚠️ Warning: tree-sitter not available. Install with 'pip install tree-sitter tree-sitter-java'")

# Add framework scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from repomix_parser import RepomixParser


@dataclass
class BusinessLogicSnippet:
    """Represents a specific business logic pattern found within a method or class"""
    type: str
    description: str
    pattern_matched: str
    code_lines: str
    snippet: str
    confidence: float
    importance: int  # 1-5 scale
    context: str = ""  # Additional context around the match


@dataclass
class StaticBusinessRule:
    """Represents a static variable, constant, or initialization block"""
    rule_type: str  # 'static_variable', 'constant', 'static_block', 'instance_block'
    name: str  # Variable name or 'static_initializer'
    data_type: str  # e.g., BigDecimal, String, int
    value: str  # Initial value if available
    code_snippet: str  # Full code snippet
    file_path: str
    class_name: str
    lines: str
    business_significance: str  # Why this is important
    complexity_score: int


@dataclass
class MethodBusinessLogic:
    """Consolidated business logic analysis for a single method"""
    method_signature: str
    file_path: str
    class_name: str
    start_line: int
    end_line: int
    complexity_score: int
    business_logic_types: List[str]
    snippets: List[BusinessLogicSnippet]
    full_method_body: str
    control_flow_complexity: int
    business_domain_score: int
    rules: List[str] = None  # New field for tree-sitter extracted rules
    cyclomatic_complexity: int = 0
    method_length: int = 0
    has_business_annotations: bool = False


class TreeSitterBusinessRuleAnalyzer:
    """Uses tree-sitter AST analysis to extract business rules from method source code"""

    def __init__(self):
        self.parsers = {}
        self.languages = {}

        if TREE_SITTER_AVAILABLE:
            # Initialize Java parser
            if java_language is not None:
                try:
                    java_parser = tree_sitter.Parser(java_language())
                    self.parsers['java'] = java_parser
                    self.languages['java'] = java_language()
                except Exception as e:
                    print(f"⚠️ Warning: Failed to initialize Java parser: {e}")

            # Initialize C# parser if available
            if csharp_language is not None:
                try:
                    csharp_parser = tree_sitter.Parser(csharp_language())
                    self.parsers['csharp'] = csharp_parser
                    self.languages['csharp'] = csharp_language()
                except Exception as e:
                    print(f"⚠️ Warning: Failed to initialize C# parser: {e}")

            # Initialize PHP parser if available
            if php_language is not None:
                try:
                    php_parser = tree_sitter.Parser(php_language())
                    self.parsers['php'] = php_parser
                    self.languages['php'] = php_language()
                except Exception as e:
                    print(f"⚠️ Warning: Failed to initialize PHP parser: {e}")

    def get_language_from_file_path(self, file_path: str) -> Optional[str]:
        """Determine language from file extension"""
        ext = Path(file_path).suffix.lower()
        if ext in ['.java', '.jsp', '.jsf']:
            return 'java'
        elif ext in ['.cs', '.cshtml']:
            return 'csharp'
        elif ext in ['.php', '.phtml', '.php3', '.php4', '.php5', '.php7', '.phps']:
            return 'php'
        return None

    def extract_business_rules_from_method(self, method_source: str, file_path: str) -> List[str]:
        """Extract business rules from method source using tree-sitter AST analysis"""
        if not TREE_SITTER_AVAILABLE:
            return self._fallback_rule_extraction(method_source, file_path)

        language = self.get_language_from_file_path(file_path)
        if language not in self.parsers:
            return self._fallback_rule_extraction(method_source, file_path)

        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(method_source, 'utf8'))
            root_node = tree.root_node

            rules = []

            if language == 'java':
                rules = self._extract_java_business_rules(root_node, method_source)
            elif language == 'csharp':
                rules = self._extract_csharp_business_rules(root_node, method_source)
            elif language == 'php':
                rules = self._extract_php_business_rules(root_node, method_source)

            return rules

        except Exception as e:
            print(f"⚠️ Warning: Tree-sitter parsing failed for {file_path}: {e}")
            return self._fallback_rule_extraction(method_source, file_path)

    def _fallback_rule_extraction(self, method_source: str, file_path: str) -> List[str]:
        """Generic contextual rule extraction for any business domain"""
        rules = []

        # Generic business indicators (not domain-specific)
        business_indicators = [
            'calculate', 'validate', 'process', 'create', 'update', 'delete',
            'check', 'verify', 'ensure', 'handle', 'manage', 'execute',
            'if (', 'switch', 'for (', 'while (', 'try {',
            '== null', '!= null', '.equals(', '.compareTo(',
            'BigDecimal', 'Money', 'Currency', 'Amount', 'Decimal'
        ]

        if not any(indicator in method_source for indicator in business_indicators):
            return []

        lines = method_source.split('\n')

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//'):
                continue

            # Generic conditional logic extraction with context
            if 'if (' in line_stripped:
                condition_match = re.search(r'if\s*\(([^)]+)\)', line_stripped)
                if condition_match:
                    condition = condition_match.group(1).strip()
                    context = self._get_meaningful_context(lines, i, 1, 2)

                    if '== null' in condition or '!= null' in condition:
                        entity = condition.split()[0] if condition.split() else 'object'
                        rules.append(f"Validation rule: Check {entity} existence -> {condition}\nContext:\n{context}")
                    elif any(comparator in condition for comparator in ['==', '!=', '>', '<', '>=', '<=']):
                        rules.append(f"Business condition: Evaluate {condition} to control flow\nContext:\n{context}")
                    else:
                        rules.append(f"Conditional logic: {condition}\nContext:\n{context}")

            # Generic try-catch blocks
            elif 'try {' in line_stripped:
                rules.append("Error handling: Begin transaction/operation with exception management")

            # Generic mathematical/financial calculations
            elif ('=' in line_stripped and
                  (any(math_indicator in line_stripped for math_indicator in ['.multiply(', '.add(', '.subtract(', '.divide(', '*', '+', '-', '/', 'Math.']) or
                   'BigDecimal' in line_stripped or 'Decimal' in line_stripped)):

                # Get variable being assigned
                var_name = line_stripped.split('=')[0].strip()
                calculation = line_stripped.split('=')[1].strip().rstrip(';')

                # Show actual calculation with real variable names
                if 'BigDecimal' in calculation:
                    # Parse complex BigDecimal operations to show meaningful patterns
                    if '.multiply(' in calculation and '.subtract(' in calculation:
                        # Handle nested BigDecimal operations like: (new BigDecimal(quantity).multiply(price)).subtract(orderFee)
                        # Extract variable names from the calculation
                        multiply_match = re.search(r'BigDecimal\((\w+)\)\.multiply\((\w+)\)', calculation)
                        subtract_match = re.search(r'\.subtract\((\w+)\)', calculation)

                        if multiply_match and subtract_match:
                            var1 = multiply_match.group(1)
                            var2 = multiply_match.group(2)
                            var3 = subtract_match.group(1)
                            context = self._get_meaningful_context(lines, i, 2, 1)
                            rules.append(f"Calculation rule: {var_name} = ({var1} * {var2}) - {var3} [BigDecimal precision]\nContext:\n{context}")
                        else:
                            # Fallback to simplified view
                            simplified = re.sub(r'new BigDecimal\((\w+)\)', r'\1', calculation)
                            simplified = simplified.replace('.multiply(', ' * ').replace('.subtract(', ' - ').replace(')', '')
                            context = self._get_meaningful_context(lines, i, 1, 1)
                            rules.append(f"Calculation rule: {var_name} = {simplified} [BigDecimal precision]\nContext:\n{context}")

                    elif '.multiply(' in calculation:
                        multiply_match = re.search(r'BigDecimal\((\w+)\)\.multiply\((\w+)\)', calculation)
                        if multiply_match:
                            var1 = multiply_match.group(1)
                            var2 = multiply_match.group(2)
                            rules.append(f"Calculation rule: {var_name} = {var1} * {var2} [BigDecimal precision]")
                        else:
                            simplified = re.sub(r'new BigDecimal\((\w+)\)', r'\1', calculation)
                            simplified = simplified.replace('.multiply(', ' * ').replace(')', '')
                            rules.append(f"Calculation rule: {var_name} = {simplified}")

                    elif '.add(' in calculation:
                        add_match = re.search(r'(\w+)\.add\((\w+)\)', calculation)
                        if add_match:
                            var1 = add_match.group(1)
                            var2 = add_match.group(2)
                            rules.append(f"Calculation rule: {var_name} = {var1} + {var2} [BigDecimal precision]")
                        else:
                            simplified = calculation.replace('.add(', ' + ').replace(')', '')
                            rules.append(f"Calculation rule: {var_name} = {simplified}")

                    elif '.subtract(' in calculation:
                        subtract_match = re.search(r'(\w+)\.subtract\((\w+)\)', calculation)
                        if subtract_match:
                            var1 = subtract_match.group(1)
                            var2 = subtract_match.group(2)
                            rules.append(f"Calculation rule: {var_name} = {var1} - {var2} [BigDecimal precision]")
                        else:
                            simplified = calculation.replace('.subtract(', ' - ').replace(')', '')
                            rules.append(f"Calculation rule: {var_name} = {simplified}")
                    else:
                        rules.append(f"Calculation rule: {var_name} = {calculation[:60]}... [BigDecimal precision]")

                elif any(op in calculation for op in ['*', '/', '+', '-']):
                    rules.append(f"Calculation rule: {var_name} = {calculation}")
                else:
                    rules.append(f"Assignment rule: {var_name} = {calculation[:50]}...")

            # Generic data assignment patterns
            elif ('=' in line_stripped and
                  any(data_pattern in line_stripped for data_pattern in ['.get(', 'new ', '.find(', '.create('])):

                var_name = line_stripped.split('=')[0].strip()
                assignment = line_stripped.split('=')[1].strip().rstrip(';')

                if '.get(' in assignment:
                    rules.append(f"Data access: Retrieve {var_name} from existing object")
                elif '.find(' in assignment:
                    rules.append(f"Data retrieval: Query {var_name} from data source")
                elif 'new ' in assignment:
                    rules.append(f"Object creation: Initialize new {var_name}")
                elif '.create(' in assignment:
                    rules.append(f"Factory method: Create {var_name} using business logic")
                else:
                    rules.append(f"Data assignment: Set {var_name} = {assignment[:30]}...")

            # Generic state update patterns with context
            elif ('set' in line_stripped.lower() and '(' in line_stripped):
                method_match = re.search(r'\.(\w*set\w*)\s*\(([^)]*)\)', line_stripped, re.IGNORECASE)
                if method_match:
                    method_name = method_match.group(1)
                    parameter = method_match.group(2).strip().strip('"\'')
                    context = self._get_meaningful_context(lines, i, 1, 1)

                    # Generic state update descriptions with context
                    property_name = method_name.replace('set', '').replace('Set', '')
                    if '.add(' in parameter:
                        rules.append(f"State update: Increment {property_name} by adding {parameter}\nContext:\n{context}")
                    elif '.subtract(' in parameter:
                        rules.append(f"State update: Decrement {property_name} by subtracting {parameter}\nContext:\n{context}")
                    elif parameter.startswith('"') and parameter.endswith('"'):
                        rules.append(f"State update: Set {property_name} to '{parameter.strip('\"')}'\nContext:\n{context}")
                    else:
                        rules.append(f"State update: Set {property_name} = {parameter}\nContext:\n{context}")

            # Generic database/persistence operations
            elif any(op in line_stripped.lower() for op in ['persist', 'remove', 'find', 'merge', 'save', 'delete']):
                persistence_match = re.search(r'(\w+)\.(persist|remove|find|merge|save|delete)', line_stripped, re.IGNORECASE)
                if persistence_match:
                    operation = persistence_match.group(2).lower()
                    if operation in ['persist', 'save']:
                        rules.append("Persistence rule: Save object to data store")
                    elif operation in ['remove', 'delete']:
                        rules.append("Persistence rule: Delete object from data store")
                    elif operation == 'find':
                        rules.append("Data access rule: Query object from data store")
                    elif operation == 'merge':
                        rules.append("Persistence rule: Update existing object in data store")

            # Generic method invocation patterns with context
            elif (re.search(r'\w+\s*\([^)]*\)', line_stripped) and
                  any(action_word in line_stripped.lower() for action_word in
                      ['complete', 'queue', 'process', 'execute', 'handle', 'manage', 'validate', 'verify'])):

                method_match = re.search(r'(\w+)\s*\(([^)]*)\)', line_stripped)
                if method_match:
                    method_name = method_match.group(1)
                    args = method_match.group(2)
                    context = self._get_meaningful_context(lines, i, 1, 1)

                    if any(keyword in method_name.lower() for keyword in ['complete', 'finish', 'finalize']):
                        rules.append(f"Workflow rule: {method_name}({args}) - Complete operation\nContext:\n{context}")
                    elif any(keyword in method_name.lower() for keyword in ['queue', 'enqueue', 'schedule']):
                        rules.append(f"Workflow rule: {method_name}({args}) - Queue for async processing\nContext:\n{context}")
                    elif any(keyword in method_name.lower() for keyword in ['validate', 'verify', 'check']):
                        rules.append(f"Validation rule: {method_name}({args}) - Verify constraints\nContext:\n{context}")
                    elif any(keyword in method_name.lower() for keyword in ['process', 'execute', 'handle']):
                        rules.append(f"Processing rule: {method_name}({args}) - Execute operation\nContext:\n{context}")
                    else:
                        rules.append(f"Business method: {method_name}({args})\nContext:\n{context}")

            # Generic conditional flow control
            elif ('if (' in line_stripped and
                  any(flow_pattern in line_stripped for flow_pattern in ['Mode', 'Config', 'Type', 'Status', '==', '!='])):

                condition_match = re.search(r'if\s*\(([^)]+)\)', line_stripped)
                if condition_match:
                    condition = condition_match.group(1).strip()
                    next_line = self._get_next_meaningful_lines(lines, i, 1)

                    if any(sync_pattern in condition for sync_pattern in ['SYNCH', 'SYNC', 'Synchronous']):
                        rules.append(f"Flow control: If synchronous mode -> execute immediately ({next_line[:30]}...)")
                    elif any(async_pattern in condition for async_pattern in ['ASYNCH', 'ASYNC', 'Asynchronous']):
                        rules.append(f"Flow control: If asynchronous mode -> defer execution ({next_line[:30]}...)")
                    elif 'Mode' in condition or 'Config' in condition:
                        rules.append(f"Configuration rule: Based on {condition} -> determine execution path")
                    else:
                        rules.append(f"Conditional rule: If {condition} -> execute specific logic")

        # Prioritize rules by importance before grouping
        if len(rules) > 1:
            priority_rules = []
            regular_rules = []

            # Separate high-priority rules (calculations, validations, workflow, conditions)
            for rule in rules:
                if any(priority_keyword in rule.lower() for priority_keyword in
                      ['calculation rule', 'validation rule', 'workflow rule', 'conditional rule', 'flow control', 'error handling']):
                    priority_rules.append(rule)
                else:
                    regular_rules.append(rule)

            # Combine with priority rules first
            all_rules = priority_rules + regular_rules

            # Group with separators
            grouped_rules = []
            for i in range(len(all_rules)):
                grouped_rules.append(all_rules[i])
                # Add separator after every 3 related rules
                if (i + 1) % 3 == 0 and i + 1 < len(all_rules):
                    grouped_rules.append("...")

            return grouped_rules[:10]  # Increased limit to capture more important rules

        return rules

    def _get_meaningful_context(self, lines: List[str], center_idx: int, before: int = 2, after: int = 2) -> str:
        """Get meaningful context around a line showing actual code structure"""
        context_lines = []
        start = max(0, center_idx - before)
        end = min(len(lines), center_idx + after + 1)

        for i in range(start, end):
            line = lines[i].strip()
            if not line or line.startswith('//'):
                continue

            # Indicate which line is the current focus
            if i == center_idx:
                context_lines.append(f">>> {line}")
            else:
                context_lines.append(f"    {line}")

        return '\n'.join(context_lines) if context_lines else ""

    def _get_next_meaningful_lines(self, lines: List[str], start_idx: int, count: int) -> str:
        """Get next meaningful lines after start_idx for context"""
        meaningful_lines = []
        for i in range(start_idx + 1, min(start_idx + count + 5, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('//') and line not in ['{', '}', '};']:
                meaningful_lines.append(line)
                if len(meaningful_lines) >= count:
                    break
        return '\n    '.join(meaningful_lines) if meaningful_lines else ""

    def _get_surrounding_context(self, lines: List[str], center_idx: int, radius: int) -> str:
        """Get context around a line for better understanding"""
        context_lines = []
        start = max(0, center_idx - radius)
        end = min(len(lines), center_idx + radius + 1)

        for i in range(start, end):
            if i == center_idx:
                continue  # Skip the center line itself
            line = lines[i].strip()
            if line and not line.startswith('//') and len(line) > 5:
                context_lines.append(line)

        return '\n    '.join(context_lines[:3]) if context_lines else "processing data"

    def _extract_java_business_rules(self, root_node, source_code: str) -> List[str]:
        """Extract business rules from Java AST"""
        rules = []
        source_lines = source_code.split('\n')

        def traverse_node(node, depth=0):
            # Extract business logic from different node types
            node_type = node.type

            # Java conditional logic rules with context
            if node_type == 'if_statement':
                condition = self._get_node_text(node.child_by_field_name('condition'), source_code)
                if condition and self._is_business_condition(condition):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 2)
                    rules.append(f"Validation rule: {condition.strip()}\nContext:\n{context}")

            # Java switch/case business rules with context
            elif node_type in ['switch_expression', 'switch_statement']:
                switch_expr = self._get_node_text(node.child_by_field_name('condition'), source_code)
                if switch_expr and self._is_business_related(switch_expr):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Business logic: Switch on {switch_expr.strip()}\nContext:\n{context}")

            # Java method invocation business rules with context
            elif node_type == 'method_invocation':
                method_name = self._get_method_name(node, source_code)
                if method_name and self._is_business_method(method_name):
                    args = self._get_method_arguments(node, source_code)
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rule_text = f"Business operation: {method_name}{args}\nContext:\n{context}" if args else f"Business operation: {method_name}()\nContext:\n{context}"
                    rules.append(rule_text)

            # Java assignment with business calculations and context
            elif node_type == 'assignment_expression':
                left = self._get_node_text(node.child_by_field_name('left'), source_code)
                right = self._get_node_text(node.child_by_field_name('right'), source_code)
                if left and right and (self._is_business_calculation(right) or self._is_business_variable(left)):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Calculation rule: {left.strip()} = {right.strip()}\nContext:\n{context}")

            # Java variable declarations with business significance and context
            elif node_type == 'variable_declarator':
                var_name = self._get_variable_name(node, source_code)
                initializer = node.child_by_field_name('value')
                if var_name and initializer and self._is_business_variable(var_name):
                    init_text = self._get_node_text(initializer, source_code)
                    if init_text:
                        line_num = source_code[:node.start_byte].count('\n')
                        context = self._get_context_from_source(source_lines, line_num, 1, 1)
                        rules.append(f"Data initialization: {var_name} = {init_text.strip()}\nContext:\n{context}")

            # Recursively traverse child nodes
            for child in node.children:
                traverse_node(child, depth + 1)

        traverse_node(root_node)

        # Split multiple logical sections with "..."
        if len(rules) > 3:
            # Group rules by logical sections (every 2-3 rules)
            grouped_rules = []
            for i in range(0, len(rules), 3):
                section = rules[i:i+3]
                grouped_rules.extend(section)
                if i + 3 < len(rules):  # Not the last section
                    grouped_rules.append("...")
            return grouped_rules

        return rules

    def _extract_csharp_business_rules(self, root_node, source_code: str) -> List[str]:
        """Extract business rules from C# AST"""
        rules = []
        source_lines = source_code.split('\n')

        def traverse_node(node, depth=0):
            node_type = node.type

            # C# conditional statements
            if node_type == 'if_statement':
                condition = self._get_node_text(node.child_by_field_name('condition'), source_code)
                if condition and self._is_business_condition(condition):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 2)
                    rules.append(f"Validation rule: {condition.strip()}\nContext:\n{context}")

            # C# switch expressions/statements
            elif node_type in ['switch_statement', 'switch_expression']:
                switch_expr = self._get_node_text(node.child_by_field_name('value'), source_code)
                if switch_expr and self._is_business_related(switch_expr):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Business logic: Switch on {switch_expr.strip()}\nContext:\n{context}")

            # C# method invocations
            elif node_type == 'invocation_expression':
                method_node = node.child_by_field_name('function')
                if method_node:
                    method_name = self._get_node_text(method_node, source_code)
                    if method_name and self._is_business_method(method_name):
                        args_node = node.child_by_field_name('arguments')
                        args = self._get_node_text(args_node, source_code) if args_node else "()"
                        line_num = source_code[:node.start_byte].count('\n')
                        context = self._get_context_from_source(source_lines, line_num, 1, 1)
                        rules.append(f"Business operation: {method_name}{args}\nContext:\n{context}")

            # C# assignment expressions
            elif node_type == 'assignment_expression':
                left = self._get_node_text(node.child_by_field_name('left'), source_code)
                right = self._get_node_text(node.child_by_field_name('right'), source_code)
                if left and right and (self._is_business_calculation(right) or self._is_business_variable(left)):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Calculation rule: {left.strip()} = {right.strip()}\nContext:\n{context}")

            # C# variable declarations
            elif node_type == 'variable_declarator':
                name_node = node.child_by_field_name('name')
                value_node = node.child_by_field_name('value')
                if name_node and value_node:
                    var_name = self._get_node_text(name_node, source_code)
                    init_value = self._get_node_text(value_node, source_code)
                    if var_name and init_value and self._is_business_variable(var_name):
                        line_num = source_code[:node.start_byte].count('\n')
                        context = self._get_context_from_source(source_lines, line_num, 1, 1)
                        rules.append(f"Data initialization: {var_name} = {init_value.strip()}\nContext:\n{context}")

            # Recursively traverse child nodes
            for child in node.children:
                traverse_node(child, depth + 1)

        traverse_node(root_node)

        # Group rules by logical sections with separators
        if len(rules) > 3:
            grouped_rules = []
            for i in range(0, len(rules), 3):
                section = rules[i:i+3]
                grouped_rules.extend(section)
                if i + 3 < len(rules):
                    grouped_rules.append("...")
            return grouped_rules[:10]

        return rules

    def _extract_php_business_rules(self, root_node, source_code: str) -> List[str]:
        """Extract business rules from PHP AST"""
        rules = []
        source_lines = source_code.split('\n')

        def traverse_node(node, depth=0):
            node_type = node.type

            # PHP conditional statements
            if node_type == 'if_statement':
                condition = self._get_node_text(node.child_by_field_name('condition'), source_code)
                if condition and self._is_business_condition(condition):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 2)
                    rules.append(f"Validation rule: {condition.strip()}\nContext:\n{context}")

            # PHP switch statements
            elif node_type == 'switch_statement':
                switch_expr = self._get_node_text(node.child_by_field_name('value'), source_code)
                if switch_expr and self._is_business_related(switch_expr):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Business logic: Switch on {switch_expr.strip()}\nContext:\n{context}")

            # PHP function calls
            elif node_type == 'function_call_expression':
                function_node = node.child_by_field_name('function')
                if function_node:
                    function_name = self._get_node_text(function_node, source_code)
                    if function_name and self._is_business_method(function_name):
                        args_node = node.child_by_field_name('arguments')
                        args = self._get_node_text(args_node, source_code) if args_node else "()"
                        line_num = source_code[:node.start_byte].count('\n')
                        context = self._get_context_from_source(source_lines, line_num, 1, 1)
                        rules.append(f"Business operation: {function_name}{args}\nContext:\n{context}")

            # PHP assignment expressions
            elif node_type == 'assignment_expression':
                left = self._get_node_text(node.child_by_field_name('left'), source_code)
                right = self._get_node_text(node.child_by_field_name('right'), source_code)
                if left and right and (self._is_business_calculation(right) or self._is_business_variable(left)):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Calculation rule: {left.strip()} = {right.strip()}\nContext:\n{context}")

            # PHP variable declarations (with assignment)
            elif node_type == 'simple_assignment':
                left = self._get_node_text(node.child_by_field_name('left'), source_code)
                right = self._get_node_text(node.child_by_field_name('right'), source_code)
                if left and right and (self._is_business_variable(left) or self._is_business_calculation(right)):
                    line_num = source_code[:node.start_byte].count('\n')
                    context = self._get_context_from_source(source_lines, line_num, 1, 1)
                    rules.append(f"Data assignment: {left.strip()} = {right.strip()}\nContext:\n{context}")

            # Recursively traverse child nodes
            for child in node.children:
                traverse_node(child, depth + 1)

        traverse_node(root_node)

        # Group rules by logical sections with separators
        if len(rules) > 3:
            grouped_rules = []
            for i in range(0, len(rules), 3):
                section = rules[i:i+3]
                grouped_rules.extend(section)
                if i + 3 < len(rules):
                    grouped_rules.append("...")
            return grouped_rules[:10]

        return rules

    def _get_context_from_source(self, source_lines: List[str], center_line: int, before: int, after: int) -> str:
        """Get context around a specific line number in source code"""
        context_lines = []
        start = max(0, center_line - before)
        end = min(len(source_lines), center_line + after + 1)

        for i in range(start, end):
            line = source_lines[i].strip()
            if not line or line.startswith('//'):
                continue

            if i == center_line:
                context_lines.append(f">>> {line}")
            else:
                context_lines.append(f"    {line}")

        return '\n'.join(context_lines) if context_lines else ""

    def _get_node_text(self, node, source_code: str) -> Optional[str]:
        """Get text content of a node"""
        if node is None:
            return None
        try:
            return source_code[node.start_byte:node.end_byte]
        except:
            return None

    def _get_method_name(self, method_node, source_code: str) -> Optional[str]:
        """Extract method name from method invocation node"""
        name_node = method_node.child_by_field_name('name')
        if name_node:
            return self._get_node_text(name_node, source_code)
        return None

    def _get_method_arguments(self, method_node, source_code: str) -> str:
        """Extract method arguments as string"""
        args_node = method_node.child_by_field_name('arguments')
        if args_node:
            return self._get_node_text(args_node, source_code)
        return ""

    def _get_variable_name(self, var_node, source_code: str) -> Optional[str]:
        """Extract variable name from variable declarator"""
        name_node = var_node.child_by_field_name('name')
        if name_node:
            return self._get_node_text(name_node, source_code)
        return None

    def _is_business_condition(self, condition: str) -> bool:
        """Check if a condition represents business logic (generic patterns)"""
        business_patterns = [
            r'\b(?:amount|value|total|count|size|length|limit|threshold)\b',
            r'\b(?:status|state|type|mode|flag|enabled|disabled)\s*[=!<>]',
            r'\b(?:valid|invalid|allowed|denied|approved|rejected|active|inactive)\b',
            r'\b(?:minimum|maximum|min|max|limit|threshold|boundary)\b',
            r'\b(?:is\w+|can\w+|has\w+|should\w+)\b',
            r'== null|!= null|\bequals\(',
            r'>\s*0|<\s*0|>=\s*\d+|<=\s*\d+'
        ]
        return any(re.search(pattern, condition, re.IGNORECASE) for pattern in business_patterns)

    def _is_business_related(self, text: str) -> bool:
        """Check if text is business-related (generic patterns)"""
        business_keywords = [
            'status', 'state', 'mode', 'type', 'config', 'setting',
            'data', 'entity', 'model', 'object', 'item', 'record',
            'user', 'client', 'customer', 'request', 'response'
        ]
        return any(keyword in text.lower() for keyword in business_keywords)

    def _is_business_method(self, method_name: str) -> bool:
        """Check if method name indicates business logic (generic patterns)"""
        business_method_patterns = [
            r'(?:calculate|compute|process|validate|verify|check|ensure|confirm)',
            r'(?:create|build|generate|make|construct|initialize)',
            r'(?:update|modify|change|set|assign|configure)',
            r'(?:delete|remove|clear|reset|cleanup)',
            r'(?:save|persist|store|insert|upsert)',
            r'(?:load|fetch|retrieve|get|find|search|query)',
            r'(?:send|publish|emit|notify|trigger|fire)',
            r'(?:handle|manage|execute|perform|run|start|stop)',
            r'(?:login|logout|register|authenticate|authorize)',
            r'(?:approve|reject|cancel|complete|finish|close)',
            r'(?:transform|convert|parse|format|serialize)'
        ]
        return any(re.search(pattern, method_name, re.IGNORECASE) for pattern in business_method_patterns)

    def _is_business_calculation(self, expression: str) -> bool:
        """Check if expression represents business calculation (generic patterns)"""
        calculation_patterns = [
            r'(?:total|amount|sum|count|value|result|output)\s*[+\-*/%]',
            r'(?:BigDecimal|Decimal|Money|Currency)\s*\.\s*(?:add|subtract|multiply|divide)',
            r'Math\s*\.\s*(?:round|ceil|floor|abs|pow|sqrt|max|min)',
            r'(?:calculate|compute|sum|aggregate)\w*\s*\(',
            r'\d+\s*[*/%]\s*\d+',
            r'[+\-*/]\s*(?:rate|factor|multiplier|coefficient)',
            r'(?:precision|scale|rounding)',
            r'[+\-*/=]\s*(?:fee|cost|charge|penalty|bonus|discount)'
        ]
        return any(re.search(pattern, expression, re.IGNORECASE) for pattern in calculation_patterns)

    def _is_business_variable(self, var_name: str) -> bool:
        """Check if variable name indicates business data (generic patterns)"""
        business_var_patterns = [
            r'(?:total|amount|sum|count|value|result|output|input)',
            r'(?:data|entity|model|object|item|record|instance)',
            r'(?:user|client|customer|person|account|profile)',
            r'(?:status|state|type|mode|flag|config|setting)',
            r'(?:id|key|index|identifier|reference|handle)',
            r'(?:list|collection|array|set|map|dictionary)',
            r'(?:response|request|message|event|notification)',
            r'(?:error|exception|result|outcome|success|failure)'
        ]
        return any(re.search(pattern, var_name, re.IGNORECASE) for pattern in business_var_patterns)


class BaseBusinessLogicAnalyzer(ABC):
    """Abstract base class for language-specific business logic analyzers"""

    def __init__(self):
        # Common control flow patterns across languages
        self.control_flow_patterns = {
            'complex_conditional': [],
            'iteration_logic': [],
            'exception_handling': [],
            'synchronization': []
        }

        # Common business domain patterns
        self.business_domain_patterns = {
            'financial_calculations': [],
            'transaction_management': [],
            'data_processing': [],
            'state_management': [],
            'validation_logic': [],
            'integration_patterns': []
        }

        # Common business rule patterns
        self.business_rule_patterns = {
            'authorization_security': [],
            'business_calculations': [],
            'workflow_orchestration': []
        }

        # Static patterns
        self.static_patterns = {
            'financial_constants': [],
            'business_thresholds': [],
            'configuration_constants': [],
            'static_initialization': []
        }

    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """Return supported file extensions for this language"""
        pass

    @abstractmethod
    def extract_class_name(self, file_content: List[str], file_path: str) -> str:
        """Extract class name from file content"""
        pass

    @abstractmethod
    def extract_static_elements(self, file_content: List[str], file_path: str, class_name: str) -> List[StaticBusinessRule]:
        """Extract static variables, constants, and initialization blocks"""
        pass

    def calculate_cyclomatic_complexity(self, method_body: str) -> int:
        """Calculate cyclomatic complexity based on decision points"""
        complexity = 1  # Base complexity

        # Decision point patterns (common across languages)
        decision_patterns = [
            r'\bif\b',
            r'\bfor\b',
            r'\bwhile\b',
            r'\bcase\b',
            r'\bcatch\b',
            r'\?\s*[^:]+\s*:',  # Ternary operator
            r'&&',
            r'\|\|'
        ]

        for pattern in decision_patterns:
            matches = len(re.findall(pattern, method_body))
            complexity += matches

        return complexity

    def analyze_control_flow_complexity(self, method_body: str) -> Tuple[int, List[BusinessLogicSnippet]]:
        """Enhanced control flow analysis with context awareness"""
        complexity_score = 0
        snippets = []
        method_lines = method_body.split('\n')

        for category, patterns in self.control_flow_patterns.items():
            for pattern, description, weight in patterns:
                matches = list(re.finditer(pattern, method_body, re.DOTALL | re.IGNORECASE))
                for match in matches:
                    complexity_score += weight

                    match_start = method_body[:match.start()].count('\n') + 1
                    match_end = method_body[:match.end()].count('\n') + 1

                    context_start = max(0, match_start - 3)
                    context_end = min(len(method_lines), match_end + 2)
                    context_lines = method_lines[context_start:context_end]
                    context_text = '\n'.join(line.strip() for line in context_lines if line.strip())

                    snippet_text = match.group(0)[:200]

                    snippets.append(BusinessLogicSnippet(
                        type=category,
                        description=description,
                        pattern_matched=pattern[:50],
                        code_lines=f"Lines {match_start}-{match_end}",
                        snippet=snippet_text,
                        confidence=0.85,
                        importance=weight,
                        context=context_text
                    ))

        return complexity_score, snippets

    def analyze_business_domain(self, method_body: str) -> Tuple[int, List[BusinessLogicSnippet]]:
        """Enhanced business domain analysis with better pattern matching"""
        domain_score = 0
        snippets = []
        method_lines = method_body.split('\n')

        for category, patterns in self.business_domain_patterns.items():
            for pattern, description, weight in patterns:
                matches = list(re.finditer(pattern, method_body, re.DOTALL | re.IGNORECASE))
                for match in matches:
                    domain_score += weight

                    match_start = method_body[:match.start()].count('\n') + 1
                    match_end = method_body[:match.end()].count('\n') + 1

                    context_start = max(0, match_start - 2)
                    context_end = min(len(method_lines), match_end + 2)
                    context_lines = method_lines[context_start:context_end]
                    context_text = '\n'.join(line.strip() for line in context_lines if line.strip())

                    snippet_text = match.group(0)[:200]

                    snippets.append(BusinessLogicSnippet(
                        type=category,
                        description=description,
                        pattern_matched=pattern[:50],
                        code_lines=f"Lines {match_start}-{match_end}",
                        snippet=snippet_text,
                        confidence=0.9,
                        importance=weight,
                        context=context_text
                    ))

        return domain_score, snippets

    def analyze_business_rules(self, method_body: str) -> List[BusinessLogicSnippet]:
        """Enhanced business rule analysis"""
        snippets = []
        method_lines = method_body.split('\n')

        for category, patterns in self.business_rule_patterns.items():
            for pattern, description, weight in patterns:
                matches = list(re.finditer(pattern, method_body, re.DOTALL | re.IGNORECASE))
                for match in matches:
                    match_start = method_body[:match.start()].count('\n') + 1
                    match_end = method_body[:match.end()].count('\n') + 1

                    context_start = max(0, match_start - 2)
                    context_end = min(len(method_lines), match_end + 2)
                    context_lines = method_lines[context_start:context_end]
                    context_text = '\n'.join(line.strip() for line in context_lines if line.strip())

                    snippet_text = match.group(0)[:200]

                    snippets.append(BusinessLogicSnippet(
                        type=category,
                        description=description,
                        pattern_matched=pattern[:50],
                        code_lines=f"Lines {match_start}-{match_end}",
                        snippet=snippet_text,
                        confidence=0.88,
                        importance=weight,
                        context=context_text
                    ))

        return snippets

    def calculate_static_complexity(self, code_snippet: str, significance: str) -> int:
        """Calculate complexity score for static elements"""
        score = 10  # Base score for static elements

        # Add points for business keywords
        business_keywords = ['PRICE', 'RATE', 'FEE', 'TAX', 'COMMISSION', 'BALANCE',
                            'MAXIMUM', 'MINIMUM', 'THRESHOLD', 'LIMIT', 'AMOUNT']
        for keyword in business_keywords:
            if keyword in code_snippet.upper():
                score += 3

        # Add points based on significance
        if 'Financial' in significance:
            score += 10
        elif 'initialization' in significance:
            score += 8
        elif 'Business rule' in significance:
            score += 7

        return min(50, score)  # Cap at 50 for static elements

    def calculate_complexity_score(self, control_flow_score: int, domain_score: int,
                                 num_snippets: int, method_length: int,
                                 cyclomatic_complexity: int, has_annotations: bool) -> int:
        """Enhanced complexity scoring algorithm"""
        base_score = control_flow_score + domain_score

        import math
        cyclomatic_bonus = min(20, cyclomatic_complexity * 2)
        length_bonus = min(15, int(math.log(method_length + 1) * 3))
        snippet_bonus = min(10, num_snippets)
        annotation_bonus = 5 if has_annotations else 0

        total_score = (
            base_score * 1.0 +
            cyclomatic_bonus * 0.8 +
            length_bonus * 0.5 +
            snippet_bonus * 0.7 +
            annotation_bonus * 0.6
        )

        return min(100, int(total_score))


class JavaBusinessLogicAnalyzerV4(BaseBusinessLogicAnalyzer):
    """Advanced analyzer for Java business logic patterns - Version 4 with static analysis
    PRESERVES ALL EXISTING JAVA FUNCTIONALITY"""

    def __init__(self):
        super().__init__()

        # Java-specific control flow patterns - PRESERVED FROM ORIGINAL
        self.control_flow_patterns = {
            'complex_conditional': [
                (r'if\s*\([^)]+\)\s*\{[^}]*\}\s*else\s+if\s*\([^)]+\)\s*\{[^}]*\}\s*else', 'Complex if-else-if chain', 4),
                (r'if\s*\([^)]+\)\s*\{(?:[^{}]*\{[^{}]*\})*[^}]*\}', 'Nested conditional logic', 5),
                (r'switch\s*\([^)]+\)\s*\{(?:[^}]*case\s+[^:]*:[^}]*){3,}', 'Complex switch with multiple cases', 4),
                (r'if\s*\([^)]*(?:&&|\|\|)[^)]*(?:&&|\|\|)[^)]*\)', 'Complex compound conditions', 3),
                (r'if\s*\([^)]*\)\s*\{[^}]*if\s*\([^)]*\)\s*\{', 'Nested if statements', 3),
            ],
            'iteration_logic': [
                (r'for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)\s*\{', 'Nested loops', 6),
                (r'while\s*\([^)]+\)\s*\{[^}]*(?:break|continue)', 'Complex while loop with flow control', 3),
                (r'\.stream\(\).*?\.(?:filter|map|reduce|collect)', 'Stream processing pipeline', 3),
                (r'do\s*\{[^}]*\}\s*while\s*\([^)]+\)', 'Do-while loop', 2),
                (r'for\s*\([^:]*:\s*[^)]+\)\s*\{[^}]*if', 'Enhanced for loop with conditions', 2),
            ],
            'exception_handling': [
                (r'try\s*\{[^}]*\}\s*catch\s*\([^)]+\)\s*\{[^}]*\}\s*catch', 'Multiple exception handlers', 5),
                (r'try\s*\{[^}]*try\s*\{', 'Nested try blocks', 4),
                (r'throw\s+new\s+\w*(?:Business|Validation|Domain)\w*Exception', 'Domain-specific exception', 4),
                (r'catch\s*\([^)]+\)\s*\{[^}]*throw', 'Exception transformation', 3),
                (r'finally\s*\{[^}]*(?:close|release|cleanup)', 'Resource cleanup in finally', 3),
            ],
            'synchronization': [
                (r'synchronized\s*\([^)]+\)\s*\{[^}]*synchronized', 'Nested synchronization', 5),
                (r'ReentrantLock|ReadWriteLock|Semaphore', 'Advanced concurrency control', 4),
                (r'volatile\s+\w+', 'Volatile field access', 2),
                (r'CompletableFuture.*?\.(?:thenApply|thenCompose|allOf)', 'Async composition', 3),
                (r'@Async.*?public\s+\w+', 'Asynchronous method', 3),
            ]
        }

        # Java-specific business domain patterns - PRESERVED FROM ORIGINAL
        self.business_domain_patterns = {
            'financial_calculations': [
                (r'BigDecimal.*?\.(?:add|subtract|multiply|divide)\([^)]*\).*?\.setScale', 'Precise financial calculation with rounding', 5),
                (r'(?:calculate|compute)(?:Price|Total|Tax|Fee|Commission|Interest|Balance)', 'Financial calculation method', 5),
                (r'(?:price|amount|total|balance)\s*=.*?(?:price|amount|rate|quantity)', 'Financial formula', 4),
                (r'NumberFormat\.getCurrencyInstance|Currency\.getInstance', 'Currency formatting', 3),
                (r'(?:ROUND_HALF_UP|ROUND_DOWN|ROUND_CEILING)', 'Financial rounding mode', 3),
            ],
            'transaction_management': [
                (r'@Transactional\s*\(.*?(?:isolation|propagation|rollback)', 'Complex transaction configuration', 5),
                (r'(?:begin|start|commit|rollback)Transaction', 'Explicit transaction management', 5),
                (r'(?:buy|sell|trade|order|purchase|transfer|withdraw|deposit)\s*\([^)]*\)', 'Trading/Banking operation', 5),
                (r'TransactionTemplate|PlatformTransactionManager', 'Spring transaction management', 4),
                (r'savepoint|setSavepoint|releaseSavepoint', 'Transaction savepoint management', 4),
            ],
            'data_processing': [
                (r'SELECT.*?(?:JOIN|GROUP BY|HAVING|UNION)', 'Complex SQL query', 4),
                (r'CriteriaBuilder|CriteriaQuery|Specification', 'JPA Criteria API', 4),
                (r'@Query\s*\([^)]*(?:nativeQuery|value)', 'Custom query annotation', 3),
                (r'\.(?:findBy|deleteBy|countBy)[A-Z]\w+', 'Spring Data method', 3),
                (r'Pageable|PageRequest|Sort\.by', 'Pagination and sorting', 3),
            ],
            'state_management': [
                (r'StateMachine|StateContext|StateTransition', 'State machine implementation', 5),
                (r'(?:PENDING|PROCESSING|COMPLETED|FAILED|CANCELLED)', 'Status state management', 4),
                (r'workflow\.(?:start|advance|complete|cancel|transition)', 'Workflow operations', 4),
                (r'setStatus\s*\(\s*\w+\.\w+', 'Status assignment', 3),
                (r'enum\s+\w*State\s*\{', 'State enumeration definition', 3),
                (r'transition(?:To|From).*?State', 'State transition method', 4),
            ],
            'validation_logic': [
                (r'@Valid(?:ated)?|@(?:NotNull|NotEmpty|Size|Pattern|Range|Min|Max)', 'Bean validation annotations', 3),
                (r'(?:validate|verify|check|ensure|assert)[A-Z]\w+\s*\([^)]*\)', 'Validation method call', 4),
                (r'if\s*\([^)]*(?:isValid|isAllowed|canPerform|hasPermission)', 'Validation conditional', 4),
                (r'ValidationException|ConstraintViolation|BindingResult', 'Validation framework usage', 3),
                (r'Validator\.validate|BindingResult\.hasErrors', 'Validation execution', 4),
            ],
            'integration_patterns': [
                (r'@(?:RestController|RequestMapping|GetMapping|PostMapping)', 'REST endpoint', 3),
                (r'RestTemplate|WebClient|HttpClient', 'HTTP client usage', 3),
                (r'@(?:MessageMapping|SendTo|JmsListener|KafkaListener)', 'Message handling', 4),
                (r'(?:publish|send|emit)(?:Event|Message|Notification)', 'Event publishing', 4),
                (r'@EventListener|ApplicationEventPublisher', 'Event-driven architecture', 4),
            ]
        }

        # Java-specific business rule patterns - PRESERVED FROM ORIGINAL
        self.business_rule_patterns = {
            'authorization_security': [
                (r'@(?:PreAuthorize|PostAuthorize|Secured|RolesAllowed)', 'Method-level security', 4),
                (r'SecurityContext(?:Holder)?\.getContext|Authentication\s+', 'Security context access', 3),
                (r'hasRole\([^)]+\)|hasAuthority\([^)]+\)|hasPermission\([^)]+\)', 'Permission checking', 4),
                (r'@WithMockUser|@WithUserDetails', 'Security testing annotations', 2),
                (r'BCrypt|PasswordEncoder|MessageDigest', 'Cryptographic operations', 3),
            ],
            'business_calculations': [
                (r'(?:rate|percentage|discount|markup|margin)\s*[*/%]\s*', 'Rate/percentage calculation', 4),
                (r'(?:commission|fee|penalty|interest)\s*=.*?(?:calculate|compute)', 'Business fee calculation', 5),
                (r'Math\.(?:round|ceil|floor|abs).*?(?:price|amount|total)', 'Financial rounding', 3),
                (r'(?:minimum|maximum|threshold|limit).*?[<>]=?.*?(?:amount|quantity)', 'Business threshold check', 4),
                (r'TaxCalculator|FeeCalculator|PriceCalculator', 'Calculator component usage', 4),
            ],
            'workflow_orchestration': [
                (r'@(?:Saga|Compensate|SagaOrchestrationStart|SagaOrchestrationEnd)', 'Saga pattern', 5),
                (r'(?:approve|reject|escalate|delegate|assign)\w*\s*\([^)]*\)', 'Approval workflow', 4),
                (r'TaskScheduler|@Scheduled|CronExpression', 'Scheduled task execution', 3),
                (r'(?:retry|backoff|circuit).*?(?:Policy|Strategy|Breaker)', 'Resilience patterns', 4),
                (r'CompensatingTransaction|rollback(?:Transaction|Operation)', 'Compensation logic', 5),
            ]
        }

        # Java-specific static patterns - PRESERVED FROM ORIGINAL
        self.static_patterns = {
            'financial_constants': [
                (r'(?:static|final).*?BigDecimal\s+\w*(?:PRICE|RATE|FEE|TAX|AMOUNT|BALANCE|LIMIT|MAXIMUM|MINIMUM)',
                 'Financial constant declaration', 5),
                (r'(?:static|final).*?(?:double|float)\s+\w*(?:RATE|PERCENTAGE|FACTOR|MULTIPLIER)',
                 'Rate/percentage constant', 4),
                (r'new\s+BigDecimal\s*\([^)]+\).*?setScale', 'Precise decimal initialization', 4),
            ],
            'business_thresholds': [
                (r'(?:static|final).*?(?:int|long|Integer|Long)\s+\w*(?:MAX|MIN|LIMIT|THRESHOLD|COUNT)',
                 'Business limit constant', 4),
                (r'(?:static|final).*?(?:MAXIMUM|MINIMUM|DEFAULT)_\w+', 'Threshold constant', 3),
            ],
            'configuration_constants': [
                (r'(?:static|final).*?String\s+\w*(?:CONFIG|SETTING|PARAMETER|PROPERTY)',
                 'Configuration constant', 3),
                (r'(?:static|final).*?boolean\s+\w*(?:ENABLE|DISABLE|ALLOW)',
                 'Feature flag constant', 3),
            ],
            'static_initialization': [
                (r'static\s*\{[^}]*\}', 'Static initialization block', 4),
                (r'static\s*\{[^}]*(?:BigDecimal|initialize|setup|config)', 'Business logic initialization', 5),
            ]
        }

    def get_file_extensions(self) -> List[str]:
        return ['.java', '.jsp', '.jsf']

    def extract_class_name(self, file_content: List[str], file_path: str) -> str:
        """Extract Java class name from file content"""
        content = '\n'.join(file_content)

        # Java class declaration patterns
        class_patterns = [
            r'\bclass\s+([A-Z]\w+)\s*(?:\{|extends|implements)',
            r'\binterface\s+([A-Z]\w+)\s*(?:\{|extends)',
            r'\benum\s+([A-Z]\w+)\s*\{',
            r'public\s+(?:final\s+)?(?:abstract\s+)?class\s+([A-Z]\w+)',
            r'(?:public|private|protected)\s+class\s+([A-Z]\w+)'
        ]

        for pattern in class_patterns:
            match = re.search(pattern, content)
            if match:
                class_name = match.group(1)
                if class_name and class_name[0].isupper() and class_name not in ['String', 'Object', 'Integer', 'Boolean']:
                    return class_name

        # Fallback to filename
        filename = Path(file_path).stem
        if filename and filename[0].isupper():
            return filename

        return "UnknownClass"

    def extract_static_elements(self, file_content: List[str], file_path: str, class_name: str) -> List[StaticBusinessRule]:
        """Extract Java static variables, constants, and initialization blocks - PRESERVED FROM ORIGINAL"""
        static_rules = []
        content = '\n'.join(file_content)

        # Extract static variables and constants
        static_var_pattern = r'(?:public|private|protected)?\s*(?:static|final|static\s+final)\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=\s*([^;]+))?;'
        for match in re.finditer(static_var_pattern, content):
            data_type = match.group(1)
            var_name = match.group(2)
            initial_value = match.group(3) if match.group(3) else 'uninitialized'

            # Check if it's a business-relevant constant
            is_business_relevant = False
            significance = ""

            if 'BigDecimal' in data_type:
                is_business_relevant = True
                significance = "Financial precision constant"
            elif any(keyword in var_name.upper() for keyword in
                    ['PRICE', 'RATE', 'FEE', 'TAX', 'AMOUNT', 'BALANCE', 'LIMIT',
                     'MAXIMUM', 'MINIMUM', 'THRESHOLD', 'COMMISSION', 'MULTIPLIER']):
                is_business_relevant = True
                significance = "Business rule constant"
            elif any(keyword in var_name.upper() for keyword in
                    ['MAX', 'MIN', 'LIMIT', 'THRESHOLD', 'COUNT', 'SIZE']):
                is_business_relevant = True
                significance = "Business threshold constant"
            elif 'final' in match.group(0) and any(keyword in var_name.upper() for keyword in
                    ['CONFIG', 'SETTING', 'DEFAULT', 'TIMEOUT', 'RETRY']):
                is_business_relevant = True
                significance = "Configuration constant"

            if is_business_relevant:
                line_num = content[:match.start()].count('\n') + 1
                static_rules.append(StaticBusinessRule(
                    rule_type='static_constant' if 'final' in match.group(0) else 'static_variable',
                    name=var_name,
                    data_type=data_type,
                    value=initial_value.strip() if initial_value else '',
                    code_snippet=match.group(0),
                    file_path=file_path,
                    class_name=class_name,
                    lines=f"{line_num}",
                    business_significance=significance,
                    complexity_score=self.calculate_static_complexity(match.group(0), significance)
                ))

        # Extract static initialization blocks
        static_block_pattern = r'static\s*\{([^}]*)\}'
        for match in re.finditer(static_block_pattern, content, re.DOTALL):
            block_content = match.group(1)

            if any(pattern in block_content for pattern in
                   ['BigDecimal', 'setScale', 'initialize', 'setup', 'config',
                    'ROUND', 'multiply', 'divide', 'add', 'subtract']):
                line_num = content[:match.start()].count('\n') + 1
                static_rules.append(StaticBusinessRule(
                    rule_type='static_block',
                    name='static_initializer',
                    data_type='initialization_block',
                    value='',
                    code_snippet=match.group(0),
                    file_path=file_path,
                    class_name=class_name,
                    lines=f"{line_num}-{line_num + block_content.count(chr(10))}",
                    business_significance="Static business logic initialization",
                    complexity_score=self.calculate_static_complexity(match.group(0), "initialization")
                ))

        return static_rules

    def calculate_static_complexity(self, code_snippet: str, significance: str) -> int:
        """Calculate complexity score for Java static elements - PRESERVED FROM ORIGINAL"""
        score = 10  # Base score for static elements

        # Add points for financial elements
        if 'BigDecimal' in code_snippet:
            score += 15
        if 'setScale' in code_snippet:
            score += 10
        if any(op in code_snippet for op in ['multiply', 'divide', 'add', 'subtract']):
            score += 5

        # Add points for business keywords
        business_keywords = ['PRICE', 'RATE', 'FEE', 'TAX', 'COMMISSION', 'BALANCE',
                            'MAXIMUM', 'MINIMUM', 'THRESHOLD', 'LIMIT']
        for keyword in business_keywords:
            if keyword in code_snippet.upper():
                score += 3

        # Add points based on significance
        if 'Financial' in significance:
            score += 10
        elif 'initialization' in significance:
            score += 8
        elif 'Business rule' in significance:
            score += 7

        return min(50, score)  # Cap at 50 for static elements

    def detect_business_annotations(self, method_body: str) -> bool:
        """Detect Java business-related annotations"""
        business_annotations = [
            r'@Transactional',
            r'@Valid',
            r'@Secured',
            r'@PreAuthorize',
            r'@PostAuthorize',
            r'@Cacheable',
            r'@Async',
            r'@Scheduled',
            r'@EventListener',
            r'@MessageMapping',
            r'@RequestMapping',
            r'@Query',
            r'@Authorize'
        ]

        for annotation in business_annotations:
            if re.search(annotation, method_body, re.IGNORECASE):
                return True
        return False


class CSharpBusinessLogicAnalyzer(BaseBusinessLogicAnalyzer):
    """Analyzer for C#/.NET business logic patterns"""

    def __init__(self):
        super().__init__()

        # C#-specific control flow patterns
        self.control_flow_patterns = {
            'complex_conditional': [
                (r'if\s*\([^)]+\)\s*\{[^}]*\}\s*else\s+if\s*\([^)]+\)\s*\{[^}]*\}\s*else', 'Complex if-else-if chain', 4),
                (r'if\s*\([^)]+\)\s*\{(?:[^{}]*\{[^{}]*\})*[^}]*\}', 'Nested conditional logic', 5),
                (r'switch\s*\([^)]+\)\s*\{(?:[^}]*case\s+[^:]*:[^}]*){3,}', 'Complex switch with multiple cases', 4),
                (r'switch\s+expression', 'Switch expression pattern', 3),
                (r'if\s*\([^)]*(?:&&|\|\|)[^)]*(?:&&|\|\|)[^)]*\)', 'Complex compound conditions', 3),
            ],
            'iteration_logic': [
                (r'for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)\s*\{', 'Nested loops', 6),
                (r'foreach\s*\([^)]+\)\s*\{[^}]*if', 'Foreach loop with conditions', 2),
                (r'\.(?:Where|Select|OrderBy|GroupBy|Join)\s*\([^)]*\)', 'LINQ query operations', 3),
                (r'from\s+\w+\s+in\s+\w+.*?select', 'LINQ query syntax', 3),
                (r'Parallel\.(?:For|ForEach)', 'Parallel loop processing', 4),
            ],
            'exception_handling': [
                (r'try\s*\{[^}]*\}\s*catch\s*\([^)]+\)\s*\{[^}]*\}\s*catch', 'Multiple exception handlers', 5),
                (r'try\s*\{[^}]*try\s*\{', 'Nested try blocks', 4),
                (r'throw\s+new\s+\w*(?:Business|Validation|Domain)\w*Exception', 'Domain-specific exception', 4),
                (r'catch\s*\([^)]+\)\s+when\s*\([^)]+\)', 'Exception filter', 3),
                (r'finally\s*\{[^}]*(?:Dispose|Close|Cleanup)', 'Resource cleanup in finally', 3),
            ],
            'synchronization': [
                (r'lock\s*\([^)]+\)\s*\{', 'Lock statement', 3),
                (r'Monitor\.(?:Enter|Exit|Wait|Pulse)', 'Monitor synchronization', 4),
                (r'(?:Mutex|Semaphore|ReaderWriterLock)', 'Advanced synchronization', 4),
                (r'volatile\s+\w+', 'Volatile field', 2),
                (r'async\s+(?:Task|ValueTask)', 'Async method', 3),
                (r'await\s+\w+', 'Await expression', 2),
            ]
        }

        # C#-specific business domain patterns
        self.business_domain_patterns = {
            'financial_calculations': [
                (r'decimal.*?(?:\+|-|\*|/)', 'Decimal calculation', 4),
                (r'Math\.Round\([^)]*MidpointRounding', 'Financial rounding', 4),
                (r'(?:Calculate|Compute)(?:Price|Total|Tax|Fee|Commission|Interest|Balance)', 'Financial calculation method', 5),
                (r'Currency|Money|Amount', 'Financial types', 3),
            ],
            'transaction_management': [
                (r'using\s*\(.*?TransactionScope', 'Transaction scope', 5),
                (r'BeginTransaction|CommitTransaction|Rollback', 'Transaction management', 5),
                (r'IsolationLevel\.', 'Transaction isolation', 4),
                (r'DbTransaction|SqlTransaction', 'Database transaction', 4),
            ],
            'data_processing': [
                (r'DbContext|DataContext', 'Entity Framework context', 3),
                (r'\.(?:Where|FirstOrDefault|SingleOrDefault|ToList|ToArray)\(\)', 'LINQ to SQL', 3),
                (r'SqlCommand|SqlDataAdapter', 'ADO.NET data access', 3),
                (r'IQueryable|IEnumerable', 'Query interfaces', 2),
            ],
            'state_management': [
                (r'enum\s+\w*State\s*\{', 'State enumeration', 3),
                (r'StateMachine|WorkflowInstance', 'State machine', 5),
                (r'Status\s*=\s*\w+\.', 'Status assignment', 3),
            ],
            'validation_logic': [
                (r'\[(?:Required|StringLength|Range|RegularExpression)\]', 'Data annotation validation', 3),
                (r'IValidatableObject|ValidationResult', 'Custom validation', 4),
                (r'ModelState\.IsValid', 'Model validation', 3),
                (r'(?:Validate|Verify|Check|Ensure)[A-Z]\w+', 'Validation method', 4),
            ],
            'integration_patterns': [
                (r'\[(?:HttpGet|HttpPost|HttpPut|HttpDelete)\]', 'Web API endpoint', 3),
                (r'HttpClient|RestSharp', 'HTTP client', 3),
                (r'SignalR|Hub', 'Real-time communication', 4),
                (r'ServiceBus|MessageQueue', 'Message bus', 4),
            ]
        }

        # C#-specific business rule patterns
        self.business_rule_patterns = {
            'authorization_security': [
                (r'\[Authorize(?:\([^)]*\))?\]', 'Authorization attribute', 4),
                (r'ClaimsPrincipal|Identity', 'Identity management', 3),
                (r'User\.(?:IsInRole|HasClaim)', 'Role/claim checking', 4),
                (r'IAuthorizationService', 'Authorization service', 3),
            ],
            'business_calculations': [
                (r'(?:rate|percentage|discount|markup|margin)\s*[*/%]\s*', 'Rate calculation', 4),
                (r'(?:commission|fee|penalty|interest)\s*=.*?(?:Calculate|Compute)', 'Fee calculation', 5),
            ],
            'workflow_orchestration': [
                (r'WorkflowApplication|WorkflowInvoker', 'Workflow foundation', 5),
                (r'BackgroundService|IHostedService', 'Background processing', 3),
                (r'Hangfire|Quartz', 'Job scheduling', 3),
            ]
        }

        # C#-specific static patterns
        self.static_patterns = {
            'financial_constants': [
                (r'(?:static|const|readonly).*?decimal\s+\w*(?:Price|Rate|Fee|Tax|Amount)',
                 'Financial constant', 5),
                (r'(?:static|const|readonly).*?(?:double|float)\s+\w*(?:Rate|Percentage)',
                 'Rate constant', 4),
            ],
            'business_thresholds': [
                (r'(?:static|const|readonly).*?(?:int|long)\s+\w*(?:Max|Min|Limit|Threshold)',
                 'Business limit', 4),
            ],
            'configuration_constants': [
                (r'(?:static|const|readonly).*?string\s+\w*(?:Config|Setting)',
                 'Configuration constant', 3),
            ],
            'static_initialization': [
                (r'static\s+\w+\s*\(\)\s*\{', 'Static constructor', 4),
            ]
        }

    def get_file_extensions(self) -> List[str]:
        return ['.cs', '.cshtml', '.vb']

    def extract_class_name(self, file_content: List[str], file_path: str) -> str:
        """Extract C# class name from file content"""
        content = '\n'.join(file_content)

        # C# class declaration patterns
        class_patterns = [
            r'class\s+([A-Z]\w+)\s*(?::|<|\{)',
            r'interface\s+([A-Z]\w+)\s*(?::|<|\{)',
            r'struct\s+([A-Z]\w+)\s*(?::|<|\{)',
            r'record\s+([A-Z]\w+)\s*(?:\(|:|<|\{)',
            r'public\s+(?:partial\s+)?(?:sealed\s+)?(?:abstract\s+)?class\s+([A-Z]\w+)',
        ]

        for pattern in class_patterns:
            match = re.search(pattern, content)
            if match:
                class_name = match.group(1)
                if class_name and class_name[0].isupper():
                    return class_name

        # Fallback to filename
        filename = Path(file_path).stem
        if filename and filename[0].isupper():
            return filename

        return "UnknownClass"

    def extract_static_elements(self, file_content: List[str], file_path: str, class_name: str) -> List[StaticBusinessRule]:
        """Extract C# static variables, constants, and initialization blocks"""
        static_rules = []
        content = '\n'.join(file_content)

        # Extract static/const/readonly members
        static_patterns = [
            r'(?:public|private|protected|internal)?\s*(?:static|const|readonly|static\s+readonly)\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=\s*([^;]+))?;',
            r'(?:public|private|protected|internal)?\s*const\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        ]

        for pattern in static_patterns:
            for match in re.finditer(pattern, content):
                data_type = match.group(1)
                var_name = match.group(2)
                initial_value = match.group(3) if match.group(3) else 'uninitialized'

                is_business_relevant = False
                significance = ""

                if 'decimal' in data_type.lower():
                    is_business_relevant = True
                    significance = "Financial precision constant"
                elif any(keyword in var_name.upper() for keyword in
                        ['PRICE', 'RATE', 'FEE', 'TAX', 'AMOUNT', 'BALANCE', 'LIMIT',
                         'MAXIMUM', 'MINIMUM', 'THRESHOLD', 'COMMISSION']):
                    is_business_relevant = True
                    significance = "Business rule constant"

                if is_business_relevant:
                    line_num = content[:match.start()].count('\n') + 1
                    static_rules.append(StaticBusinessRule(
                        rule_type='static_constant' if 'const' in match.group(0) or 'readonly' in match.group(0) else 'static_variable',
                        name=var_name,
                        data_type=data_type,
                        value=initial_value.strip() if initial_value else '',
                        code_snippet=match.group(0),
                        file_path=file_path,
                        class_name=class_name,
                        lines=f"{line_num}",
                        business_significance=significance,
                        complexity_score=self.calculate_static_complexity(match.group(0), significance)
                    ))

        # Extract static constructors
        static_ctor_pattern = r'static\s+' + re.escape(class_name) + r'\s*\(\)\s*\{([^}]*)\}'
        for match in re.finditer(static_ctor_pattern, content, re.DOTALL):
            block_content = match.group(1)
            if any(pattern in block_content for pattern in
                   ['decimal', 'Initialize', 'Setup', 'Config']):
                line_num = content[:match.start()].count('\n') + 1
                static_rules.append(StaticBusinessRule(
                    rule_type='static_block',
                    name='static_constructor',
                    data_type='constructor',
                    value='',
                    code_snippet=match.group(0),
                    file_path=file_path,
                    class_name=class_name,
                    lines=f"{line_num}-{line_num + block_content.count(chr(10))}",
                    business_significance="Static initialization",
                    complexity_score=self.calculate_static_complexity(match.group(0), "initialization")
                ))

        return static_rules

    def detect_business_annotations(self, method_body: str) -> bool:
        """Detect C# business-related attributes"""
        business_attributes = [
            r'\[Authorize',
            r'\[Transaction',
            r'\[Required',
            r'\[HttpGet',
            r'\[HttpPost',
            r'\[ServiceFilter',
            r'\[ActionFilter'
        ]

        for attribute in business_attributes:
            if re.search(attribute, method_body):
                return True
        return False


class PHPBusinessLogicAnalyzer(BaseBusinessLogicAnalyzer):
    """Analyzer for PHP business logic patterns"""

    def __init__(self):
        super().__init__()

        # PHP-specific control flow patterns
        self.control_flow_patterns = {
            'complex_conditional': [
                (r'if\s*\([^)]+\)\s*\{[^}]*\}\s*else\s*if\s*\([^)]+\)\s*\{[^}]*\}\s*else', 'Complex if-elseif chain', 4),
                (r'if\s*\([^)]+\)\s*:.*?else\s*:.*?endif', 'Alternative if syntax', 3),
                (r'switch\s*\([^)]+\)\s*\{(?:[^}]*case\s+[^:]*:[^}]*){3,}', 'Complex switch', 4),
                (r'match\s*\([^)]+\)\s*\{', 'Match expression (PHP 8)', 3),
            ],
            'iteration_logic': [
                (r'for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)\s*\{', 'Nested loops', 6),
                (r'foreach\s*\([^)]+\)\s*\{[^}]*if', 'Foreach with conditions', 2),
                (r'while\s*\([^)]+\)\s*\{[^}]*(?:break|continue)', 'While loop with flow control', 3),
                (r'array_(?:map|filter|reduce|walk)', 'Array functional operations', 3),
            ],
            'exception_handling': [
                (r'try\s*\{[^}]*\}\s*catch\s*\([^)]+\)\s*\{[^}]*\}\s*catch', 'Multiple catch blocks', 5),
                (r'throw\s+new\s+\w*(?:Exception|Error)', 'Exception throwing', 3),
                (r'catch\s*\(\s*\w+\s*\|\s*\w+', 'Multiple exception types', 3),
                (r'finally\s*\{', 'Finally block', 3),
            ],
            'synchronization': []  # PHP doesn't have built-in thread synchronization
        }

        # PHP-specific business domain patterns
        self.business_domain_patterns = {
            'financial_calculations': [
                (r'bcadd|bcsub|bcmul|bcdiv|bcmod', 'Arbitrary precision math', 5),
                (r'number_format|money_format', 'Currency formatting', 3),
                (r'round\([^)]*,\s*\d+', 'Decimal rounding', 3),
                (r'(?:calculate|compute)(?:Price|Total|Tax|Fee|Commission)', 'Financial calculation', 5),
            ],
            'transaction_management': [
                (r'\$\w+->beginTransaction\(\)', 'Database transaction start', 5),
                (r'\$\w+->commit\(\)', 'Transaction commit', 4),
                (r'\$\w+->rollback\(\)', 'Transaction rollback', 4),
                (r'DB::transaction', 'Laravel transaction', 4),
            ],
            'data_processing': [
                (r'SELECT.*?(?:JOIN|GROUP BY|HAVING|UNION)', 'Complex SQL query', 4),
                (r'\$\w+->query\(|->prepare\(', 'Database query', 3),
                (r'Eloquent|Model::', 'Laravel Eloquent ORM', 3),
                (r'->where\(|->orderBy\(|->groupBy\(', 'Query builder', 3),
            ],
            'state_management': [
                (r'const\s+(?:PENDING|PROCESSING|COMPLETED|FAILED)', 'Status constants', 3),
                (r'\$(?:status|state)\s*=', 'State assignment', 2),
            ],
            'validation_logic': [
                (r'filter_var|filter_input', 'PHP filter validation', 3),
                (r'preg_match|preg_match_all', 'Regex validation', 3),
                (r'Validator::make|validate\(', 'Laravel validation', 4),
                (r'(?:validate|verify|check)[A-Z]\w+', 'Validation method', 4),
            ],
            'integration_patterns': [
                (r'Route::(?:get|post|put|delete)', 'Laravel routing', 3),
                (r'curl_init|file_get_contents', 'HTTP requests', 3),
                (r'json_encode|json_decode', 'JSON processing', 2),
                (r'API|Rest|Soap', 'API integration', 3),
            ]
        }

        # PHP-specific business rule patterns
        self.business_rule_patterns = {
            'authorization_security': [
                (r'->can\(|->cannot\(|Gate::', 'Laravel authorization', 4),
                (r'Auth::check|Auth::user', 'Authentication check', 3),
                (r'password_hash|password_verify', 'Password handling', 3),
                (r'hash\(|Hash::', 'Hashing operations', 3),
            ],
            'business_calculations': [
                (r'(?:rate|percentage|discount|commission)\s*[*/%]', 'Rate calculation', 4),
                (r'\$(?:total|amount|price)\s*=.*?[+\-*/]', 'Financial calculation', 3),
            ],
            'workflow_orchestration': [
                (r'Job::|dispatch\(|Queue::', 'Laravel queues', 4),
                (r'Event::|event\(', 'Event handling', 3),
                (r'Schedule::|->cron\(', 'Task scheduling', 3),
            ]
        }

        # PHP-specific static patterns
        self.static_patterns = {
            'financial_constants': [
                (r'const\s+\w*(?:PRICE|RATE|FEE|TAX|AMOUNT)', 'Financial constant', 5),
                (r'define\([\'"]\\w*(?:PRICE|RATE|FEE|TAX)', 'Financial define', 4),
            ],
            'business_thresholds': [
                (r'const\s+\w*(?:MAX|MIN|LIMIT|THRESHOLD)', 'Business limit', 4),
                (r'private\s+static\s+\$\w*(?:max|min|limit)', 'Static limit property', 3),
            ],
            'configuration_constants': [
                (r'const\s+\w*(?:CONFIG|SETTING|DEFAULT)', 'Configuration constant', 3),
                (r'define\([\'"]\\w*(?:CONFIG|SETTING)', 'Configuration define', 3),
            ],
            'static_initialization': [
                (r'static\s+function\s+boot\(\)', 'Laravel model boot', 4),
                (r'public\s+static\s+\$\w+\s*=\s*\[', 'Static array initialization', 3),
            ]
        }

    def get_file_extensions(self) -> List[str]:
        return ['.php', '.phtml', '.php3', '.php4', '.php5', '.php7', '.phps']

    def extract_class_name(self, file_content: List[str], file_path: str) -> str:
        """Extract PHP class name from file content"""
        content = '\n'.join(file_content)

        # PHP class declaration patterns
        class_patterns = [
            r'class\s+([A-Z]\w+)(?:\s+extends|\s+implements|\s*\{)',
            r'interface\s+([A-Z]\w+)(?:\s+extends|\s*\{)',
            r'trait\s+([A-Z]\w+)\s*\{',
            r'abstract\s+class\s+([A-Z]\w+)',
            r'final\s+class\s+([A-Z]\w+)',
        ]

        for pattern in class_patterns:
            match = re.search(pattern, content)
            if match:
                class_name = match.group(1)
                if class_name and class_name[0].isupper():
                    return class_name

        # Fallback to filename
        filename = Path(file_path).stem
        if filename and filename[0].isupper():
            return filename

        return "UnknownClass"

    def extract_static_elements(self, file_content: List[str], file_path: str, class_name: str) -> List[StaticBusinessRule]:
        """Extract PHP static variables, constants, and initialization blocks"""
        static_rules = []
        content = '\n'.join(file_content)

        # Extract class constants
        const_pattern = r'(?:public|private|protected)?\s*const\s+(\w+)\s*=\s*([^;]+);'
        for match in re.finditer(const_pattern, content):
            const_name = match.group(1)
            const_value = match.group(2)

            is_business_relevant = False
            significance = ""

            if any(keyword in const_name.upper() for keyword in
                   ['PRICE', 'RATE', 'FEE', 'TAX', 'AMOUNT', 'BALANCE', 'LIMIT',
                    'MAXIMUM', 'MINIMUM', 'THRESHOLD', 'COMMISSION']):
                is_business_relevant = True
                significance = "Business rule constant"

            if is_business_relevant:
                line_num = content[:match.start()].count('\n') + 1
                static_rules.append(StaticBusinessRule(
                    rule_type='static_constant',
                    name=const_name,
                    data_type='const',
                    value=const_value.strip(),
                    code_snippet=match.group(0),
                    file_path=file_path,
                    class_name=class_name,
                    lines=f"{line_num}",
                    business_significance=significance,
                    complexity_score=self.calculate_static_complexity(match.group(0), significance)
                ))

        # Extract static properties
        static_prop_pattern = r'(?:public|private|protected)?\s*static\s+\$(\w+)\s*(?:=\s*([^;]+))?;'
        for match in re.finditer(static_prop_pattern, content):
            prop_name = match.group(1)
            prop_value = match.group(2) if match.group(2) else 'uninitialized'

            is_business_relevant = any(keyword in prop_name.upper() for keyword in
                                      ['CONFIG', 'SETTING', 'CACHE', 'INSTANCE'])

            if is_business_relevant:
                line_num = content[:match.start()].count('\n') + 1
                static_rules.append(StaticBusinessRule(
                    rule_type='static_variable',
                    name=f"${prop_name}",
                    data_type='static',
                    value=prop_value.strip() if prop_value != 'uninitialized' else '',
                    code_snippet=match.group(0),
                    file_path=file_path,
                    class_name=class_name,
                    lines=f"{line_num}",
                    business_significance="Static configuration",
                    complexity_score=self.calculate_static_complexity(match.group(0), "configuration")
                ))

        return static_rules

    def detect_business_annotations(self, method_body: str) -> bool:
        """Detect PHP business-related annotations/attributes"""
        # PHP 8 attributes and docblock annotations
        business_patterns = [
            r'#\[Route',
            r'#\[Authorize',
            r'@Route',
            r'@Security',
            r'@Transaction',
            r'@Validate'
        ]

        for pattern in business_patterns:
            if re.search(pattern, method_body):
                return True
        return False


class BusinessLogicExtractorV4:
    """Enhanced business logic extractor with multi-language support"""

    def __init__(self):
        self.parser = None
        self.repomix_content = []
        self.analyzer = None  # Will be set based on file type
        self.tree_sitter_analyzer = TreeSitterBusinessRuleAnalyzer()  # Add tree-sitter analyzer
        self.analyzers = {
            '.java': JavaBusinessLogicAnalyzerV4(),
            '.jsp': JavaBusinessLogicAnalyzerV4(),
            '.jsf': JavaBusinessLogicAnalyzerV4(),
            '.cs': CSharpBusinessLogicAnalyzer(),
            '.cshtml': CSharpBusinessLogicAnalyzer(),
            '.vb': CSharpBusinessLogicAnalyzer(),
            '.php': PHPBusinessLogicAnalyzer(),
            '.phtml': PHPBusinessLogicAnalyzer(),
            '.php3': PHPBusinessLogicAnalyzer(),
            '.php4': PHPBusinessLogicAnalyzer(),
            '.php5': PHPBusinessLogicAnalyzer(),
            '.php7': PHPBusinessLogicAnalyzer(),
            '.phps': PHPBusinessLogicAnalyzer()
        }
        self.methods_by_signature = {}
        self.static_rules = []

    def get_analyzer_for_file(self, file_path: str) -> Optional[BaseBusinessLogicAnalyzer]:
        """Get the appropriate analyzer based on file extension"""
        ext = Path(file_path).suffix.lower()
        return self.analyzers.get(ext)

    def load_repomix_content(self, repomix_path: str) -> bool:
        """Load the repomix file content"""
        try:
            with open(repomix_path, 'r', encoding='utf-8') as f:
                self.repomix_content = f.readlines()
            return True
        except Exception as e:
            print(f"❌ Error loading repomix content: {e}")
            return False

    def extract_file_content(self, file_path: str) -> List[str]:
        """Extract content for a specific file from repomix"""
        file_content = []
        file_start = -1
        in_file = False

        for i, line in enumerate(self.repomix_content):
            if line.strip() == f"## File: {file_path}":
                in_file = True
                file_start = i
                continue
            elif in_file and line.startswith("## File:"):
                break
            elif in_file:
                file_content.append(line)

        return file_content

    def extract_full_method_body(self, repomix_content: List[str], file_path: str,
                                method_name: str, start_line: int) -> Tuple[str, int, int]:
        """Enhanced method body extraction with better brace tracking and edge case handling
        This method works for Java, C#, and PHP"""
        file_start = -1
        file_end = len(repomix_content)

        # Find file section
        for i, line in enumerate(repomix_content):
            if line.strip() == f"## File: {file_path}":
                file_start = i
                for j in range(i + 1, len(repomix_content)):
                    if repomix_content[j].startswith("## File:"):
                        file_end = j
                        break
                break

        if file_start == -1:
            return "", 0, 0

        # Get the appropriate analyzer for this file
        analyzer = self.get_analyzer_for_file(file_path)
        if not analyzer:
            analyzer = self.analyzers['.java']  # Default to Java analyzer

        # Enhanced method extraction
        method_lines = []
        in_code_block = False
        method_found = False
        brace_count = 0
        paren_count = 0
        in_string = False
        in_comment = False
        method_start_line = 0
        method_end_line = 0
        current_line_num = 0
        signature_lines = []
        collecting_signature = False

        # Language-specific modifiers
        if file_path.endswith(('.java', '.jsp', '.jsf')):
            modifiers = r'(public|private|protected|static|final|abstract|synchronized)'
        elif file_path.endswith(('.cs', '.cshtml', '.vb')):
            modifiers = r'(public|private|protected|internal|static|virtual|override|abstract|sealed|async)'
        elif file_path.endswith('.php'):
            modifiers = r'(public|private|protected|static|final|abstract)'
        else:
            modifiers = r'(public|private|protected|static)'

        for i in range(file_start + 1, file_end):
            line = repomix_content[i]

            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    current_line_num = 0
                continue

            if in_code_block:
                current_line_num += 1
                stripped_line = line.strip()

                # Skip empty lines before method is found
                if not method_found and not stripped_line:
                    continue

                # Enhanced method signature detection
                if not method_found:
                    # Check for method signature patterns
                    if (method_name in line and
                        (re.search(modifiers, line) or
                         collecting_signature or
                         (file_path.endswith('.php') and 'function' in line))):

                        if not collecting_signature:
                            collecting_signature = True
                            method_start_line = current_line_num
                            paren_count = 0
                            in_string = False

                        signature_lines.append(line.rstrip())

                        # Track parentheses in signature
                        for char in line:
                            if char == '(' and not in_string:
                                paren_count += 1
                            elif char == ')' and not in_string:
                                paren_count -= 1
                            elif char == '"':
                                in_string = not in_string

                        # Check if we have complete signature
                        if paren_count == 0 and '(' in ' '.join(signature_lines):
                            method_found = True
                            method_lines = signature_lines.copy()

                            # Count braces in signature lines
                            for sig_line in signature_lines:
                                if '{' in sig_line:
                                    brace_count += sig_line.count('{')
                                if '}' in sig_line:
                                    brace_count -= sig_line.count('}')

                            collecting_signature = False

                elif method_found:
                    method_lines.append(line.rstrip())

                    # Enhanced brace counting with string/comment awareness
                    i = 0
                    while i < len(line):
                        if in_comment:
                            if '*/' in line[i:]:
                                in_comment = False
                                i = line.index('*/', i) + 2
                                continue
                        elif line[i:i+2] == '/*':
                            in_comment = True
                            i += 2
                            continue
                        elif line[i:i+2] == '//':
                            break  # Rest of line is comment
                        elif line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                            in_string = not in_string
                        elif not in_string and not in_comment:
                            if line[i] == '{':
                                brace_count += 1
                            elif line[i] == '}':
                                brace_count -= 1
                        i += 1

                    # Method ends when braces balance
                    if brace_count == 0 and len(method_lines) > 1:
                        method_end_line = current_line_num
                        break

        return '\n'.join(method_lines), method_start_line, method_end_line

    def should_skip_method(self, method_name: str, method_body: str) -> bool:
        """Improved trivial method detection - less aggressive filtering"""
        if not method_body or not method_body.strip():
            return True

        # Count meaningful lines (excluding comments and braces)
        meaningful_lines = []
        for line in method_body.split('\n'):
            stripped = line.strip()
            if (stripped and
                not stripped.startswith('//') and
                not stripped.startswith('/*') and
                not stripped.startswith('*') and
                stripped not in ['{', '}', '};']):
                meaningful_lines.append(stripped)

        # Skip only if truly trivial
        if len(meaningful_lines) <= 1:
            # Check if it's a simple getter/setter
            if (method_name.startswith('get') or method_name.startswith('set') or
                method_name.startswith('is')):
                # Simple return statement or assignment
                if len(meaningful_lines) == 1:
                    line = meaningful_lines[0]
                    if (re.match(r'^return\s+\w+;?$', line) or
                        re.match(r'^this\.\w+\s*=\s*\w+;?$', line)):
                        return True

        # Skip basic Object methods only if they're very simple
        if method_name in ['toString', 'hashCode', 'equals']:
            if len(meaningful_lines) <= 2:
                return True

        # Don't skip methods with any business logic patterns
        business_indicators = [
            'if', 'for', 'while', 'switch', 'try', 'throw',
            'calculate', 'validate', 'process', 'handle', 'check',
            'BigDecimal', 'Transaction', 'Order', 'Account',
            '@Transactional', '@Valid', '@PreAuthorize',
            'decimal', 'Money', 'Currency'  # C# patterns
        ]

        for indicator in business_indicators:
            if indicator in method_body:
                return False

        # Skip if method is too short and has no business indicators
        if len(meaningful_lines) <= 2:
            return True

        return False

    def analyze_method(self, component: Any, file_path: str) -> Optional[MethodBusinessLogic]:
        """Enhanced method analysis with multi-language support"""
        # Get appropriate analyzer for the file
        analyzer = self.get_analyzer_for_file(file_path)
        if not analyzer:
            return None  # Unsupported file type

        # Extract component information
        if hasattr(component, '__dict__'):
            comp_dict = component.__dict__
        else:
            comp_dict = component

        method_name = comp_dict.get('name', '')
        signature = comp_dict.get('signature', '')
        start_line = comp_dict.get('original_line', 0)

        # Extract full method body with improved extraction
        method_body, method_start, method_end = self.extract_full_method_body(
            self.repomix_content, file_path, method_name, start_line
        )

        if not method_body or self.should_skip_method(method_name, method_body):
            return None

        # Calculate cyclomatic complexity
        cyclomatic = analyzer.calculate_cyclomatic_complexity(method_body)

        # Check for business annotations
        has_annotations = analyzer.detect_business_annotations(method_body)

        # Create unique signature for deduplication
        class_name = self.extract_class_name(file_path, method_start, analyzer)
        unique_signature = f"{class_name}.{method_name}({file_path}:{method_start})"

        # Multi-pass analysis
        control_flow_score, control_flow_snippets = analyzer.analyze_control_flow_complexity(method_body)
        domain_score, domain_snippets = analyzer.analyze_business_domain(method_body)
        rule_snippets = analyzer.analyze_business_rules(method_body)

        # Combine and deduplicate snippets
        all_snippets = control_flow_snippets + domain_snippets + rule_snippets

        # Deduplicate snippets by snippet text
        unique_snippets = {}
        for snippet in all_snippets:
            key = f"{snippet.type}:{snippet.snippet[:50]}"
            if key not in unique_snippets or snippet.importance > unique_snippets[key].importance:
                unique_snippets[key] = snippet

        all_snippets = list(unique_snippets.values())

        # Calculate method length
        method_length = len([line for line in method_body.split('\n') if line.strip()])

        # Calculate overall complexity with enhanced algorithm
        complexity_score = analyzer.calculate_complexity_score(
            control_flow_score, domain_score, len(all_snippets),
            method_length, cyclomatic, has_annotations
        )

        # Extract business logic types
        business_logic_types = list(set(snippet.type for snippet in all_snippets))

        # NEW: Extract business rules using tree-sitter AST analysis
        extracted_rules = self.tree_sitter_analyzer.extract_business_rules_from_method(method_body, file_path)

        return MethodBusinessLogic(
            method_signature=f"{method_name}({signature.split('(', 1)[1] if '(' in signature else ''}",
            file_path=file_path,
            class_name=class_name,
            start_line=method_start,
            end_line=method_end,
            complexity_score=complexity_score,
            business_logic_types=business_logic_types,
            snippets=sorted(all_snippets, key=lambda x: x.importance, reverse=True)[:20],
            full_method_body=method_body,
            control_flow_complexity=control_flow_score,
            business_domain_score=domain_score,
            rules=extracted_rules,  # NEW: Add the tree-sitter extracted rules
            cyclomatic_complexity=cyclomatic,
            method_length=method_length,
            has_business_annotations=has_annotations
        )

    def extract_class_name(self, file_path: str, method_line: int, analyzer: BaseBusinessLogicAnalyzer) -> str:
        """Extract class name using language-specific analyzer"""
        file_content = self.extract_file_content(file_path)
        if file_content:
            return analyzer.extract_class_name(file_content, file_path)

        # Fallback to filename
        filename = Path(file_path).stem
        if filename and filename[0].isupper():
            return filename
        return "UnknownClass"

    def extract(self, repomix_path: str) -> Dict[str, Any]:
        """Main extraction with enhanced quality checks and multi-language support"""
        # Initialize parser
        self.parser = RepomixParser(repomix_path)

        if not self.parser.load():
            raise Exception(f"Failed to load repomix file: {repomix_path}")

        if not self.load_repomix_content(repomix_path):
            print("⚠️ Warning: Could not load repomix content")

        # Extract components
        components = self.parser.extract_all_components()

        # Group files by language for static analysis
        files_by_language = defaultdict(set)
        for method in components.get('methods', []):
            file_path = method.file_path if hasattr(method, 'file_path') else method.get('file_path', '')
            analyzer = self.get_analyzer_for_file(file_path)
            if analyzer:
                files_by_language[type(analyzer).__name__].add(file_path)

        # Phase 1: Extract static elements from each file
        all_static_rules = []
        for analyzer_type, files in files_by_language.items():
            for file_path in files:
                analyzer = self.get_analyzer_for_file(file_path)
                if analyzer:
                    class_name = self.extract_class_name(file_path, 0, analyzer)
                    file_content = self.extract_file_content(file_path)
                    static_rules = analyzer.extract_static_elements(file_content, file_path, class_name)
                    all_static_rules.extend(static_rules)

        # Get interface files to exclude
        interface_files = set()
        for interface in components.get('interfaces', []):
            if hasattr(interface, 'file_path'):
                interface_files.add(interface.file_path)
            else:
                interface_files.add(interface.get('file_path', ''))

        # Phase 2: Parse and analyze all methods
        analyzed_methods = []

        for method in components.get('methods', []):
            if hasattr(method, 'file_path'):
                file_path = method.file_path
            else:
                file_path = method.get('file_path', '')

            # Skip interface methods and unsupported files
            if file_path in interface_files:
                continue

            # Check if we have an analyzer for this file type
            if not self.get_analyzer_for_file(file_path):
                continue

            method_analysis = self.analyze_method(method, file_path)
            if method_analysis:
                analyzed_methods.append(method_analysis)

        # Phase 3: Consolidation with improved deduplication
        consolidated_methods = {}
        for method in analyzed_methods:
            # Create more specific key to avoid over-consolidation
            method_name = method.method_signature.split('(')[0]
            key = f"{method.file_path}::{method.class_name}::{method_name}::{method.start_line}"

            if key not in consolidated_methods:
                consolidated_methods[key] = method
            else:
                # Merge if truly the same method
                existing = consolidated_methods[key]
                if abs(existing.start_line - method.start_line) <= 2:  # Same method
                    # Keep the one with higher complexity
                    if method.complexity_score > existing.complexity_score:
                        consolidated_methods[key] = method

        # Phase 4: Ranking and categorization
        final_methods = list(consolidated_methods.values())
        final_methods.sort(key=lambda x: x.complexity_score, reverse=True)

        # Filter static rules by complexity
        significant_static_rules = [rule for rule in all_static_rules if rule.complexity_score >= 20]
        significant_static_rules.sort(key=lambda x: x.complexity_score, reverse=True)

        # Filter methods by complexity threshold (default 20) BEFORE assigning IDs
        min_complexity_threshold = 20
        significant_methods = [m for m in final_methods if m.complexity_score >= min_complexity_threshold]

        # Calculate statistics (on ALL methods for reporting)
        total_methods = len(final_methods)
        total_static = len(significant_static_rules)
        high_complexity = len([m for m in final_methods if m.complexity_score >= 50])
        medium_complexity = len([m for m in final_methods if 20 <= m.complexity_score < 50])
        low_complexity = len([m for m in final_methods if m.complexity_score < 20])

        # Create unified list of all business rules with continuous numbering
        all_business_rules = []
        rule_counter = 1

        # Add significant methods first (sorted by complexity)
        for method in significant_methods:
            rule_dict = self.method_to_dict(method, f"BR-{rule_counter:05d}")
            all_business_rules.append(rule_dict)
            rule_counter += 1

        # Add static rules with continued numbering
        for static_rule in significant_static_rules:
            rule_dict = self.static_rule_to_dict(static_rule, f"BR-{rule_counter:05d}")
            all_business_rules.append(rule_dict)
            rule_counter += 1

        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'source_file': repomix_path,
            'extractor_version': '4.0',
            'analysis_type': 'comprehensive_business_logic_with_static',
            'statistics': {
                'total_business_rules': len(all_business_rules),
                'total_methods_analyzed': len(significant_methods),
                'total_static_rules': total_static,
                'high_complexity_methods': high_complexity,
                'medium_complexity_methods': medium_complexity,
                'low_complexity_methods': low_complexity,
                'average_complexity': sum(m.complexity_score for m in final_methods) / total_methods if total_methods > 0 else 0,
                'average_cyclomatic': sum(m.cyclomatic_complexity for m in final_methods) / total_methods if total_methods > 0 else 0,
                'methods_with_annotations': len([m for m in final_methods if m.has_business_annotations])
            },
            'business_logic_distribution': self.calculate_distribution(final_methods),
            'business_rules': all_business_rules
        }

    def calculate_distribution(self, methods: List[MethodBusinessLogic]) -> Dict[str, int]:
        """Calculate distribution of business logic types"""
        distribution = defaultdict(int)
        for method in methods:
            for logic_type in method.business_logic_types:
                distribution[logic_type] += 1
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

    def generate_business_rule_description(self, method: MethodBusinessLogic) -> str:
        """Generate a meaningful business rule description based on method analysis"""
        descriptions = []

        # Primary description based on method name and class
        method_name = method.method_signature.split('(')[0].lower()
        class_name = method.class_name.lower()

        # Method name based descriptions
        if 'buy' in method_name or 'purchase' in method_name:
            descriptions.append("Process buy order and update portfolio holdings")
        elif 'sell' in method_name:
            descriptions.append("Execute sell order and calculate proceeds")
        elif 'completeorder' in method_name:
            descriptions.append("Finalize order execution and update account balances")
        elif 'getmarketsummary' in method_name:
            descriptions.append("Retrieve market performance metrics and top movers")
        elif 'reset' in method_name:
            descriptions.append("Reset trading data and restore initial state")
        elif 'create' in method_name:
            if 'account' in method_name:
                descriptions.append("Create new trading account with initial balance")
            elif 'trade' in method_name:
                descriptions.append("Initialize trading environment and data")
            else:
                descriptions.append("Create and initialize business entities")
        elif 'validate' in method_name:
            descriptions.append("Validate business constraints and data integrity")
        elif 'calculate' in method_name:
            descriptions.append("Perform financial calculations and aggregations")
        elif 'process' in method_name:
            descriptions.append("Process business transaction workflow")
        elif 'update' in method_name:
            descriptions.append("Update entity state and persist changes")
        elif 'login' in method_name or 'logout' in method_name:
            descriptions.append("Manage user authentication and session")
        elif 'register' in method_name:
            descriptions.append("Register new user and initialize profile")
        elif 'config' in method_name or 'setconfig' in method_name:
            descriptions.append("Configure system parameters and settings")
        elif 'init' in method_name:
            descriptions.append("Initialize system components and resources")
        elif 'performtask' in method_name or 'service' in method_name:
            descriptions.append("Handle service request and route to business logic")
        elif 'onmessage' in method_name:
            descriptions.append("Process asynchronous message and trigger actions")

        # Add details based on business logic types
        logic_details = []
        if 'financial_calculations' in method.business_logic_types:
            logic_details.append("with financial calculations")
        if 'transaction_management' in method.business_logic_types:
            logic_details.append("with transaction management")
        if 'state_management' in method.business_logic_types:
            logic_details.append("including state transitions")
        if 'validation_logic' in method.business_logic_types:
            logic_details.append("with validation rules")
        if 'exception_handling' in method.business_logic_types:
            logic_details.append("with error handling")

        # Combine description
        if descriptions:
            base_desc = descriptions[0]
            if logic_details:
                base_desc += " " + " and ".join(logic_details[:2])
            return base_desc
        else:
            # Fallback description based on logic types
            if method.business_logic_types:
                return f"Business logic for {' and '.join(method.business_logic_types[:2])}"
            else:
                return f"Business method implementation in {method.class_name}"

    def method_to_dict(self, method: MethodBusinessLogic, rule_id: str) -> Dict[str, Any]:
        """Convert MethodBusinessLogic to dictionary for JSON serialization"""
        return {
            'business_rule_id': rule_id,
            'business_rule_description': self.generate_business_rule_description(method),
            'rule_type': 'method',
            'method_signature': method.method_signature,
            'file_path': method.file_path,
            'class_name': method.class_name,
            'lines': f"{method.start_line}-{method.end_line}",
            'complexity_score': method.complexity_score,
            'business_logic_types': method.business_logic_types,
            'rules': method.rules or [],  # NEW: Include tree-sitter extracted rules
            'full_method_source': method.full_method_body
        }

    def static_rule_to_dict(self, rule: StaticBusinessRule, rule_id: str) -> Dict[str, Any]:
        """Convert StaticBusinessRule to dictionary for JSON serialization"""
        description = f"{rule.business_significance}: {rule.name}"
        if rule.rule_type == 'static_block':
            description = "Static initialization block with business logic configuration"
        elif 'BigDecimal' in rule.data_type or 'decimal' in rule.data_type.lower():
            description = f"Financial constant {rule.name} with precise decimal value"
        elif rule.value:
            description = f"{rule.business_significance}: {rule.name} = {rule.value[:50]}"

        return {
            'business_rule_id': rule_id,
            'business_rule_description': description,
            'rule_type': rule.rule_type,
            'name': rule.name,
            'data_type': rule.data_type,
            'value': rule.value,
            'file_path': rule.file_path,
            'class_name': rule.class_name,
            'lines': rule.lines,
            'complexity_score': rule.complexity_score,
            'business_significance': rule.business_significance,
            'code_snippet': rule.code_snippet
        }


def main():
    parser = argparse.ArgumentParser(description='Comprehensive Business Logic Extraction V4 - Multi-language')
    parser.add_argument('--input', '-i', default='output/reports/repomix-summary.md',
                        help='Path to Repomix summary file')
    parser.add_argument('--output', '-o', default='output/context/business-rules-extracted.json',
                        help='Output JSON file path')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--min-complexity', type=int, default=20,
                        help='Minimum complexity score to include (default: 20)')
    parser.add_argument('--top-n', type=int, default=0,
                        help='Only output top N methods by complexity (0 for all)')
    parser.add_argument('--include-static', action='store_true', default=True,
                        help='Include static variables and initialization blocks (default: True)')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        return 1

    # Extract business logic
    extractor = BusinessLogicExtractorV4()

    try:
        results = extractor.extract(args.input)

        # Filter by minimum complexity if specified
        if args.min_complexity > 0 and 'business_rules' in results:
            filtered_rules = [r for r in results['business_rules']
                            if r.get('complexity_score', 0) >= args.min_complexity]
            results['business_rules'] = filtered_rules
            # Recalculate statistics
            method_rules = [r for r in filtered_rules if r.get('method_signature')]
            total = len(method_rules)
            results['statistics']['total_methods_analyzed'] = total
            if total > 0:
                results['statistics']['average_complexity'] = sum(r.get('complexity_score', 0) for r in method_rules) / total

        # Limit to top N if specified
        if args.top_n > 0 and 'business_rules' in results:
            results['business_rules'] = results['business_rules'][:args.top_n]

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Print enhanced summary
    stats = results['statistics']
    print(f"✅ Comprehensive Business Logic Extraction Complete (V4 - Multi-language)")
    print(f"   Source: {args.input}")
    print(f"   Output: {args.output}")
    print(f"\n📊 Statistics:")
    print(f"   Total Business Rules: {stats.get('total_business_rules', stats['total_methods_analyzed'] + stats['total_static_rules'])}")
    print(f"   - Methods: {stats['total_methods_analyzed']}")
    print(f"   - Static Rules: {stats['total_static_rules']}")
    print(f"   High complexity (50+): {stats['high_complexity_methods']}")
    print(f"   Medium complexity (20-49): {stats['medium_complexity_methods']}")
    print(f"   Low complexity (<20): {stats['low_complexity_methods']}")
    print(f"   Average complexity: {stats['average_complexity']:.1f}")

    # Show sample business rules (both methods and static)
    if results.get('business_rules'):
        # Find static rules in the unified list
        static_rules = [r for r in results['business_rules'] if r.get('rule_type') in ['static_variable', 'static_constant', 'static_block']]
        if static_rules:
            print(f"\n📋 Sample Static Business Rules:")
            for rule in static_rules[:5]:  # Show first 5
                desc = rule.get('business_rule_description', rule.get('business_significance', 'Static rule'))
                print(f"   {rule['business_rule_id']}: {desc[:60]}...")

    if results['business_logic_distribution']:
        print(f"\n📈 Business Logic Distribution:")
        for logic_type, count in list(results['business_logic_distribution'].items())[:10]:
            print(f"   - {logic_type.replace('_', ' ').title()}: {count}")

    if args.verbose and results.get('business_rules'):
        print(f"\n🔝 Top 5 Most Complex Business Rules:")
        # Sort by complexity and show top 5
        sorted_rules = sorted([r for r in results['business_rules'] if 'complexity_score' in r],
                            key=lambda x: x['complexity_score'], reverse=True)[:5]
        for i, rule in enumerate(sorted_rules, 1):
            if rule.get('method_signature'):
                print(f"  {i:2}. [{rule['complexity_score']:3}] {rule['class_name']}.{rule['method_signature']}")
            else:
                print(f"  {i:2}. [{rule['complexity_score']:3}] {rule['class_name']}.{rule.get('name', 'static_rule')}")

    # Print detected languages
    print(f"\n🌐 Languages Detected:")
    languages = set()
    for rule in results.get('business_rules', []):
        file_path = rule.get('file_path', '')
        if file_path.endswith(('.java', '.jsp', '.jsf')):
            languages.add('Java')
        elif file_path.endswith(('.cs', '.cshtml', '.vb')):
            languages.add('C#/.NET')
        elif file_path.endswith(('.php', '.phtml')):
            languages.add('PHP')
    for lang in sorted(languages):
        print(f"   - {lang}")

    return 0


if __name__ == '__main__':
    exit(main())