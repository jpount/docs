#!/usr/bin/env python3
"""
Comprehensive tests for citation validation functionality
Tests edge cases, data integrity, and validation features
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from dataclasses import dataclass, asdict
import os

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from extract_citations import validate_extraction, assign_ref_ids
from repomix_parser import CodeComponent


class TestValidationIntegration(unittest.TestCase):
    """Integration tests for validation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_citations.json"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_comprehensive_data(self):
        """Test validation with comprehensive component types"""
        data = {
            'classes': [
                {'name': 'UserService', 'file_path': 'service.java', 'ref_id': 'REF-00001'},
                {'name': 'OrderService', 'file_path': 'service.java', 'ref_id': 'REF-00002'}
            ],
            'interfaces': [
                {'name': 'Repository', 'file_path': 'repo.java', 'ref_id': 'REF-00003'}
            ],
            'methods': [
                {'name': 'getUser', 'parent_class': 'UserService', 'ref_id': 'REF-00004'},
                {'name': 'saveOrder', 'parent_class': 'OrderService', 'ref_id': 'REF-00005'}
            ],
            'enums': [
                {'name': 'Status', 'file_path': 'types.java', 'ref_id': 'REF-00006'}
            ],
            'configs': [
                {'name': 'db.url', 'type': 'property', 'ref_id': 'REF-00007'}
            ],
            'api_endpoints': [
                {'name': 'GetMapping', 'type': 'annotation', 'ref_id': 'REF-00008'}
            ],
            'ref_index': {
                'REF-00001': {'name': 'UserService', 'type': 'class'},
                'REF-00002': {'name': 'OrderService', 'type': 'class'},
                'REF-00003': {'name': 'Repository', 'type': 'interface'},
                'REF-00004': {'name': 'getUser', 'type': 'method'},
                'REF-00005': {'name': 'saveOrder', 'type': 'method'},
                'REF-00006': {'name': 'Status', 'type': 'enum'},
                'REF-00007': {'name': 'db.url', 'type': 'property'},
                'REF-00008': {'name': 'GetMapping', 'type': 'annotation'}
            },
            'metadata': {
                'version': '1.1',
                'total_components': 8,
                'generated': '2024-01-01T00:00:00'
            }
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print') as mock_print:
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

        # Check all component types are validated
        print_output = ' '.join(str(call) for call in mock_print.call_args_list)
        self.assertIn('classes: 2 items', print_output)
        self.assertIn('interfaces: 1 items', print_output)
        self.assertIn('methods: 2 items', print_output)

    def test_validate_empty_collections(self):
        """Test validation with empty component collections"""
        data = {
            'classes': [],
            'interfaces': [],
            'methods': [],
            'enums': [],
            'configs': [],
            'ref_index': {},
            'metadata': {
                'version': '1.1',
                'total_components': 0
            }
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print') as mock_print:
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

        print_output = ' '.join(str(call) for call in mock_print.call_args_list)
        self.assertIn('classes: 0 items', print_output)

    def test_validate_malformed_entries(self):
        """Test validation with malformed component entries"""
        data = {
            'classes': [
                {'name': 'CompleteClass', 'file_path': 'test.java', 'ref_id': 'REF-00001'},
                {'name': 'MissingPath', 'ref_id': 'REF-00002'},  # Missing file_path
                {}  # Empty entry
            ],
            'methods': [
                {'name': 'method1'},  # Missing ref_id
                {'ref_id': 'REF-00003'}  # Missing name
            ],
            'metadata': {}
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        # Should still validate but might report issues
        with patch('builtins.print'):
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

    def test_validate_unicode_and_special_chars(self):
        """Test validation with Unicode and special characters"""
        data = {
            'classes': [
                {'name': 'ÜñíçödëClass', 'file_path': 'unicode.java', 'ref_id': 'REF-00001'},
                {'name': '中文类名', 'file_path': 'chinese.java', 'ref_id': 'REF-00002'},
                {'name': 'Class$With_Special@Chars', 'file_path': 'special.java', 'ref_id': 'REF-00003'}
            ],
            'methods': [
                {'name': 'método', 'parent_class': 'ÜñíçödëClass', 'ref_id': 'REF-00004'},
                {'name': '计算', 'parent_class': '中文类名', 'ref_id': 'REF-00005'}
            ],
            'metadata': {'version': '1.1'}
        }

        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

        with patch('builtins.print'):
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

    def test_validate_very_long_names(self):
        """Test validation with very long component names"""
        long_name = 'VeryLongClassName' * 20  # 340 characters

        data = {
            'classes': [
                {'name': long_name, 'file_path': 'long.java', 'ref_id': 'REF-00001'}
            ],
            'methods': [
                {'name': 'method_with_' + 'very_' * 50 + 'long_name', 'ref_id': 'REF-00002'}
            ],
            'metadata': {}
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print'):
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

    def test_validate_missing_ref_index(self):
        """Test validation when ref_index is missing"""
        data = {
            'classes': [
                {'name': 'TestClass', 'ref_id': 'REF-00001'}
            ],
            # Missing ref_index
            'metadata': {'version': '1.1'}
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print'):
            # Should still validate even without ref_index
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)


class TestValidationEdgeCases(unittest.TestCase):
    """Test edge cases in validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "edge_case.json"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_corrupted_json(self):
        """Test validation with corrupted JSON"""
        # Write corrupted JSON
        with open(self.test_file, 'w') as f:
            f.write('{"classes": [{"name": "Test"')  # Incomplete JSON

        with patch('builtins.print'):
            with self.assertRaises(json.JSONDecodeError):
                validate_extraction(str(self.test_file))

    def test_validate_empty_file(self):
        """Test validation with empty file"""
        self.test_file.touch()  # Create empty file

        with patch('builtins.print'):
            with self.assertRaises(json.JSONDecodeError):
                validate_extraction(str(self.test_file))

    def test_validate_very_large_file(self):
        """Test validation with very large citation file"""
        # Create a large dataset
        data = {
            'classes': [
                {'name': f'Class{i}', 'file_path': f'file{i}.java', 'ref_id': f'REF-{i:05d}'}
                for i in range(1000)
            ],
            'methods': [
                {'name': f'method{i}', 'parent_class': f'Class{i%100}', 'ref_id': f'REF-{i+1000:05d}'}
                for i in range(5000)
            ],
            'ref_index': {
                f'REF-{i:05d}': {'name': f'Component{i}', 'type': 'class'}
                for i in range(6000)
            },
            'metadata': {
                'total_components': 6000
            }
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print'):
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

    def test_validate_null_values(self):
        """Test validation with null values in data"""
        data = {
            'classes': [
                {'name': 'TestClass', 'file_path': None, 'ref_id': 'REF-00001'},
                {'name': None, 'file_path': 'test.java', 'ref_id': 'REF-00002'}
            ],
            'methods': [
                {'name': 'method1', 'parent_class': None, 'ref_id': 'REF-00003'}
            ],
            'metadata': {
                'version': None,
                'total_components': None
            }
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print'):
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

    def test_validate_non_json_file(self):
        """Test validation with non-JSON file"""
        with open(self.test_file, 'w') as f:
            f.write("This is not JSON content\nJust plain text")

        with patch('builtins.print'):
            with self.assertRaises(json.JSONDecodeError):
                validate_extraction(str(self.test_file))

    def test_validate_json_with_comments(self):
        """Test validation with JSON containing comments (invalid)"""
        with open(self.test_file, 'w') as f:
            f.write("""{
                // This is a comment
                "classes": [],
                /* Another comment */
                "methods": []
            }""")

        with patch('builtins.print'):
            with self.assertRaises(json.JSONDecodeError):
                validate_extraction(str(self.test_file))


class TestRefIdValidation(unittest.TestCase):
    """Test REF-ID specific validation"""

    def test_ref_id_uniqueness_validation(self):
        """Test that duplicate REF-IDs are handled"""
        components = {
            'classes': [
                CodeComponent('Class1', 'class', 'file1.java', 1),
                CodeComponent('Class2', 'class', 'file2.java', 2)
            ],
            'methods': [
                CodeComponent('method1', 'method', 'file1.java', 3)
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        # Check all REF-IDs are unique
        all_refs = []
        for comp_list in result.values():
            if isinstance(comp_list, list):
                for comp in comp_list:
                    if 'ref_id' in comp:
                        all_refs.append(comp['ref_id'])

        self.assertEqual(len(all_refs), len(set(all_refs)))

    def test_ref_index_consistency(self):
        """Test that ref_index is consistent with component REF-IDs"""
        components = {
            'classes': [
                CodeComponent('TestClass', 'class', 'test.java', 1)
            ],
            'methods': [
                CodeComponent('testMethod', 'method', 'test.java', 2)
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        ref_index = result['ref_index']

        # Check that all component REF-IDs are in ref_index
        for comp_type in ['classes', 'methods']:
            for comp in result[comp_type]:
                ref_id = comp['ref_id']
                self.assertIn(ref_id, ref_index)
                self.assertEqual(ref_index[ref_id]['name'], comp['name'])


class TestFileIOEdgeCases(unittest.TestCase):
    """Test file I/O edge cases"""

    def test_read_only_file(self):
        """Test validation with read-only file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'classes': [], 'metadata': {}}, f)
            temp_file = f.name

        # Make file read-only
        os.chmod(temp_file, 0o444)

        try:
            with patch('builtins.print'):
                result = validate_extraction(temp_file)
            self.assertTrue(result)
        finally:
            # Clean up
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_symlink_file(self):
        """Test validation with symbolic link to citations file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create actual file
            actual_file = Path(temp_dir) / "actual.json"
            with open(actual_file, 'w') as f:
                json.dump({'classes': [], 'metadata': {}}, f)

            # Create symlink
            symlink = Path(temp_dir) / "symlink.json"
            symlink.symlink_to(actual_file)

            with patch('builtins.print'):
                result = validate_extraction(str(symlink))

            self.assertTrue(result)

    def test_binary_file_validation(self):
        """Test validation fails gracefully with binary file"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            # Write binary data
            f.write(b'\x00\x01\x02\x03\x04\x05')
            temp_file = f.name

        try:
            with patch('builtins.print'):
                with self.assertRaises((json.JSONDecodeError, UnicodeDecodeError)):
                    validate_extraction(temp_file)
        finally:
            os.unlink(temp_file)


class TestLargeDatasetHandling(unittest.TestCase):
    """Test handling of large datasets"""

    def test_assign_ref_ids_performance(self):
        """Test REF-ID assignment with large number of components"""
        # Create a large dataset
        num_components = 10000
        components = {
            'classes': [
                CodeComponent(f'Class{i}', 'class', f'file{i}.java', i)
                for i in range(num_components)
            ]
        }

        import time
        start_time = time.time()

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        self.assertLess(elapsed_time, 5.0)

        # Verify all components got REF-IDs
        self.assertEqual(len(result['classes']), num_components)
        self.assertEqual(len(result['ref_index']), num_components)

        # Verify REF-ID format for large numbers
        last_ref = result['classes'][-1]['ref_id']
        self.assertEqual(last_ref, f'REF-{num_components:03d}')


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity during processing"""

    def test_component_data_preservation(self):
        """Test that all component data is preserved during REF-ID assignment"""
        original_component = CodeComponent(
            name='ComplexClass',
            type='class',
            file_path='/path/to/file.java',
            repomix_line=100,
            original_line=50,
            signature='public class ComplexClass extends Base implements Interface',
            parent_class='OuterClass',
            snippet='public class ComplexClass extends Base implements Interface { }'
        )

        components = {'classes': [original_component]}

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        processed = result['classes'][0]

        # All original fields should be preserved
        self.assertEqual(processed['name'], original_component.name)
        self.assertEqual(processed['type'], original_component.type)
        self.assertEqual(processed['file_path'], original_component.file_path)
        self.assertEqual(processed['repomix_line'], original_component.repomix_line)
        self.assertEqual(processed['original_line'], original_component.original_line)
        self.assertEqual(processed['signature'], original_component.signature)
        self.assertEqual(processed['parent_class'], original_component.parent_class)
        self.assertEqual(processed['snippet'], original_component.snippet)

        # Plus the new REF-ID
        self.assertIn('ref_id', processed)

    def test_mixed_component_types(self):
        """Test handling of mixed dataclass and dict components"""
        components = {
            'classes': [
                CodeComponent('DataclassComponent', 'class', 'file1.java', 1)
            ],
            'configs': [
                {'name': 'DictComponent', 'type': 'property', 'file_path': 'config.properties'}
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        # Both types should be processed correctly
        self.assertEqual(result['classes'][0]['ref_id'], 'REF-00001')
        self.assertEqual(result['configs'][0]['ref_id'], 'REF-00002')

        # Check ref_index
        self.assertEqual(len(result['ref_index']), 2)


if __name__ == '__main__':
    unittest.main()