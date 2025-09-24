#!/usr/bin/env python3
"""
Test suite for complete business rules catalog generation
Ensures ALL rules are documented without data loss
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import os

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from generate_complete_business_rules_catalog import (
    load_extracted_rules,
    generate_rule_markdown,
    write_rules_incrementally,
    generate_distribution_summary,
    main
)


class TestCompleteCatalogGeneration(unittest.TestCase):
    """Test complete catalog generation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_json = Path(self.test_dir) / 'test_rules.json'
        self.test_output = Path(self.test_dir) / 'test_catalog.md'

        # Create sample rules data
        self.sample_data = {
            "extraction_timestamp": "2025-09-24T08:36:12.024088",
            "statistics": {
                "total_business_rules": 3,
                "total_methods_analyzed": 2,
                "total_static_rules": 1,
                "high_complexity_methods": 1,
                "medium_complexity_methods": 1,
                "low_complexity_methods": 0,
                "average_complexity": 35.0
            },
            "business_rules": [
                {
                    "business_rule_id": "BR-00001",
                    "business_rule_description": "Process sell order",
                    "rule_type": "method",
                    "method_signature": "sell(String userID, Integer holdingID)",
                    "file_path": "TradeSLSB.java",
                    "class_name": "TradeSLSB",
                    "lines": "100-150",
                    "complexity_score": 50,
                    "business_logic_types": ["transaction_management", "financial_calculations"],
                    "full_method_source": "public OrderDataBean sell() { /* method code */ }"
                },
                {
                    "business_rule_id": "BR-00002",
                    "business_rule_description": "Process buy order",
                    "rule_type": "method",
                    "method_signature": "buy(String userID, String symbol, double quantity)",
                    "file_path": "TradeSLSB.java",
                    "class_name": "TradeSLSB",
                    "lines": "200-250",
                    "complexity_score": 45,
                    "business_logic_types": ["validation_logic", "state_management"],
                    "full_method_source": "public OrderDataBean buy() { /* buy code */ }"
                },
                {
                    "business_rule_id": "BR-00003",
                    "business_rule_description": "Order fee constant",
                    "rule_type": "static_constant",
                    "name": "ORDER_FEE",
                    "data_type": "BigDecimal",
                    "file_path": "TradeConfig.java",
                    "lines": "50",
                    "code_snippet": "public static final BigDecimal ORDER_FEE = new BigDecimal(\"24.95\");",
                    "business_significance": "Financial precision constant"
                }
            ]
        }

        # Write test JSON
        with open(self.test_json, 'w') as f:
            json.dump(self.sample_data, f)

    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_extracted_rules(self):
        """Test loading rules from JSON"""
        data = load_extracted_rules(str(self.test_json))

        self.assertIsNotNone(data)
        self.assertEqual(len(data['business_rules']), 3)
        self.assertEqual(data['statistics']['total_business_rules'], 3)

    def test_generate_rule_markdown(self):
        """Test markdown generation for a single rule"""
        rule = self.sample_data['business_rules'][0]
        markdown = generate_rule_markdown(rule, 1)

        # Check required elements
        self.assertIn("### BR-00001:", markdown)
        self.assertIn("Process sell order", markdown)
        self.assertIn("**Type**: method", markdown)
        self.assertIn("TradeSLSB.java:100-150", markdown)
        self.assertIn("**Complexity Score**: 50", markdown)
        self.assertIn("```java", markdown)
        self.assertIn("public OrderDataBean sell()", markdown)

    def test_generate_static_rule_markdown(self):
        """Test markdown generation for static rule"""
        rule = self.sample_data['business_rules'][2]
        markdown = generate_rule_markdown(rule, 3)

        self.assertIn("### BR-00003:", markdown)
        self.assertIn("Order fee constant", markdown)
        self.assertIn("**Type**: static_constant", markdown)
        self.assertIn("**Name**: `ORDER_FEE`", markdown)
        self.assertIn("**Data Type**: `BigDecimal`", markdown)
        self.assertIn("Financial precision constant", markdown)

    def test_write_rules_incrementally(self):
        """Test incremental writing with small batches"""
        rules = self.sample_data['business_rules'][:2]  # Use method rules

        written = write_rules_incrementally(
            rules,
            str(self.test_output),
            "method",
            batch_size=1  # Test with batch size of 1
        )

        self.assertEqual(written, 2)
        self.assertTrue(self.test_output.exists())

        # Check file content
        content = self.test_output.read_text()
        self.assertIn("Complete Business Rules Catalog - method", content)
        self.assertIn("BR-00001", content)
        self.assertIn("BR-00002", content)
        self.assertIn("Successfully documented **2** out of **2** method rules", content)

    def test_generate_distribution_summary(self):
        """Test distribution summary generation"""
        rules = self.sample_data['business_rules'][:2]  # Method rules only
        summary = generate_distribution_summary(rules)

        self.assertIn("Business Logic Distribution", summary)
        self.assertIn("transaction_management", summary.lower())
        self.assertIn("financial_calculations", summary.lower())
        self.assertIn("validation_logic", summary.lower())

    def test_all_rules_documented(self):
        """Test that ALL rules are documented"""
        # Create a larger dataset
        large_data = self.sample_data.copy()
        large_data['business_rules'] = []

        # Add 71 rules (matching real scenario)
        for i in range(1, 72):
            rule = {
                "business_rule_id": f"BR-{i:05d}",
                "business_rule_description": f"Test rule {i}",
                "rule_type": "method" if i <= 54 else "static_constant",
                "method_signature": f"method{i}()" if i <= 54 else None,
                "name": f"CONSTANT_{i}" if i > 54 else None,
                "file_path": f"File{i}.java",
                "lines": f"{i*10}-{i*10+50}",
                "complexity_score": i * 2,
                "business_logic_types": ["test_logic"],
                "full_method_source": f"public void method{i}() {{ }}" if i <= 54 else None,
                "code_snippet": f"public static final int CONSTANT_{i} = {i};" if i > 54 else None
            }
            large_data['business_rules'].append(rule)

        large_data['statistics']['total_business_rules'] = 71

        # Write large dataset
        large_json = Path(self.test_dir) / 'large_rules.json'
        with open(large_json, 'w') as f:
            json.dump(large_data, f)

        # Test with command line arguments
        with patch('sys.argv', ['test',
                               '--input', str(large_json),
                               '--output-dir', str(self.test_dir),
                               '--batch-size', '10']):
            result = main()
            self.assertEqual(result, 0)

        # Check output file
        output_file = Path(self.test_dir) / 'business-rules-deterministic-complete.md'
        self.assertTrue(output_file.exists())

        content = output_file.read_text()

        # Verify all 71 rules are present
        for i in range(1, 72):
            rule_id = f"BR-{i:05d}"
            self.assertIn(f"### {rule_id}:", content,
                         f"Rule {rule_id} not found in output")

        # Count actual rules in output
        rule_count = content.count("### BR-")
        self.assertEqual(rule_count, 71,
                        f"Expected 71 rules, found {rule_count}")

    def test_error_handling(self):
        """Test error handling for missing input"""
        with patch('sys.argv', ['test',
                               '--input', 'nonexistent.json',
                               '--output-dir', str(self.test_dir)]):
            result = main()
            self.assertEqual(result, 1)

    def test_batch_processing_memory_safety(self):
        """Test that batch processing prevents memory issues"""
        # Create rules with large content
        large_content_rules = []
        for i in range(20):
            rule = {
                "business_rule_id": f"BR-{i+1:05d}",
                "business_rule_description": f"Large rule {i+1}",
                "rule_type": "method",
                "file_path": "Test.java",
                "lines": f"{i*100}-{i*100+50}",
                "complexity_score": 30,
                "business_logic_types": ["test"],
                # Large source code
                "full_method_source": "public void method() {\n" + ("    // Large content\n" * 100) + "}"
            }
            large_content_rules.append(rule)

        # Process with small batch size
        output = Path(self.test_dir) / 'large_content.md'
        written = write_rules_incrementally(
            large_content_rules,
            str(output),
            "method",
            batch_size=2  # Small batch to test incremental writing
        )

        self.assertEqual(written, 20)
        self.assertTrue(output.exists())

        # Verify file is not corrupted
        content = output.read_text()
        for i in range(1, 21):
            self.assertIn(f"BR-{i:05d}", content)


if __name__ == '__main__':
    unittest.main()