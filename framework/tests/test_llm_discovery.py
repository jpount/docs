#!/usr/bin/env python3
"""
Test suite for LLM business rule discovery
Tests semantic analysis and pattern discovery
"""

import unittest
import tempfile
from pathlib import Path
import sys
from unittest.mock import patch, Mock, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from discover_llm_business_rules import (
    LLMBusinessRuleDiscoverer,
    write_discovered_rules,
    main
)


class TestLLMDiscovery(unittest.TestCase):
    """Test LLM rule discovery functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.discoverer = LLMBusinessRuleDiscoverer()

    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_search_comments_for_rules(self):
        """Test discovery of rules in comments"""
        content = """
        public class TradeService {
            // TODO: Validate order amount must not exceed $100,000
            public void processOrder(OrderDataBean order) {
                // FIXME: Need to check user permission before processing
                // Business Rule: Orders over $50K require manager approval
                /* NOTE: Commission should be calculated as 0.1% of trade value
                   with minimum of $10 */
            }
        }
        """

        rules = self.discoverer.search_comments_for_rules(content, "TradeService.java")

        self.assertGreater(len(rules), 0)

        # Check specific discoveries
        comments = [r['text'] for r in rules]
        self.assertTrue(any('$100,000' in c for c in comments))
        self.assertTrue(any('manager approval' in c for c in comments))
        self.assertTrue(any('Commission' in c for c in comments))

    def test_search_configuration_for_rules(self):
        """Test discovery of configuration rules"""
        content = """
        max.order.size=10000
        min_balance=500
        timeout.seconds=30
        retry_limit=3
        approval.threshold=50000
        session.expire.minutes=20
        """

        rules = self.discoverer.search_configuration_for_rules(content, "config.properties")

        self.assertGreater(len(rules), 0)

        # Check discovered settings
        settings = {r['setting']: r['value'] for r in rules}
        self.assertIn('maximum_limit_order', settings)
        self.assertIn('minimum_limit_balance', settings)
        self.assertIn('timeout_setting_seconds', settings)

    def test_search_validation_patterns(self):
        """Test discovery of validation patterns"""
        jsp_content = """
        <h:inputText id="amount" value="#{bean.amount}">
            <f:validateDoubleRange minimum="0.01" maximum="99999.99"/>
            <f:validateRequired/>
        </h:inputText>
        """

        rules = self.discoverer.search_validation_patterns(jsp_content, "form.jsp")

        self.assertGreater(len(rules), 0)

        # Check validation types
        validations = [r['validation'] for r in rules]
        self.assertTrue(any('minimum' in v for v in validations))
        self.assertTrue(any('maximum' in v for v in validations))

        js_content = """
        function validateForm() {
            if (username.length < 3) {
                return false;
            }
            if (amount > 10000) {
                showError("Amount too large");
            }
            const emailRegex = /^[\\w-]+@[\\w-]+\\.[\\w]+$/;
            return emailRegex.test(email);
        }
        """

        js_rules = self.discoverer.search_validation_patterns(js_content, "validate.js")
        self.assertGreater(len(js_rules), 0)

    def test_search_error_messages(self):
        """Test discovery of rules from error messages"""
        content = """
        public void validateBalance(BigDecimal balance) {
            if (balance.compareTo(minimumBalance) < 0) {
                throw new ValidationException("Balance cannot be less than minimum required");
            }
            if (dailyLimit.exceeded()) {
                Log.error("Daily transaction limit exceeded for user");
            }
            if (account.isExpired()) {
                addError("Account has expired and must be renewed");
            }
        }
        """

        rules = self.discoverer.search_error_messages(content, "Validator.java")

        self.assertGreater(len(rules), 0)

        # Check error types
        messages = [r['message'] for r in rules]
        self.assertTrue(any('minimum' in m.lower() for m in messages))
        self.assertTrue(any('limit exceeded' in m.lower() for m in messages))
        self.assertTrue(any('expired' in m.lower() for m in messages))

    def test_search_cross_method_workflows(self):
        """Test discovery of cross-method workflows"""
        content = """
        public class OrderService {
            public void processOrder(Order order) {
                validateOrder(order);
                calculateTotal(order);
                if (approved) {
                    persistOrder(order);
                    updateInventory(order);
                }
            }

            private void initializeAccount() {
                // Initialize then update status
                createAccount();
                updateAccountStatus();
            }
        }
        """

        rules = self.discoverer.search_cross_method_workflows(content, "OrderService.java")

        # May find some patterns
        self.assertIsInstance(rules, list)

    def test_search_permission_checks(self):
        """Test discovery of permission rules"""
        content = """
        @Secured("ROLE_ADMIN")
        public void deleteUser(String userId) {
            if (!hasRole("ADMIN")) {
                throw new SecurityException("Insufficient permissions");
            }
        }

        @RolesAllowed("MANAGER")
        public void approveOrder(Order order) {
            if (!hasPermission("ORDER_APPROVE")) {
                return;
            }
            checkAccess(order.getAccountId());
        }
        """

        rules = self.discoverer.search_permission_checks(content, "SecureService.java")

        self.assertGreater(len(rules), 0)

        # Check permissions found
        permissions = [r.get('permission', '') for r in rules]
        self.assertTrue(any('ADMIN' in p for p in permissions))
        self.assertTrue(any('MANAGER' in p for p in permissions))

    def test_create_llm_rule(self):
        """Test creation of formal LLM rule from discovery"""
        discovery = {
            'type': 'comment_rule',
            'text': 'Orders over $50K require manager approval',
            'file_path': 'Trade.java',
            'line': 100,
            'confidence': 'high',
            'category': 'business_rule_comment'
        }

        rule = self.discoverer.create_llm_rule(discovery)

        self.assertEqual(rule['business_rule_id'], 'BR-LLM-001')
        self.assertIn('Orders over $50K', rule['business_rule_description'])
        self.assertEqual(rule['rule_type'], 'llm_discovered')
        self.assertEqual(rule['confidence'], 'high')
        self.assertIsNotNone(rule['business_significance'])

    def test_generate_description(self):
        """Test description generation for different discovery types"""
        test_cases = [
            ({
                'type': 'comment_rule',
                'text': 'Test comment'
            }, 'Business constraint from comment'),
            ({
                'type': 'configuration_rule',
                'setting': 'max_size',
                'value': '1000'
            }, 'Configuration limit'),
            ({
                'type': 'error_constraint_rule',
                'message': 'Invalid amount'
            }, 'Error constraint'),
            ({
                'type': 'permission_rule',
                'check': 'hasRole',
                'permission': 'ADMIN'
            }, 'Permission requirement')
        ]

        for discovery, expected_prefix in test_cases:
            desc = self.discoverer.generate_description(discovery)
            self.assertTrue(desc.startswith(expected_prefix),
                           f"Description '{desc}' doesn't start with '{expected_prefix}'")

    def test_write_discovered_rules(self):
        """Test writing discovered rules to markdown"""
        rules = [
            {
                'business_rule_id': 'BR-LLM-001',
                'business_rule_description': 'Test rule 1',
                'discovery_type': 'comment_rule',
                'file_path': 'Test.java',
                'line': 10,
                'confidence': 'high',
                'category': 'business_rule_comment',
                'business_significance': 'Important rule',
                'evidence': {'text': 'Rule text'}
            },
            {
                'business_rule_id': 'BR-LLM-002',
                'business_rule_description': 'Test rule 2',
                'discovery_type': 'configuration_rule',
                'file_path': 'config.props',
                'line': 20,
                'confidence': 'medium',
                'category': 'maximum_limit',
                'business_significance': 'Sets limits',
                'evidence': {'setting': 'max_value', 'value': '100'}
            }
        ]

        output = Path(self.test_dir) / 'discovered.md'
        write_discovered_rules(rules, str(output))

        self.assertTrue(output.exists())
        content = output.read_text()

        # Check content
        self.assertIn("Additional LLM-Discovered Business Rules", content)
        self.assertIn("BR-LLM-001", content)
        self.assertIn("BR-LLM-002", content)
        self.assertIn("Business Rule Comment", content)
        self.assertIn("Maximum Limit", content)
        self.assertIn("high confidence: 1", content.lower())
        self.assertIn("medium confidence: 1", content.lower())

    def test_discoverer_increments_rule_ids(self):
        """Test that rule IDs increment properly"""
        discoveries = [
            {'type': 'test', 'file_path': 'test.java', 'line': 1,
             'confidence': 'high', 'category': 'test'},
            {'type': 'test', 'file_path': 'test.java', 'line': 2,
             'confidence': 'high', 'category': 'test'}
        ]

        rules = []
        for disc in discoveries:
            rule = self.discoverer.create_llm_rule(disc)
            rules.append(rule)

        self.assertEqual(rules[0]['business_rule_id'], 'BR-LLM-001')
        self.assertEqual(rules[1]['business_rule_id'], 'BR-LLM-002')

    @patch('discover_llm_business_rules.RepomixParser')
    def test_discover_rules_from_repomix(self, mock_parser_class):
        """Test discovery from repomix file"""
        # Create mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Create mock components
        mock_component = MagicMock()
        mock_component.content = [
            "// TODO: Validate amount must be positive",
            "public void process() {",
            "    if (amount > MAX_AMOUNT) {",
            "        throw new Exception('Amount exceeds limit');",
            "    }",
            "}"
        ]
        mock_component.file_path = "Service.java"

        mock_parser.parse.return_value = {
            'classes': [mock_component]
        }

        # Test discovery
        rules = self.discoverer.discover_rules_from_repomix("test.md")

        # Should find at least the comment rule
        self.assertGreater(len(rules), 0)
        self.assertTrue(any(r['discovery_type'] == 'comment_rule' for r in rules))


if __name__ == '__main__':
    unittest.main()