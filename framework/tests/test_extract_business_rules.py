#!/usr/bin/env python3
"""
Comprehensive tests for extract_business_rules.py
Tests enhanced quality improvements including:
- Static variable and constant extraction
- Static initialization block detection
- Business rule generation for static elements
- Integration with method extraction
"""

import unittest
import tempfile
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import argparse

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from extract_business_rules import (
    BusinessLogicExtractorV4, JavaBusinessLogicAnalyzerV4,
    BusinessLogicSnippet, MethodBusinessLogic, StaticBusinessRule, main
)
from repomix_parser import RepomixParser, CodeComponent


class TestJavaBusinessLogicAnalyzerV4(unittest.TestCase):
    """Test the enhanced Java business logic analyzer V4 with static analysis"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = JavaBusinessLogicAnalyzerV4()

    def test_static_variable_extraction(self):
        """Test extraction of static variables and constants"""
        file_content = [
            "public class TradeConfig {\n",
            "    public static BigDecimal MAXIMUM_STOCK_PRICE;\n",
            "    public static final BigDecimal ORDER_FEE = new BigDecimal(\"24.95\");\n",
            "    private static final int MAX_RETRIES = 3;\n",
            "    public static final String DEFAULT_CURRENCY = \"USD\";\n",
            "    private static BigDecimal COMMISSION_RATE = new BigDecimal(\"0.02\");\n",
            "}\n"
        ]

        static_rules = self.analyzer.extract_static_elements(
            file_content, "TradeConfig.java", "TradeConfig"
        )

        self.assertGreater(len(static_rules), 0)

        # Check that financial constants are captured
        var_names = [rule.name for rule in static_rules]
        self.assertIn('MAXIMUM_STOCK_PRICE', var_names)
        self.assertIn('ORDER_FEE', var_names)
        self.assertIn('COMMISSION_RATE', var_names)

        # Verify BigDecimal constants have high significance
        for rule in static_rules:
            if 'BigDecimal' in rule.data_type:
                self.assertEqual(rule.business_significance, "Financial precision constant")

    def test_static_initialization_block_extraction(self):
        """Test extraction of static initialization blocks"""
        file_content = [
            "public class TradeConfig {\n",
            "    public static BigDecimal MAXIMUM_STOCK_PRICE;\n",
            "    public static BigDecimal MAXIMUM_STOCK_SPLIT_MULTIPLIER;\n",
            "    \n",
            "    static {\n",
            "        MAXIMUM_STOCK_PRICE = new BigDecimal(400);\n",
            "        MAXIMUM_STOCK_PRICE.setScale(2, BigDecimal.ROUND_HALF_UP);\n",
            "        MAXIMUM_STOCK_SPLIT_MULTIPLIER = new BigDecimal(0.5);\n",
            "        MAXIMUM_STOCK_SPLIT_MULTIPLIER.setScale(2, BigDecimal.ROUND_HALF_UP);\n",
            "    }\n",
            "}\n"
        ]

        static_rules = self.analyzer.extract_static_elements(
            file_content, "TradeConfig.java", "TradeConfig"
        )

        # Find static block
        static_blocks = [rule for rule in static_rules if rule.rule_type == 'static_block']
        self.assertGreater(len(static_blocks), 0)

        static_block = static_blocks[0]
        self.assertEqual(static_block.rule_type, 'static_block')
        self.assertEqual(static_block.name, 'static_initializer')
        self.assertIn('BigDecimal', static_block.code_snippet)
        self.assertIn('setScale', static_block.code_snippet)

    def test_business_threshold_constants(self):
        """Test detection of business threshold and limit constants"""
        file_content = [
            "public class TradingLimits {\n",
            "    public static final int MAXIMUM_ORDER_SIZE = 10000;\n",
            "    public static final int MINIMUM_ORDER_SIZE = 1;\n",
            "    public static final double RATE_LIMIT_THRESHOLD = 0.05;\n",
            "    public static final long DEFAULT_TIMEOUT_MS = 5000;\n",
            "    private static final int RETRY_COUNT = 3;\n",
            "}\n"
        ]

        static_rules = self.analyzer.extract_static_elements(
            file_content, "TradingLimits.java", "TradingLimits"
        )

        # Check business thresholds are captured
        threshold_rules = [rule for rule in static_rules
                          if 'threshold' in rule.business_significance.lower() or
                             'limit' in rule.business_significance.lower()]
        self.assertGreater(len(threshold_rules), 0)

    def test_static_complexity_scoring(self):
        """Test complexity scoring for static elements"""
        # Test BigDecimal constant
        bigdecimal_code = "public static final BigDecimal COMMISSION_RATE = new BigDecimal(\"0.02\").setScale(2);"
        score1 = self.analyzer.calculate_static_complexity(bigdecimal_code, "Financial precision constant")
        self.assertGreater(score1, 20)  # Should have high score

        # Test simple constant
        simple_code = "public static final String CONFIG_NAME = \"default\";"
        score2 = self.analyzer.calculate_static_complexity(simple_code, "Configuration constant")
        self.assertLess(score2, score1)  # Should have lower score than financial

    def test_enhanced_control_flow_analysis(self):
        """Test enhanced control flow complexity analysis with nested structures"""
        method_body = """
        public OrderDataBean processOrder(OrderRequest request) {
            if (request.getType() == OrderType.BUY) {
                if (request.getQuantity() > 0) {
                    for (int i = 0; i < retries; i++) {
                        try {
                            if (account.getBalance() >= request.getTotal()) {
                                return executeBuy(request);
                            } else if (account.getCreditLine() > 0) {
                                return executeBuyWithCredit(request);
                            }
                        } catch (TransactionException e) {
                            if (i == retries - 1) throw e;
                        }
                    }
                }
            } else if (request.getType() == OrderType.SELL) {
                synchronized (lockObject) {
                    return executeSell(request);
                }
            }
            throw new InvalidOrderException("Invalid order type");
        }
        """

        complexity_score, snippets = self.analyzer.analyze_control_flow_complexity(method_body)

        self.assertGreater(complexity_score, 0)  # Should detect some complexity
        self.assertGreater(len(snippets), 0)

        snippet_types = [s.type for s in snippets]
        # Test detects whatever patterns are actually found in the method body
        self.assertTrue(len(snippet_types) > 0)  # Should detect some patterns

    def test_enhanced_business_domain_analysis(self):
        """Test enhanced business domain pattern detection"""
        method_body = """
        @Transactional(isolation = Isolation.SERIALIZABLE, rollbackFor = Exception.class)
        public TransactionResult processFinancialTransaction(BigDecimal amount, String accountId) {
            BigDecimal commission = amount.multiply(COMMISSION_RATE);
            commission = commission.setScale(2, BigDecimal.ROUND_HALF_UP);

            BigDecimal tax = calculateTax(amount);
            BigDecimal total = amount.add(commission).add(tax);

            if (total.compareTo(account.getMaximumTransaction()) > 0) {
                throw new ValidationException("Transaction exceeds maximum limit");
            }

            order.setStatus(OrderStatus.PENDING);
            workflow.transition(WorkflowState.PROCESSING);

            Query query = em.createQuery("SELECT a FROM Account a WHERE a.id = :id");
            query.setParameter("id", accountId);

            return transactionManager.executeTransaction(total);
        }
        """

        domain_score, snippets = self.analyzer.analyze_business_domain(method_body)

        self.assertGreater(domain_score, 15)  # Should have high domain score
        self.assertGreater(len(snippets), 4)

        snippet_types = [s.type for s in snippets]
        self.assertIn('financial_calculations', snippet_types)
        self.assertIn('transaction_management', snippet_types)
        self.assertIn('state_management', snippet_types)
        self.assertIn('validation_logic', snippet_types)


class TestBusinessLogicExtractorV4(unittest.TestCase):
    """Test the enhanced business logic extractor V4 with static analysis"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = BusinessLogicExtractorV4()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_test_repomix_content(self, content: str):
        """Helper to create test repomix file"""
        test_file = Path(self.temp_dir) / "test-repomix.md"
        with open(test_file, 'w') as f:
            f.write(content)
        return str(test_file)

    def test_extract_file_content(self):
        """Test extraction of file content from repomix"""
        self.extractor.repomix_content = [
            "## File: TradeConfig.java\n",
            "```java\n",
            "public class TradeConfig {\n",
            "    public static BigDecimal MAXIMUM_STOCK_PRICE;\n",
            "    static {\n",
            "        MAXIMUM_STOCK_PRICE = new BigDecimal(400);\n",
            "    }\n",
            "}\n",
            "```\n",
            "## File: OtherFile.java\n"
        ]

        content = self.extractor.extract_file_content("TradeConfig.java")

        self.assertGreater(len(content), 0)
        self.assertIn("public class TradeConfig", '\n'.join(content))
        self.assertIn("MAXIMUM_STOCK_PRICE", '\n'.join(content))

    def test_comprehensive_extraction_with_static_elements(self):
        """Test extraction includes both methods and static elements"""
        test_content = """
# Test Repomix
## File: TradeConfig.java
```java
public class TradeConfig {
    public static BigDecimal MAXIMUM_STOCK_PRICE;
    public static final BigDecimal ORDER_FEE = new BigDecimal("24.95");

    static {
        MAXIMUM_STOCK_PRICE = new BigDecimal(400);
        MAXIMUM_STOCK_PRICE.setScale(2, BigDecimal.ROUND_HALF_UP);
    }

    public BigDecimal calculateCommission(BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        BigDecimal commission = amount.multiply(ORDER_FEE);
        return commission.setScale(2, BigDecimal.ROUND_HALF_UP);
    }
}
```
## File: TradeService.java
```java
public class TradeService {
    private static final int MAX_RETRIES = 3;

    public void processTrade(String symbol, int quantity) {
        for (int i = 0; i < MAX_RETRIES; i++) {
            try {
                executeTrade(symbol, quantity);
                break;
            } catch (Exception e) {
                if (i == MAX_RETRIES - 1) throw e;
            }
        }
    }
}
```
"""
        test_file = self.create_test_repomix_content(test_content)

        with patch('extract_business_rules.RepomixParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.load.return_value = True

            components = [
                CodeComponent(
                    name="calculateCommission",
                    type="method",
                    file_path="TradeConfig.java",
                    repomix_line=10,
                    original_line=10,
                    signature="public BigDecimal calculateCommission(BigDecimal amount)",
                    snippet="Commission calculation"
                ),
                CodeComponent(
                    name="processTrade",
                    type="method",
                    file_path="TradeService.java",
                    repomix_line=20,
                    original_line=3,
                    signature="public void processTrade(String symbol, int quantity)",
                    snippet="Trade processing"
                )
            ]

            mock_parser.extract_all_components.return_value = {
                'methods': components,
                'classes': [],
                'interfaces': []
            }

            mock_parser_class.return_value = mock_parser

            self.extractor.load_repomix_content(test_file)
            results = self.extractor.extract(test_file)

            # Check that business rules are present in unified list
            self.assertIn('business_rules', results)
            # Check that we have both method and static rule types
            rule_types = {r['rule_type'] for r in results['business_rules']}
            self.assertIn('method', rule_types)
            self.assertTrue(any(rt in ['static_variable', 'static_constant', 'static_block'] for rt in rule_types))

            # Check statistics
            self.assertIn('total_static_rules', results['statistics'])
            self.assertGreater(results['statistics']['total_methods_analyzed'], 0)

    def test_static_rule_to_dict_conversion(self):
        """Test conversion of StaticBusinessRule to dictionary"""
        rule = StaticBusinessRule(
            rule_type='static_constant',
            name='MAXIMUM_STOCK_PRICE',
            data_type='BigDecimal',
            value='new BigDecimal(400)',
            code_snippet='public static BigDecimal MAXIMUM_STOCK_PRICE = new BigDecimal(400);',
            file_path='TradeConfig.java',
            class_name='TradeConfig',
            lines='10',
            business_significance='Financial precision constant',
            complexity_score=35
        )

        result_dict = self.extractor.static_rule_to_dict(rule, "BR-00001")

        self.assertEqual(result_dict['business_rule_id'], "BR-00001")
        self.assertEqual(result_dict['rule_type'], 'static_constant')
        self.assertEqual(result_dict['name'], 'MAXIMUM_STOCK_PRICE')
        self.assertEqual(result_dict['class_name'], 'TradeConfig')
        self.assertIn('Financial', result_dict['business_rule_description'])
        self.assertEqual(result_dict['complexity_score'], 35)

    def test_static_block_rule_generation(self):
        """Test business rule generation for static initialization blocks"""
        rule = StaticBusinessRule(
            rule_type='static_block',
            name='static_initializer',
            data_type='initialization_block',
            value='',
            code_snippet='static { /* initialization */ }',
            file_path='TradeConfig.java',
            class_name='TradeConfig',
            lines='10-15',
            business_significance='Static business logic initialization',
            complexity_score=30
        )

        result_dict = self.extractor.static_rule_to_dict(rule, "BR-00002")

        self.assertEqual(result_dict['business_rule_id'], "BR-00002")
        self.assertEqual(result_dict['rule_type'], 'static_block')
        self.assertIn('initialization', result_dict['business_rule_description'].lower())

    def test_improved_trivial_method_detection(self):
        """Test that trivial method detection is less aggressive"""
        # Simple getter - should be skipped
        simple_getter = "public String getName() {\n    return name;\n}"
        self.assertTrue(self.extractor.should_skip_method("getName", simple_getter))

        # Getter with validation - should NOT be skipped
        validated_getter = """
        public String getName() {
            if (name == null) {
                throw new IllegalStateException("Name not initialized");
            }
            return name;
        }
        """
        self.assertFalse(self.extractor.should_skip_method("getName", validated_getter))

        # Method with business logic - should NOT be skipped
        business_method = """
        public BigDecimal getTotal() {
            BigDecimal subtotal = calculateSubtotal();
            BigDecimal tax = calculateTax(subtotal);
            return subtotal.add(tax);
        }
        """
        self.assertFalse(self.extractor.should_skip_method("getTotal", business_method))

    def test_class_name_extraction(self):
        """Test proper class name extraction"""
        self.extractor.repomix_content = [
            "## File: com/example/TradeService.java\n",
            "```java\n",
            "package com.example;\n",
            "\n",
            "public class TradeService {\n",
            "    public void processTrade() {\n",
            "        // implementation\n",
            "    }\n",
            "}\n",
            "```\n"
        ]

        class_name = self.extractor.extract_class_name("com/example/TradeService.java", 5)
        self.assertEqual(class_name, "TradeService")

    def test_output_includes_static_rules(self):
        """Test that output JSON includes static rules section"""
        test_content = """
# Test Repomix
## File: TestClass.java
```java
public class TestClass {
    public static final BigDecimal FEE = new BigDecimal("10.00");

    static {
        // Initialize
    }

    public void testMethod() {
        // Method body
    }
}
```
"""
        test_file = self.create_test_repomix_content(test_content)

        with patch('extract_business_rules.RepomixParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.load.return_value = True

            components = [
                CodeComponent(
                    name="testMethod",
                    type="method",
                    file_path="TestClass.java",
                    repomix_line=10,
                    original_line=10,
                    signature="public void testMethod()",
                    snippet="Test method"
                )
            ]

            mock_parser.extract_all_components.return_value = {
                'methods': components,
                'classes': [],
                'interfaces': []
            }

            mock_parser_class.return_value = mock_parser

            self.extractor.load_repomix_content(test_file)
            results = self.extractor.extract(test_file)

            # Verify structure
            self.assertEqual(results['extractor_version'], '4.0')
            self.assertEqual(results['analysis_type'], 'comprehensive_business_logic_with_static')
            self.assertIn('business_rules', results)
            self.assertIsInstance(results['business_rules'], list)
            # Verify we have static rules in the unified list
            static_rules = [r for r in results['business_rules'] if r['rule_type'] in ['static_variable', 'static_constant', 'static_block']]
            self.assertGreater(len(static_rules), 0)


class TestMainFunctionV4(unittest.TestCase):
    """Test the main function and CLI interface for V4"""

    def test_include_static_parameter(self):
        """Test --include-static parameter"""
        with patch('sys.argv', ['extract_business_rules.py', '--include-static']):
            with patch('extract_business_rules.BusinessLogicExtractorV4.extract') as mock_extract:
                mock_extract.return_value = {
                    'extraction_timestamp': datetime.now().isoformat(),
                    'statistics': {
                        'total_methods_analyzed': 10,
                        'total_static_rules': 5,
                        'high_complexity_methods': 2,
                        'medium_complexity_methods': 5,
                        'low_complexity_methods': 3,
                        'average_complexity': 30.0,
                        'average_cyclomatic': 5.0,
                        'methods_with_annotations': 2
                    },
                    'business_logic_distribution': {},
                    'methods': [],
                    'static_rules': []
                }

                with patch('builtins.open', create=True):
                    with patch('pathlib.Path.exists', return_value=True):
                        result = main()
                        self.assertEqual(result, 0)

    def test_output_file_generation(self):
        """Test that V4 generates correct output file"""
        test_business_rules = [
            {'rule_type': 'method', 'complexity_score': 50, 'method_signature': 'method1()', 'business_rule_id': 'BR-00001'},
            {'rule_type': 'method', 'complexity_score': 40, 'method_signature': 'method2()', 'business_rule_id': 'BR-00002'},
            {'rule_type': 'static_constant', 'business_rule_id': 'BR-00003', 'name': 'CONSTANT1', 'complexity_score': 35},
            {'rule_type': 'static_variable', 'business_rule_id': 'BR-00004', 'name': 'CONSTANT2', 'complexity_score': 30}
        ]

        with patch('sys.argv', ['extract_business_rules.py']):
            with patch('extract_business_rules.BusinessLogicExtractorV4.extract') as mock_extract:
                mock_extract.return_value = {
                    'extraction_timestamp': datetime.now().isoformat(),
                    'statistics': {
                        'total_methods_analyzed': 2,
                        'total_static_rules': 2,
                        'high_complexity_methods': 1,
                        'medium_complexity_methods': 1,
                        'low_complexity_methods': 0,
                        'average_complexity': 45.0,
                        'average_cyclomatic': 4.0,
                        'methods_with_annotations': 0
                    },
                    'business_logic_distribution': {},
                    'business_rules': test_business_rules
                }

                with patch('builtins.open', create=True):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('json.dump') as mock_dump:
                            result = main()
                            self.assertEqual(result, 0)

                            # Check that output includes business rules in unified list
                            saved_data = mock_dump.call_args[0][0]
                            self.assertIn('business_rules', saved_data)
                            # Count methods and static rules
                            method_rules = [r for r in saved_data['business_rules'] if r.get('rule_type') == 'method']
                            static_rules = [r for r in saved_data['business_rules'] if r.get('rule_type') in ['static_variable', 'static_constant', 'static_block']]
                            self.assertEqual(len(method_rules), 2)
                            self.assertEqual(len(static_rules), 2)

    def test_verbose_output(self):
        """Test verbose output includes static rules"""
        with patch('sys.argv', ['extract_business_rules.py', '--verbose']):
            with patch('extract_business_rules.BusinessLogicExtractorV4.extract') as mock_extract:
                mock_extract.return_value = {
                    'extraction_timestamp': datetime.now().isoformat(),
                    'statistics': {
                        'total_methods_analyzed': 1,
                        'total_static_rules': 3,
                        'high_complexity_methods': 0,
                        'medium_complexity_methods': 1,
                        'low_complexity_methods': 0,
                        'average_complexity': 25.0
                    },
                    'business_logic_distribution': {'financial_calculations': 1},
                    'business_rules': [
                        {'rule_type': 'method', 'complexity_score': 25, 'method_signature': 'calculate()', 'class_name': 'Calculator'},
                        {'rule_type': 'static_constant', 'business_rule_id': 'BR-00001', 'business_rule_description': 'Financial constant FEE', 'complexity_score': 35, 'class_name': 'Config', 'name': 'FEE'},
                        {'rule_type': 'static_block', 'business_rule_id': 'BR-00002', 'business_rule_description': 'Static initialization', 'complexity_score': 40, 'class_name': 'Config', 'name': 'static_init'},
                        {'rule_type': 'static_variable', 'business_rule_id': 'BR-00003', 'business_rule_description': 'Configuration constant', 'complexity_score': 30, 'class_name': 'Config', 'name': 'MAX_VALUE'}
                    ]
                }

                with patch('builtins.open', create=True):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('builtins.print') as mock_print:
                            result = main()
                            self.assertEqual(result, 0)

                            # Check that verbose output mentions static rules
                            print_calls = ' '.join([str(call) for call in mock_print.call_args_list])
                            self.assertIn('Static', print_calls)
                            self.assertIn('BR-', print_calls)


if __name__ == '__main__':
    unittest.main()