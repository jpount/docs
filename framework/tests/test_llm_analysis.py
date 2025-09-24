#!/usr/bin/env python3
"""
Test suite for LLM business rule analysis
Tests the generation of insights and analysis for each rule
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock
import os

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from analyze_business_rules_llm import (
    load_extracted_rules,
    analyze_method_rule,
    analyze_static_rule,
    generate_llm_analysis_section,
    write_analysis_incrementally,
    main
)


class TestLLMAnalysis(unittest.TestCase):
    """Test LLM analysis generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_json = Path(self.test_dir) / 'test_rules.json'
        self.test_output = Path(self.test_dir) / 'test_analysis.md'

        # Sample rules for testing
        self.sample_data = {
            "business_rules": [
                {
                    "business_rule_id": "BR-00001",
                    "business_rule_description": "Execute sell order",
                    "rule_type": "method",
                    "method_signature": "sell(String userID, Integer holdingID)",
                    "file_path": "TradeSLSB.java",
                    "class_name": "TradeSLSB",
                    "lines": "175-224",
                    "complexity_score": 93,
                    "business_logic_types": ["financial_calculations", "transaction_management"],
                    "full_method_source": """
                    public OrderDataBean sell(String userID, Integer holdingID) {
                        OrderDataBean order;
                        BigDecimal total;
                        try {
                            HoldingDataBean holding = entityManager.find(HoldingDataBean.class, holdingID);
                            if (holding == null) {
                                throw new Exception("Holding not found");
                            }
                            QuoteDataBean quote = holding.getQuote();
                            double quantity = holding.getQuantity();
                            order = createOrder(account, quote, holding, "sell", quantity);
                            BigDecimal price = quote.getPrice();
                            BigDecimal orderFee = order.getOrderFee();
                            BigDecimal balance = account.getBalance();
                            total = (new BigDecimal(quantity).multiply(price)).subtract(orderFee);
                            account.setBalance(balance.add(total));
                            completeOrder(order.getOrderID(), false);
                        } catch (Exception e) {
                            Log.error("Error in sell", e);
                            throw new EJBException("Sell failed", e);
                        }
                        return order;
                    }
                    """
                },
                {
                    "business_rule_id": "BR-00002",
                    "business_rule_description": "Order fee configuration",
                    "rule_type": "static_constant",
                    "name": "ORDER_FEE",
                    "data_type": "BigDecimal",
                    "file_path": "TradeConfig.java",
                    "lines": "50",
                    "code_snippet": "public static final BigDecimal ORDER_FEE = new BigDecimal(\"24.95\");",
                    "business_significance": "Financial precision constant"
                }
            ],
            "statistics": {
                "total_business_rules": 2
            }
        }

        # Write test JSON
        with open(self.test_json, 'w') as f:
            json.dump(self.sample_data, f)

    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_analyze_method_rule(self):
        """Test analysis of method rule"""
        rule = self.sample_data['business_rules'][0]
        analysis = analyze_method_rule(rule)

        # Check analysis structure
        self.assertIn('what_it_does', analysis)
        self.assertIn('business_rules', analysis)
        self.assertIn('validation_handling', analysis)
        self.assertIn('state_changes', analysis)
        self.assertIn('why_important', analysis)

        # Check sell-specific analysis
        what_it_does = analysis['what_it_does']
        self.assertTrue(any('sell order' in item.lower() for item in what_it_does))
        self.assertTrue(any('holding' in item.lower() for item in what_it_does))

        # Check business rules detection
        biz_rules = analysis['business_rules']
        self.assertTrue(any('precision arithmetic' in item.lower() for item in biz_rules))

        # Check state changes
        state_changes = analysis['state_changes']
        self.assertTrue(any('balance' in item.lower() for item in state_changes))

    def test_analyze_static_rule(self):
        """Test analysis of static rule"""
        rule = self.sample_data['business_rules'][1]
        analysis = analyze_static_rule(rule)

        # Check structure
        self.assertIn('business_purpose', analysis)
        self.assertIn('usage_impact', analysis)
        self.assertIn('relationships', analysis)

        # Check content
        purpose = analysis['business_purpose']
        self.assertTrue(any('financial' in item.lower() or 'fee' in item.lower()
                           for item in purpose))

        impact = analysis['usage_impact']
        self.assertTrue(any('immutable' in item.lower() or 'consistent' in item.lower()
                           for item in impact))

    def test_generate_llm_analysis_section(self):
        """Test markdown generation for analysis"""
        rule = self.sample_data['business_rules'][0]
        analysis = analyze_method_rule(rule)
        section = generate_llm_analysis_section(rule, analysis)

        # Check markdown structure
        self.assertIn("## BR-00001:", section)
        self.assertIn("### What This Method Actually Does", section)
        self.assertIn("### Specific Business Rules", section)
        self.assertIn("### State Changes & Side Effects", section)
        self.assertIn("### Why This Is Important", section)

    def test_write_analysis_incrementally(self):
        """Test incremental writing of analysis"""
        rules = self.sample_data['business_rules']

        analyzed = write_analysis_incrementally(
            rules,
            str(self.test_output),
            batch_size=1  # Small batch for testing
        )

        self.assertEqual(analyzed, 2)
        self.assertTrue(self.test_output.exists())

        # Check content
        content = self.test_output.read_text()
        self.assertIn("LLM Analysis of Business Rules", content)
        self.assertIn("BR-00001", content)
        self.assertIn("BR-00002", content)
        self.assertIn("What This Method Actually Does", content)
        self.assertIn("Business Purpose", content)

    def test_financial_calculation_detection(self):
        """Test detection of financial calculations"""
        rule = {
            "business_rule_id": "BR-TEST",
            "rule_type": "method",
            "method_signature": "calculateInterest(BigDecimal principal, BigDecimal rate)",
            "business_logic_types": ["financial_calculations"],
            "complexity_score": 30,
            "full_method_source": """
            public BigDecimal calculateInterest(BigDecimal principal, BigDecimal rate) {
                BigDecimal interest = principal.multiply(rate);
                interest = interest.setScale(2, BigDecimal.ROUND_HALF_UP);
                return interest;
            }
            """
        }

        analysis = analyze_method_rule(rule)

        # Should detect financial calculations
        what_it_does = analysis['what_it_does']
        self.assertTrue(any('financial' in item.lower() for item in what_it_does))

        biz_rules = analysis['business_rules']
        self.assertTrue(any('precision' in item.lower() for item in biz_rules))
        self.assertTrue(any('rounding' in item.lower() for item in biz_rules))

    def test_validation_logic_detection(self):
        """Test detection of validation logic"""
        rule = {
            "business_rule_id": "BR-VAL",
            "rule_type": "method",
            "method_signature": "validateOrder(OrderDataBean order)",
            "business_logic_types": ["validation_logic"],
            "complexity_score": 25,
            "full_method_source": """
            public boolean validateOrder(OrderDataBean order) {
                if (order == null) {
                    throw new ValidationException("Order cannot be null");
                }
                if (order.getQuantity() <= 0) {
                    throw new ValidationException("Quantity must be positive");
                }
                if (order.getPrice().compareTo(BigDecimal.ZERO) <= 0) {
                    throw new ValidationException("Price must be positive");
                }
                return true;
            }
            """
        }

        analysis = analyze_method_rule(rule)

        # Should detect validation patterns
        biz_rules = analysis['business_rules']
        self.assertTrue(any('null check' in item.lower() for item in biz_rules))
        self.assertTrue(any('threshold' in item.lower() or 'validation' in item.lower()
                           for item in biz_rules))

    def test_main_function(self):
        """Test main function execution"""
        with patch('sys.argv', ['test',
                               '--input', str(self.test_json),
                               '--output', str(self.test_output),
                               '--batch-size', '1']):
            result = main()
            self.assertEqual(result, 0)

        # Verify output
        self.assertTrue(self.test_output.exists())
        content = self.test_output.read_text()
        self.assertIn("Successfully analyzed **2** out of **2** business rules", content)

    def test_error_handling(self):
        """Test error handling for missing input"""
        with patch('sys.argv', ['test',
                               '--input', 'nonexistent.json',
                               '--output', str(self.test_output)]):
            result = main()
            self.assertEqual(result, 1)

    def test_batch_processing(self):
        """Test batch processing with multiple rules"""
        # Create larger dataset
        large_data = {"business_rules": [], "statistics": {}}
        for i in range(10):
            rule = {
                "business_rule_id": f"BR-{i+1:05d}",
                "business_rule_description": f"Test rule {i+1}",
                "rule_type": "method",
                "method_signature": f"method{i+1}()",
                "complexity_score": 30,
                "business_logic_types": ["test"],
                "full_method_source": f"public void method{i+1}() {{ /* code */ }}"
            }
            large_data["business_rules"].append(rule)

        # Write large dataset
        large_json = Path(self.test_dir) / 'large.json'
        with open(large_json, 'w') as f:
            json.dump(large_data, f)

        # Process with batches
        output = Path(self.test_dir) / 'large_analysis.md'
        analyzed = write_analysis_incrementally(
            large_data['business_rules'],
            str(output),
            batch_size=3
        )

        self.assertEqual(analyzed, 10)
        content = output.read_text()
        for i in range(1, 11):
            self.assertIn(f"BR-{i:05d}", content)


if __name__ == '__main__':
    unittest.main()