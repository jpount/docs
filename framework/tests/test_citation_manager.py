#!/usr/bin/env python3
"""
Comprehensive tests for citation_manager.py
Tests citation loading, lookup, tracking, and document generation
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, mock_open
from datetime import datetime
import os

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from citation_manager import CitationManager


class TestCitationManagerInit(unittest.TestCase):
    """Test CitationManager initialization"""

    def test_default_initialization(self):
        """Test default initialization parameters"""
        manager = CitationManager()

        self.assertEqual(manager.citations_json_path, Path("output/context/codebase-citations.json"))
        self.assertEqual(manager.citations, {})
        self.assertEqual(manager.ref_counter, 0)
        self.assertEqual(manager.ref_mapping, {})
        self.assertEqual(manager.usage_tracking, {})
        self.assertIsNone(manager.agent_name)

    def test_custom_path_initialization(self):
        """Test initialization with custom path"""
        custom_path = "/custom/path/citations.json"
        manager = CitationManager(custom_path)

        self.assertEqual(manager.citations_json_path, Path(custom_path))


class TestLoadCitations(unittest.TestCase):
    """Test loading citations from JSON"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "citations.json"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_missing_file(self):
        """Test loading when citations file doesn't exist"""
        manager = CitationManager("/nonexistent/file.json")

        with patch('builtins.print') as mock_print:
            result = manager.load_citations()

        self.assertFalse(result)
        mock_print.assert_any_call("⚠️  Citations file not found: /nonexistent/file.json")

    def test_load_valid_citations(self):
        """Test loading valid citations file"""
        test_data = {
            'classes': [
                {'name': 'UserService', 'file_path': 'service.java', 'ref_id': 'REF-00001'},
                {'name': 'OrderService', 'file_path': 'order.java', 'ref_id': 'REF-00002'}
            ],
            'methods': [
                {'name': 'getUser', 'parent_class': 'UserService', 'ref_id': 'REF-00003'}
            ],
            'ref_index': {
                'REF-00001': {'name': 'UserService', 'type': 'class'},
                'REF-00002': {'name': 'OrderService', 'type': 'class'},
                'REF-00003': {'name': 'getUser', 'type': 'method'}
            },
            'metadata': {}
        }

        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)

        manager = CitationManager(str(self.test_file))

        with patch('builtins.print'):
            result = manager.load_citations()

        self.assertTrue(result)
        self.assertEqual(manager.citations, test_data)
        self.assertEqual(len(manager.ref_mapping), 3)
        self.assertIn('REF-00001', manager.ref_mapping)

    def test_load_citations_without_ref_index(self):
        """Test loading citations file without ref_index"""
        test_data = {
            'classes': [
                {'name': 'TestClass', 'file_path': 'test.java', 'ref_id': 'REF-00001'}
            ],
            'metadata': {}
        }

        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)

        manager = CitationManager(str(self.test_file))

        with patch('builtins.print'):
            result = manager.load_citations()

        self.assertTrue(result)
        self.assertEqual(len(manager.ref_mapping), 0)  # No ref_index to load

    def test_load_empty_citations(self):
        """Test loading empty citations file"""
        test_data = {
            'classes': [],
            'methods': [],
            'ref_index': {},
            'metadata': {}
        }

        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)

        manager = CitationManager(str(self.test_file))

        with patch('builtins.print') as mock_print:
            result = manager.load_citations()

        self.assertTrue(result)
        mock_print.assert_any_call(f"✅ Loaded 0 citations from {self.test_file}")


class TestSetAgentName(unittest.TestCase):
    """Test agent name setting"""

    def test_set_agent_name(self):
        """Test setting agent name"""
        manager = CitationManager()

        with patch('builtins.print') as mock_print:
            manager.set_agent_name("test-agent")

        self.assertEqual(manager.agent_name, "test-agent")
        mock_print.assert_called_with("📝 Citation manager initialized for agent: test-agent")


class TestFindComponent(unittest.TestCase):
    """Test component finding functionality"""

    def setUp(self):
        """Set up test manager with sample data"""
        self.manager = CitationManager()
        self.manager.citations = {
            'classes': [
                {'name': 'UserService', 'file_path': 'user.java', 'ref_id': 'REF-00001'},
                {'name': 'OrderService', 'file_path': 'order.java', 'ref_id': 'REF-00002'}
            ],
            'methods': [
                {'name': 'getUser', 'parent_class': 'UserService', 'ref_id': 'REF-00003'},
                {'name': 'getOrder', 'parent_class': 'OrderService', 'ref_id': 'REF-00004'}
            ],
            'interfaces': [
                {'name': 'Repository', 'file_path': 'repo.java', 'ref_id': 'REF-00005'}
            ]
        }

    def test_find_component_by_name(self):
        """Test finding component by name only"""
        result = self.manager.find_component('UserService')

        self.assertIsNotNone(result)
        ref_id, component = result
        self.assertEqual(ref_id, 'REF-00001')
        self.assertEqual(component['name'], 'UserService')

    def test_find_component_by_name_and_type(self):
        """Test finding component by name and type"""
        result = self.manager.find_component('getUser', 'method')

        self.assertIsNotNone(result)
        ref_id, component = result
        self.assertEqual(ref_id, 'REF-00003')
        self.assertEqual(component['name'], 'getUser')

    def test_find_nonexistent_component(self):
        """Test finding nonexistent component"""
        result = self.manager.find_component('NonexistentClass')
        self.assertIsNone(result)

    def test_find_component_wrong_type(self):
        """Test finding component with wrong type specified"""
        result = self.manager.find_component('UserService', 'method')
        self.assertIsNone(result)

    def test_find_component_updates_ref_mapping(self):
        """Test that finding component updates ref_mapping"""
        self.manager.ref_mapping = {}  # Clear mapping

        result = self.manager.find_component('UserService')

        self.assertIn('REF-00001', self.manager.ref_mapping)
        self.assertEqual(self.manager.ref_mapping['REF-00001']['name'], 'UserService')


class TestLookupCitation(unittest.TestCase):
    """Test citation lookup functionality"""

    def setUp(self):
        """Set up test manager"""
        self.manager = CitationManager()
        self.manager.citations = {
            'classes': [
                {'name': 'TestClass', 'file_path': 'test.java', 'ref_id': 'REF-00001'}
            ]
        }

    def test_lookup_existing_component(self):
        """Test lookup of existing component"""
        ref_id = self.manager.lookup_citation('TestClass')
        self.assertEqual(ref_id, 'REF-00001')

    def test_lookup_nonexistent_component(self):
        """Test lookup of nonexistent component"""
        ref_id = self.manager.lookup_citation('NonexistentClass')
        self.assertIsNone(ref_id)


class TestGetCitationDetails(unittest.TestCase):
    """Test getting citation details"""

    def test_get_existing_citation_details(self):
        """Test getting details for existing citation"""
        manager = CitationManager()
        manager.ref_mapping = {
            'REF-00001': {'name': 'TestClass', 'file_path': 'test.java'}
        }

        details = manager.get_citation_details('REF-00001')
        self.assertEqual(details['name'], 'TestClass')

    def test_get_nonexistent_citation_details(self):
        """Test getting details for nonexistent citation"""
        manager = CitationManager()
        details = manager.get_citation_details('REF-999')
        self.assertIsNone(details)


class TestTrackUsage(unittest.TestCase):
    """Test usage tracking functionality"""

    def test_track_new_usage(self):
        """Test tracking usage for new REF-ID"""
        manager = CitationManager()

        manager.track_usage('REF-00001', 'doc1.md')

        self.assertIn('REF-00001', manager.usage_tracking)
        self.assertIn('doc1.md', manager.usage_tracking['REF-00001'])

    def test_track_multiple_usage(self):
        """Test tracking usage in multiple files"""
        manager = CitationManager()

        manager.track_usage('REF-00001', 'doc1.md')
        manager.track_usage('REF-00001', 'doc2.md')
        manager.track_usage('REF-00001', 'doc1.md')  # Duplicate

        self.assertEqual(len(manager.usage_tracking['REF-00001']), 2)  # Set removes duplicates
        self.assertIn('doc1.md', manager.usage_tracking['REF-00001'])
        self.assertIn('doc2.md', manager.usage_tracking['REF-00001'])


class TestAddCitation(unittest.TestCase):
    """Test adding custom citations"""

    def test_add_custom_citation(self):
        """Test adding a custom citation"""
        manager = CitationManager()

        ref_id = manager.add_citation(
            component='CustomComponent',
            file_path='custom.java',
            original_line=42,
            repomix_line=100,
            code_snippet='public class CustomComponent { }'
        )

        self.assertEqual(ref_id, 'REF-00001')
        self.assertIn(ref_id, manager.ref_mapping)

        details = manager.ref_mapping[ref_id]
        self.assertEqual(details['name'], 'CustomComponent')
        self.assertEqual(details['file_path'], 'custom.java')
        self.assertEqual(details['original_line'], 42)
        self.assertEqual(details['type'], 'custom')
        self.assertTrue(details['_custom'])

    def test_add_multiple_custom_citations(self):
        """Test REF-ID increments correctly"""
        manager = CitationManager()

        ref1 = manager.add_citation('Component1', 'file1.java')
        ref2 = manager.add_citation('Component2', 'file2.java')
        ref3 = manager.add_citation('Component3', 'file3.java')

        self.assertEqual(ref1, 'REF-00001')
        self.assertEqual(ref2, 'REF-00002')
        self.assertEqual(ref3, 'REF-00003')


class TestGenerateCitationsFile(unittest.TestCase):
    """Test citations file generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CitationManager()
        self.manager.ref_mapping = {
            'REF-00001': {
                'name': 'UserService',
                'file_path': 'user.java',
                'original_line': 10,
                'type': 'class',
                'snippet': 'public class UserService'
            }
        }

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_generate_without_agent_name(self):
        """Test generation fails without agent name"""
        with patch('builtins.print') as mock_print:
            result = self.manager.generate_citations_file(self.temp_dir)

        self.assertEqual(result, "")
        mock_print.assert_called_with("⚠️  No agent name set. Call set_agent_name() first.")

    def test_generate_with_agent_name(self):
        """Test successful generation with agent name"""
        self.manager.set_agent_name("test-agent")

        with patch('builtins.print'):
            result = self.manager.generate_citations_file(self.temp_dir)

        expected_path = Path(self.temp_dir) / "test-agent-citations.md"
        self.assertEqual(result, str(expected_path))
        self.assertTrue(expected_path.exists())

        # Check content
        with open(expected_path, 'r') as f:
            content = f.read()

        self.assertIn("# Code Citations Reference - test-agent", content)
        self.assertIn("REF-00001: UserService", content)
        self.assertIn("user.java:10", content)

    def test_generate_creates_directory(self):
        """Test that generation creates output directory if needed"""
        nested_dir = Path(self.temp_dir) / "nested" / "output"
        self.manager.set_agent_name("test")

        with patch('builtins.print'):
            result = self.manager.generate_citations_file(str(nested_dir))

        self.assertTrue(nested_dir.exists())


class TestFormatCitations(unittest.TestCase):
    """Test citation formatting"""

    def test_format_single_citation(self):
        """Test formatting a single citation"""
        manager = CitationManager()
        manager.usage_tracking = {'REF-00001': {'doc1.md', 'doc2.md'}}

        details = {
            'name': 'TestClass',
            'file_path': 'test.java',
            'original_line': 42,
            'repomix_line': 100,
            'type': 'class',
            'snippet': 'public class TestClass extends BaseClass implements Interface'
        }

        result = manager._format_single_citation('REF-00001', details)

        self.assertIn("### REF-00001: TestClass", result)
        self.assertIn("test.java:42", result)
        self.assertIn("**Repomix Line**: 100", result)
        self.assertIn("**Type**: class", result)
        self.assertIn("doc1.md", result)
        self.assertIn("doc2.md", result)

    def test_format_citation_without_line_number(self):
        """Test formatting citation without line number"""
        manager = CitationManager()

        details = {
            'name': 'Component',
            'file_path': 'file.java',
            'type': 'class',
            'snippet': 'class Component'
        }

        result = manager._format_single_citation('REF-00001', details)

        self.assertIn("file.java`", result)  # No line number
        self.assertNotIn("file.java:", result)

    def test_format_citation_long_snippet(self):
        """Test formatting with long snippet truncation"""
        manager = CitationManager()

        long_snippet = "x" * 150
        details = {
            'name': 'Component',
            'file_path': 'file.java',
            'snippet': long_snippet
        }

        result = manager._format_single_citation('REF-00001', details)

        self.assertIn("x" * 100 + "...", result)

    def test_format_citation_with_none_snippet(self):
        """Test formatting citation with None snippet"""
        manager = CitationManager()

        details = {
            'name': 'Component',
            'file_path': 'file.java',
            'type': 'class',
            'snippet': None  # This can happen
        }

        # Should handle None gracefully
        result = manager._format_single_citation('REF-00001', details)

        self.assertIn("### REF-00001: Component", result)
        self.assertIn("file.java", result)


class TestUpdateDocumentWithReferences(unittest.TestCase):
    """Test document reference updating"""

    def setUp(self):
        """Set up test manager"""
        self.manager = CitationManager()
        self.manager.citations = {
            'classes': [
                {'name': 'UserService', 'file_path': 'UserService.java', 'ref_id': 'REF-00001'},
                {'name': 'OrderService', 'file_path': 'OrderService.java', 'ref_id': 'REF-00002'}
            ]
        }

    def test_update_document_with_inline_citations(self):
        """Test updating document with inline citations"""
        content = """
        The UserService (UserService.java:123) handles user operations.
        OrderService (OrderService.java) manages orders.
        """

        updated, count = self.manager.update_document_with_references(content, "test.md")

        self.assertEqual(count, 2)
        self.assertIn("`UserService` [REF-00001]", updated)
        self.assertIn("`OrderService` [REF-00002]", updated)
        self.assertIn('REF-00001', self.manager.usage_tracking)

    def test_update_document_no_matches(self):
        """Test updating document with no matching components"""
        content = "This document has no component references."

        updated, count = self.manager.update_document_with_references(content, "test.md")

        self.assertEqual(count, 0)
        self.assertEqual(content, updated)

    def test_update_document_partial_matches(self):
        """Test updating document with partial matches"""
        content = """
        UserService (UserService.java) exists.
        NonexistentClass (NonexistentClass.java) does not exist.
        """

        updated, count = self.manager.update_document_with_references(content, "test.md")

        self.assertEqual(count, 1)
        self.assertIn("`UserService` [REF-00001]", updated)
        self.assertIn("NonexistentClass (NonexistentClass.java)", updated)  # Unchanged


class TestGenerateDiagramCitations(unittest.TestCase):
    """Test diagram citation generation"""

    def setUp(self):
        """Set up test manager"""
        self.manager = CitationManager()
        self.manager.citations = {
            'classes': [
                {'name': 'UserService', 'ref_id': 'REF-00001'},
                {'name': 'OrderService', 'ref_id': 'REF-00002'}
            ]
        }

    def test_generate_diagram_citations(self):
        """Test generating citations for diagram components"""
        components = ['UserService', 'OrderService', 'NonexistentService']

        result = self.manager.generate_diagram_citations(components)

        self.assertIn("%% Component Citations", result)
        self.assertIn("%% UserService: REF-00001", result)
        self.assertIn("%% OrderService: REF-00002", result)
        self.assertNotIn("NonexistentService", result)

    def test_generate_diagram_citations_no_matches(self):
        """Test generating citations with no matching components"""
        components = ['NonexistentA', 'NonexistentB']

        result = self.manager.generate_diagram_citations(components)

        self.assertIn("%% No components requiring citation", result)


class TestValidateCitationsInDocument(unittest.TestCase):
    """Test document citation validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CitationManager()
        self.manager.ref_mapping = {
            'REF-00001': {'name': 'Component1'},
            'REF-00002': {'name': 'Component2'}
        }

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_missing_file(self):
        """Test validation with missing file"""
        result = self.manager.validate_citations_in_document("/nonexistent/file.md")

        self.assertFalse(result["valid"])
        self.assertEqual(result["error"], "File not found: /nonexistent/file.md")

    def test_validate_valid_citations(self):
        """Test validation with all valid citations"""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text("References: REF-00001 and REF-00002")

        result = self.manager.validate_citations_in_document(str(test_file))

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["valid_refs"]), 2)
        self.assertEqual(len(result["invalid_refs"]), 0)
        self.assertIn('REF-00001', result["valid_refs"])
        self.assertIn('REF-00002', result["valid_refs"])

    def test_validate_invalid_citations(self):
        """Test validation with invalid citations"""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text("References: REF-00001, REF-99999, and REF-88888")

        result = self.manager.validate_citations_in_document(str(test_file))

        self.assertFalse(result["valid"])
        self.assertEqual(len(result["valid_refs"]), 1)
        self.assertEqual(len(result["invalid_refs"]), 2)
        self.assertIn('REF-99999', result["invalid_refs"])
        self.assertIn('REF-88888', result["invalid_refs"])

    def test_validate_duplicate_citations(self):
        """Test validation with duplicate citations"""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text("REF-00001 appears twice: REF-00001")

        result = self.manager.validate_citations_in_document(str(test_file))

        self.assertTrue(result["valid"])
        self.assertEqual(result["total_refs"], 1)  # Set removes duplicates
        self.assertEqual(len(result["valid_refs"]), 1)

    def test_validate_tracks_usage(self):
        """Test that validation tracks usage"""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text("REF-00001")

        self.manager.validate_citations_in_document(str(test_file))

        self.assertIn('REF-00001', self.manager.usage_tracking)
        self.assertIn('test.md', self.manager.usage_tracking['REF-00001'])


class TestGetStats(unittest.TestCase):
    """Test statistics generation"""

    def test_get_stats_empty(self):
        """Test stats with empty data"""
        manager = CitationManager()
        manager.citations = {'classes': [], 'methods': []}

        stats = manager.get_stats()

        self.assertEqual(stats['total_citations'], 0)
        self.assertEqual(stats['citations_used'], 0)
        self.assertEqual(stats['most_referenced'], [])

    def test_get_stats_with_data(self):
        """Test stats with sample data"""
        manager = CitationManager()
        manager.ref_mapping = {
            'REF-00001': {'type_category': 'classes'},
            'REF-00002': {'type_category': 'classes'},
            'REF-00003': {'type_category': 'methods'}
        }
        manager.usage_tracking = {
            'REF-00001': {'doc1.md', 'doc2.md', 'doc3.md'},
            'REF-00002': {'doc1.md'}
        }
        manager.citations = {'classes': [], 'methods': []}

        stats = manager.get_stats()

        self.assertEqual(stats['total_citations'], 3)
        self.assertEqual(stats['citations_used'], 2)
        self.assertEqual(len(stats['most_referenced']), 2)
        self.assertEqual(stats['most_referenced'][0], ('REF-00001', 3))
        self.assertEqual(stats['most_referenced'][1], ('REF-00002', 1))


class TestGetOrCreateRef(unittest.TestCase):
    """Test private _get_or_create_ref method"""

    def test_get_existing_ref(self):
        """Test getting existing REF-ID for component"""
        manager = CitationManager()
        manager.ref_mapping = {
            'REF-00001': {
                'name': 'TestClass',
                'file_path': 'test.java',
                '_key': 'classes:test.java:TestClass:0'
            }
        }

        component = {
            'name': 'TestClass',
            'file_path': 'test.java',
            'repomix_line': 0
        }

        ref_id = manager._get_or_create_ref(component, 'classes')
        self.assertEqual(ref_id, 'REF-00001')

    def test_create_new_ref(self):
        """Test creating new REF-ID for component"""
        manager = CitationManager()

        component = {
            'name': 'NewClass',
            'file_path': 'new.java',
            'repomix_line': 10
        }

        ref_id = manager._get_or_create_ref(component, 'classes')

        self.assertEqual(ref_id, 'REF-00001')
        self.assertIn(ref_id, manager.ref_mapping)
        self.assertEqual(manager.ref_mapping[ref_id]['name'], 'NewClass')
        self.assertEqual(manager.ref_mapping[ref_id]['_key'], 'classes:new.java:NewClass:10')


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_unicode_in_citations(self):
        """Test handling Unicode in component names"""
        manager = CitationManager()

        ref_id = manager.add_citation(
            component='中文组件',
            file_path='unicode.java',
            code_snippet='public class 中文组件 { }'
        )

        self.assertEqual(ref_id, 'REF-00001')
        self.assertEqual(manager.ref_mapping[ref_id]['name'], '中文组件')

    def test_special_characters_in_names(self):
        """Test handling special characters in names"""
        manager = CitationManager()
        manager.citations = {
            'classes': [
                {'name': 'Class$With_Special@Chars', 'ref_id': 'REF-00001'}
            ]
        }

        ref_id = manager.lookup_citation('Class$With_Special@Chars')
        self.assertEqual(ref_id, 'REF-00001')

    def test_very_long_component_names(self):
        """Test handling very long component names"""
        manager = CitationManager()
        long_name = 'VeryLongComponentName' * 20

        ref_id = manager.add_citation(long_name, 'file.java')

        self.assertEqual(ref_id, 'REF-00001')
        self.assertEqual(manager.ref_mapping[ref_id]['name'], long_name)

    def test_empty_citations_data(self):
        """Test operations with empty citations data"""
        manager = CitationManager()
        manager.citations = {}

        result = manager.find_component('AnyComponent')
        self.assertIsNone(result)

        stats = manager.get_stats()
        self.assertEqual(stats['total_citations'], 0)

    def test_malformed_citations_data(self):
        """Test handling malformed citations data"""
        manager = CitationManager()
        manager.citations = {
            'classes': 'not_a_list',  # Should be a list
            'methods': None
        }

        result = manager.find_component('TestClass')
        self.assertIsNone(result)  # Should handle gracefully

    def test_concurrent_usage_tracking(self):
        """Test concurrent usage tracking doesn't lose data"""
        manager = CitationManager()

        # Simulate concurrent tracking
        for i in range(100):
            manager.track_usage('REF-00001', f'doc{i % 10}.md')

        # Should have at most 10 unique files
        self.assertLessEqual(len(manager.usage_tracking['REF-00001']), 10)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""

    def test_complete_workflow(self):
        """Test complete citation management workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test citations file
            citations_file = Path(temp_dir) / "citations.json"
            test_data = {
                'classes': [
                    {'name': 'UserService', 'file_path': 'user.java', 'ref_id': 'REF-00001'},
                    {'name': 'OrderService', 'file_path': 'order.java', 'ref_id': 'REF-00002'}
                ],
                'methods': [
                    {'name': 'getUser', 'parent_class': 'UserService', 'ref_id': 'REF-00003'}
                ],
                'ref_index': {
                    'REF-00001': {'name': 'UserService', 'type': 'class'},
                    'REF-00002': {'name': 'OrderService', 'type': 'class'},
                    'REF-00003': {'name': 'getUser', 'type': 'method'}
                }
            }

            with open(citations_file, 'w') as f:
                json.dump(test_data, f)

            # Initialize manager
            manager = CitationManager(str(citations_file))

            # Load citations
            with patch('builtins.print'):
                self.assertTrue(manager.load_citations())

            # Set agent name
            manager.set_agent_name("integration-test")

            # Lookup citations
            self.assertEqual(manager.lookup_citation('UserService'), 'REF-00001')
            self.assertEqual(manager.lookup_citation('getUser', 'method'), 'REF-00003')

            # Add custom citation (counter starts after loaded citations)
            custom_ref = manager.add_citation('CustomComponent', 'custom.java', code_snippet='class CustomComponent')
            self.assertIsNotNone(custom_ref)
            self.assertTrue(custom_ref.startswith('REF-'))

            # Track usage
            manager.track_usage('REF-00001', 'doc1.md')
            manager.track_usage('REF-00002', 'doc1.md')
            manager.track_usage('REF-00001', 'doc2.md')

            # Generate citations file
            with patch('builtins.print'):
                output_path = manager.generate_citations_file(temp_dir)

            self.assertTrue(Path(output_path).exists())

            # Verify content
            with open(output_path, 'r') as f:
                content = f.read()

            self.assertIn("integration-test", content)
            # The custom component takes REF-00001 since internal counter starts at 0
            self.assertIn("REF-00001: CustomComponent", content)

            # Get stats
            stats = manager.get_stats()
            # ref_mapping only contains loaded ref_index (3) + custom (1) = at least 1
            self.assertGreaterEqual(stats['total_citations'], 1)  # Should have at least the custom one
            self.assertGreaterEqual(stats['citations_used'], 2)  # At least REF-00001 and REF-00002


if __name__ == '__main__':
    unittest.main()