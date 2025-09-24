#!/usr/bin/env python3
"""
Test suite for Business Rules Merger
Tests merging of deterministic rules with LLM analysis
"""

import unittest
import tempfile
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from merge_business_rules_with_analysis import BusinessRuleMerger


class TestBusinessRuleMerger(unittest.TestCase):
    """Test business rules merging functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.merger = BusinessRuleMerger()

        # Create sample deterministic rules file
        self.det_file = Path(self.test_dir) / 'deterministic.md'
        det_content = """# Complete Deterministic Business Rules Catalog

**Generated**: 2025-09-24 10:00:00
**Total Rules**: 3

---

## Part 1: Method-Based Business Rules

### BR-00001: Execute sell order

**Type**: method
**Location**: `TradeSLSB.java:175-224`
**Class**: `TradeSLSB`
**Method Signature**: `sell(String userID, Integer holdingID)`
**Complexity Score**: 93

#### Implementation

```java
public OrderDataBean sell(String userID, Integer holdingID) {
    // Sell implementation code
    return order;
}
```

*Extracted via: Deterministic pattern matching (Python)*

---

### BR-00002: Process buy order

**Type**: method
**Location**: `TradeSLSB.java:250-300`
**Class**: `TradeSLSB`
**Method Signature**: `buy(String userID, String symbol, double quantity)`

#### Implementation

```java
public OrderDataBean buy(String userID, String symbol, double quantity) {
    // Buy implementation code
    return order;
}
```

---

### BR-00003: Order fee constant

**Type**: static_constant
**Location**: `TradeConfig.java:50`
**Name**: `ORDER_FEE`

#### Implementation

```java
public static final BigDecimal ORDER_FEE = new BigDecimal("24.95");
```

---
"""
        self.det_file.write_text(det_content)

        # Create sample LLM analysis file
        self.analysis_file = Path(self.test_dir) / 'analysis.md'
        analysis_content = """# LLM Analysis of Business Rules

**Generated**: 2025-09-24 10:30:00

---

## BR-00001: Execute sell order

**Type**: method

### What This Method Actually Does

- Processes a sell order by retrieving the holding from database
- Validates that the holding exists and belongs to the user
- Calculates the sale proceeds based on current quote price
- Updates account balance with the net proceeds

### Specific Business Rules

- User must own the holding to sell it
- Commission is deducted from proceeds
- Holding is marked as sold

### Why This Is Important

- Core trading functionality
- Ensures accurate financial calculations
- Maintains data integrity

---

## BR-00002: Process buy order

### What This Method Actually Does

- Creates a buy order for specified quantity of shares
- Validates account has sufficient balance
- Creates new holding record in portfolio

### Specific Business Rules

- Account must have sufficient funds
- Order fees are applied
- Holdings are tracked

---

## BR-00003: Order fee constant

### Business Purpose

- Defines standard trading fee
- Used in all order calculations

### Usage & Impact

- Affects all trading operations
- Critical for revenue calculations

---
"""
        self.analysis_file.write_text(analysis_content)

        # Output file
        self.output_file = Path(self.test_dir) / 'merged.md'

    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_deterministic_file(self):
        """Test parsing of deterministic rules file"""
        rules = self.merger.parse_deterministic_file(str(self.det_file))

        self.assertEqual(len(rules), 3)
        self.assertIn('BR-00001', rules)
        self.assertIn('BR-00002', rules)
        self.assertIn('BR-00003', rules)

        # Check content extraction
        br1 = rules['BR-00001']
        self.assertIn('Execute sell order', br1)
        self.assertIn('```java', br1)
        self.assertIn('public OrderDataBean sell', br1)

    def test_parse_analysis_file(self):
        """Test parsing of LLM analysis file"""
        analysis = self.merger.parse_analysis_file(str(self.analysis_file))

        self.assertEqual(len(analysis), 3)
        self.assertIn('BR-00001', analysis)

        # Check content extraction
        br1_analysis = analysis['BR-00001']
        self.assertIn('What This Method Actually Does', br1_analysis)
        self.assertIn('Specific Business Rules', br1_analysis)
        self.assertIn('Why This Is Important', br1_analysis)
        # Should NOT include the duplicate header
        self.assertNotIn('## BR-00001:', br1_analysis)

    def test_merge_rule(self):
        """Test merging a single rule with its analysis"""
        det_content = """### BR-00001: Test rule

**Type**: method
**Location**: Test.java:1-10

#### Implementation

```java
public void test() {
    // code
}
```

---"""

        analysis_content = """### What This Method Actually Does

- Does something important

### Why This Is Important

- Very important for business"""

        merged = self.merger.merge_rule('BR-00001', det_content, analysis_content)

        # Check merged content
        self.assertIn('### BR-00001: Test rule', merged)
        self.assertIn('#### Implementation', merged)
        self.assertIn('```java', merged)
        self.assertIn('#### 🔍 LLM Analysis', merged)
        self.assertIn('What This Method Actually Does', merged)
        self.assertIn('Why This Is Important', merged)
        self.assertIn('---', merged)

    def test_merge_rule_without_analysis(self):
        """Test merging when no analysis is available"""
        det_content = """### BR-00099: Test rule without analysis

**Type**: method

#### Implementation

```java
public void test() {}
```
"""

        merged = self.merger.merge_rule('BR-00099', det_content, None)

        self.assertIn('### BR-00099:', merged)
        self.assertIn('#### 🔍 LLM Analysis', merged)
        self.assertIn('*No LLM analysis available for this rule*', merged)

    def test_merge_all_rules(self):
        """Test merging all rules"""
        det_rules = self.merger.parse_deterministic_file(str(self.det_file))
        analysis = self.merger.parse_analysis_file(str(self.analysis_file))

        merged = self.merger.merge_all_rules(det_rules, analysis)

        self.assertEqual(len(merged), 3)

        # Check order is preserved
        rule_ids = [rule_id for rule_id, _ in merged]
        self.assertEqual(rule_ids, ['BR-00001', 'BR-00002', 'BR-00003'])

        # Check content is merged
        for rule_id, content in merged:
            self.assertIn(f'### {rule_id}:', content)
            self.assertIn('#### Implementation', content)
            self.assertIn('#### 🔍 LLM Analysis', content)

    def test_write_merged_file(self):
        """Test writing merged file"""
        merged_rules = [
            ('BR-00001', '### BR-00001: Rule 1\n\nContent 1\n\n---\n\n'),
            ('BR-00002', '### BR-00002: Rule 2\n\nContent 2\n\n---\n\n'),
        ]

        written = self.merger.write_merged_file(
            merged_rules,
            str(self.output_file),
            batch_size=1  # Small batch for testing
        )

        self.assertEqual(written, 2)
        self.assertTrue(self.output_file.exists())

        content = self.output_file.read_text()
        self.assertIn('# Complete Business Rules with LLM Analysis', content)
        self.assertIn('Total Rules: 2', content)
        self.assertIn('BR-00001', content)
        self.assertIn('BR-00002', content)
        self.assertIn('Successfully merged **2** business rules', content)

    def test_full_merge_process(self):
        """Test complete merge process"""
        result = self.merger.merge(
            str(self.det_file),
            str(self.analysis_file),
            str(self.output_file),
            batch_size=2
        )

        self.assertEqual(result, 3)
        self.assertTrue(self.output_file.exists())

        content = self.output_file.read_text()

        # Check all rules are present
        self.assertIn('BR-00001', content)
        self.assertIn('BR-00002', content)
        self.assertIn('BR-00003', content)

        # Check merged content structure
        self.assertIn('Execute sell order', content)
        self.assertIn('public OrderDataBean sell', content)
        self.assertIn('What This Method Actually Does', content)
        self.assertIn('Processes a sell order', content)

        # Check BR-00002 has both parts
        self.assertIn('Process buy order', content)
        self.assertIn('Creates a buy order for specified quantity', content)

        # Check BR-00003 has both parts
        self.assertIn('Order fee constant', content)
        self.assertIn('Defines standard trading fee', content)

    def test_missing_input_files(self):
        """Test error handling for missing files"""
        result = self.merger.merge(
            'nonexistent.md',
            str(self.analysis_file),
            str(self.output_file)
        )

        self.assertEqual(result, 0)

    def test_rule_id_sorting(self):
        """Test that rules are sorted by ID number"""
        det_rules = {
            'BR-00010': 'Content 10',
            'BR-00002': 'Content 2',
            'BR-00100': 'Content 100',
            'BR-00001': 'Content 1'
        }

        analysis = {}

        merged = self.merger.merge_all_rules(det_rules, analysis)

        # Check rules are sorted numerically
        rule_ids = [rule_id for rule_id, _ in merged]
        self.assertEqual(rule_ids, ['BR-00001', 'BR-00002', 'BR-00010', 'BR-00100'])

    def test_batch_writing(self):
        """Test that batch writing works correctly"""
        # Create many rules to test batching
        merged_rules = []
        for i in range(1, 21):
            rule_id = f'BR-{i:05d}'
            content = f'### {rule_id}: Rule {i}\n\nContent\n\n---\n\n'
            merged_rules.append((rule_id, content))

        written = self.merger.write_merged_file(
            merged_rules,
            str(self.output_file),
            batch_size=5  # Process 5 at a time
        )

        self.assertEqual(written, 20)
        self.assertTrue(self.output_file.exists())

        content = self.output_file.read_text()
        # Check all rules made it
        for i in range(1, 21):
            self.assertIn(f'BR-{i:05d}', content)


if __name__ == '__main__':
    unittest.main()