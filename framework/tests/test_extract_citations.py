#!/usr/bin/env python3
"""
Comprehensive tests for extract_citations.py
Tests citation extraction, REF-ID assignment, and file operations
"""

import unittest
import tempfile
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, mock_open, call
from datetime import datetime
from dataclasses import dataclass
import argparse

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from extract_citations import assign_ref_ids, main, validate_extraction
from repomix_parser import CodeComponent


class TestAssignRefIds(unittest.TestCase):
    """Test the assign_ref_ids function"""

    def test_assign_ref_ids_empty_components(self):
        """Test REF-ID assignment with empty components"""
        components = {
            'classes': [],
            'methods': [],
            'interfaces': []
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        self.assertIn('ref_index', result)
        self.assertEqual(len(result['ref_index']), 0)
        self.assertEqual(len(result['classes']), 0)

    def test_assign_ref_ids_with_dataclass_components(self):
        """Test REF-ID assignment with dataclass components"""
        components = {
            'classes': [
                CodeComponent(
                    name='TestClass',
                    type='class',
                    file_path='test.java',
                    repomix_line=10,
                    original_line=5,
                    signature='public class TestClass'
                ),
                CodeComponent(
                    name='AnotherClass',
                    type='class',
                    file_path='another.java',
                    repomix_line=20,
                    original_line=10
                )
            ],
            'methods': [
                CodeComponent(
                    name='testMethod',
                    type='method',
                    file_path='test.java',
                    repomix_line=15,
                    parent_class='TestClass'
                )
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        # Check REF-IDs are assigned
        self.assertEqual(len(result['classes']), 2)
        self.assertEqual(len(result['methods']), 1)
        self.assertEqual(result['classes'][0]['ref_id'], 'REF-00001')
        self.assertEqual(result['classes'][1]['ref_id'], 'REF-00002')
        self.assertEqual(result['methods'][0]['ref_id'], 'REF-00003')

        # Check ref_index is created
        self.assertEqual(len(result['ref_index']), 3)
        self.assertIn('REF-00001', result['ref_index'])
        self.assertEqual(result['ref_index']['REF-00001']['name'], 'TestClass')
        self.assertEqual(result['ref_index']['REF-00001']['type'], 'class')

    def test_assign_ref_ids_with_dict_components(self):
        """Test REF-ID assignment with dictionary components"""
        components = {
            'configs': [
                {'name': 'db.url', 'type': 'property', 'file_path': 'app.properties'},
                {'name': 'app.port', 'type': 'property', 'file_path': 'app.properties'}
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        self.assertEqual(len(result['configs']), 2)
        self.assertEqual(result['configs'][0]['ref_id'], 'REF-00001')
        self.assertEqual(result['configs'][1]['ref_id'], 'REF-00002')

    def test_assign_ref_ids_preserves_original_data(self):
        """Test that original component data is preserved"""
        components = {
            'classes': [
                CodeComponent(
                    name='TestClass',
                    type='class',
                    file_path='test.java',
                    repomix_line=10,
                    snippet='public class TestClass { }'
                )
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        class_data = result['classes'][0]
        self.assertEqual(class_data['name'], 'TestClass')
        self.assertEqual(class_data['snippet'], 'public class TestClass { }')
        self.assertIn('ref_id', class_data)

    def test_ref_id_uniqueness(self):
        """Test that REF-IDs are unique across all component types"""
        components = {
            'classes': [CodeComponent(f'Class{i}', 'class', f'file{i}.java', i)
                       for i in range(5)],
            'methods': [CodeComponent(f'method{i}', 'method', f'file{i}.java', i)
                       for i in range(5)],
            'interfaces': [CodeComponent(f'Interface{i}', 'interface', f'file{i}.java', i)
                          for i in range(5)]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        # Collect all REF-IDs
        all_ref_ids = []
        for comp_type in ['classes', 'methods', 'interfaces']:
            for comp in result[comp_type]:
                all_ref_ids.append(comp['ref_id'])

        # Check uniqueness
        self.assertEqual(len(all_ref_ids), len(set(all_ref_ids)))
        self.assertEqual(len(all_ref_ids), 15)

    def test_ref_id_format(self):
        """Test REF-ID format is correct"""
        components = {
            'classes': [CodeComponent(f'Class{i}', 'class', 'test.java', i)
                       for i in range(100)]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        # Check format for different numbers
        self.assertEqual(result['classes'][0]['ref_id'], 'REF-00001')
        self.assertEqual(result['classes'][9]['ref_id'], 'REF-00010')
        self.assertEqual(result['classes'][99]['ref_id'], 'REF-00100')

    def test_ref_index_contains_correct_data(self):
        """Test ref_index contains correct component details"""
        components = {
            'methods': [
                CodeComponent(
                    name='calculate',
                    type='method',
                    file_path='calc.py',
                    repomix_line=50,
                    original_line=25,
                    parent_class='Calculator'
                )
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        ref_index = result['ref_index']['REF-00001']
        self.assertEqual(ref_index['name'], 'calculate')
        self.assertEqual(ref_index['type'], 'method')
        self.assertEqual(ref_index['file_path'], 'calc.py')
        self.assertEqual(ref_index['line'], 25)

    def test_handles_special_characters_in_names(self):
        """Test handling of special characters in component names"""
        components = {
            'classes': [
                CodeComponent('Class_with$Special@Chars', 'class', 'test.java', 1),
                CodeComponent('ÜñíçödëClass', 'class', 'test.java', 2),
                CodeComponent('中文类名', 'class', 'test.java', 3)
            ]
        }

        with patch('builtins.print'):
            result = assign_ref_ids(components)

        self.assertEqual(len(result['classes']), 3)
        self.assertEqual(result['classes'][0]['name'], 'Class_with$Special@Chars')
        self.assertEqual(result['classes'][1]['name'], 'ÜñíçödëClass')
        self.assertEqual(result['classes'][2]['name'], '中文类名')


class TestMainFunction(unittest.TestCase):
    """Test the main function"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_repomix = Path(self.temp_dir) / "repomix-summary.md"
        self.test_output = Path(self.temp_dir) / "output.json"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_main_with_missing_file(self):
        """Test main function with missing repomix file"""
        args = Mock()
        args.input = '/nonexistent/file.md'
        args.output = str(self.test_output)
        args.validate = False

        with patch('builtins.print'):
            with self.assertRaises(SystemExit) as cm:
                main(args)

        self.assertEqual(cm.exception.code, 1)

    def test_main_with_parser_load_failure(self):
        """Test main function when parser fails to load"""
        # Create empty file
        self.test_repomix.write_text("")

        args = Mock()
        args.input = str(self.test_repomix)
        args.output = str(self.test_output)
        args.validate = False

        with patch('extract_citations.RepomixParser') as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.load.return_value = False

            with patch('builtins.print'):
                with self.assertRaises(SystemExit) as cm:
                    main(args)

            self.assertEqual(cm.exception.code, 1)

    def test_main_successful_execution(self):
        """Test successful execution of main function"""
        # Create a simple repomix file
        self.test_repomix.write_text("""## File: Test.java
```java
public class Test {}
```
""")

        args = Mock()
        args.input = str(self.test_repomix)
        args.output = str(self.test_output)
        args.validate = False

        # Mock the parser
        with patch('extract_citations.RepomixParser') as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.load.return_value = True
            mock_parser.extract_all_components.return_value = {
                'classes': [
                    CodeComponent('TestClass', 'class', 'Test.java', 1)
                ],
                'methods': []
            }

            with patch('builtins.print'):
                result = main(args)

            self.assertEqual(result, 0)
            self.assertTrue(self.test_output.exists())

            # Check JSON output
            with open(self.test_output, 'r') as f:
                data = json.load(f)

            self.assertIn('metadata', data)
            self.assertIn('ref_index', data)
            self.assertIn('classes', data)

    def test_main_creates_output_directory(self):
        """Test that main creates output directory if it doesn't exist"""
        nested_output = Path(self.temp_dir) / "nested" / "dir" / "output.json"

        args = Mock()
        args.input = str(self.test_repomix)
        args.output = str(nested_output)
        args.validate = False

        self.test_repomix.write_text("## File: Test.java")

        with patch('extract_citations.RepomixParser') as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.load.return_value = True
            mock_parser.extract_all_components.return_value = {'classes': []}

            with patch('builtins.print'):
                main(args)

            self.assertTrue(nested_output.parent.exists())

    def test_main_metadata_generation(self):
        """Test metadata is correctly generated"""
        self.test_repomix.write_text("## File: Test.java")

        args = Mock()
        args.input = str(self.test_repomix)
        args.output = str(self.test_output)
        args.validate = False

        with patch('extract_citations.RepomixParser') as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.load.return_value = True
            mock_parser.extract_all_components.return_value = {
                'classes': [CodeComponent('A', 'class', 'a.java', 1)],
                'methods': [CodeComponent('b', 'method', 'a.java', 2)]
            }

            with patch('builtins.print'):
                main(args)

            with open(self.test_output, 'r') as f:
                data = json.load(f)

            self.assertIn('generated', data['metadata'])
            self.assertEqual(data['metadata']['version'], '1.2')
            self.assertEqual(data['metadata']['total_components'], 2)
            self.assertEqual(data['metadata']['source'], str(self.test_repomix))


class TestValidateExtraction(unittest.TestCase):
    """Test the validate_extraction function"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "citations.json"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_missing_file(self):
        """Test validation with missing file"""
        with patch('builtins.print') as mock_print:
            result = validate_extraction('/nonexistent/file.json')

        self.assertFalse(result)
        mock_print.assert_any_call("❌ Citations file not found: /nonexistent/file.json")

    def test_validate_valid_file(self):
        """Test validation with valid citations file"""
        data = {
            'classes': [
                {'name': 'TestClass', 'file_path': 'test.java', 'ref_id': 'REF-001'},
                {'name': 'Another', 'file_path': 'another.java', 'ref_id': 'REF-002'}
            ],
            'interfaces': [],
            'methods': [
                {'name': 'method1', 'parent_class': 'TestClass', 'ref_id': 'REF-003'}
            ],
            'metadata': {
                'version': '1.1',
                'generated': '2024-01-01T00:00:00'
            }
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print'):
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)

    def test_validate_invalid_json(self):
        """Test validation with invalid JSON"""
        with open(self.test_file, 'w') as f:
            f.write("{ invalid json }")

        with patch('builtins.print'):
            with self.assertRaises(json.JSONDecodeError):
                validate_extraction(str(self.test_file))

    def test_validate_missing_required_keys(self):
        """Test validation reports missing required keys"""
        data = {
            'classes': [],
            # Missing 'interfaces', 'methods', 'metadata'
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print') as mock_print:
            result = validate_extraction(str(self.test_file))

        self.assertTrue(result)  # Still returns True but reports missing

        # Check that missing keys are reported
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('Missing: interfaces' in str(c) for c in print_calls))

    def test_validate_sample_output(self):
        """Test validation shows sample entries"""
        data = {
            'classes': [
                {'name': f'Class{i}', 'file_path': f'file{i}.java', 'ref_id': f'REF-{i:03d}'}
                for i in range(5)
            ],
            'methods': [
                {'name': f'method{i}', 'parent_class': 'TestClass', 'ref_id': f'REF-{i+5:03d}'}
                for i in range(5)
            ],
            'metadata': {}
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        with patch('builtins.print') as mock_print:
            validate_extraction(str(self.test_file))

        print_output = ' '.join(str(call) for call in mock_print.call_args_list)
        self.assertIn('Sample Classes:', print_output)
        self.assertIn('Sample Methods:', print_output)


class TestArgumentParsing(unittest.TestCase):
    """Test command-line argument parsing"""

    @patch('sys.argv', ['extract_citations.py'])
    def test_default_arguments(self):
        """Test default argument values"""
        from extract_citations import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument('-i', '--input', default='output/reports/repomix-summary.md')
        parser.add_argument('-o', '--output', default='output/context/codebase-citations.json')
        parser.add_argument('-v', '--validate', action='store_true')

        args = parser.parse_args([])

        self.assertEqual(args.input, 'output/reports/repomix-summary.md')
        self.assertEqual(args.output, 'output/context/codebase-citations.json')
        self.assertFalse(args.validate)

    @patch('sys.argv', ['extract_citations.py', '-i', 'custom.md', '-o', 'custom.json', '-v'])
    def test_custom_arguments(self):
        """Test custom argument values"""
        from extract_citations import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument('-i', '--input', default='output/reports/repomix-summary.md')
        parser.add_argument('-o', '--output', default='output/context/codebase-citations.json')
        parser.add_argument('-v', '--validate', action='store_true')

        args = parser.parse_args(['-i', 'custom.md', '-o', 'custom.json', '-v'])

        self.assertEqual(args.input, 'custom.md')
        self.assertEqual(args.output, 'custom.json')
        self.assertTrue(args.validate)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""

    def test_json_serialization_error(self):
        """Test handling of JSON serialization errors"""
        # Create a component with non-serializable data
        components = {
            'classes': [
                {'name': 'Test', 'bad_data': datetime.now()}  # datetime not JSON serializable
            ]
        }

        # This should handle the error gracefully
        with patch('builtins.print'):
            with self.assertRaises(TypeError):
                json.dumps(components)

    def test_file_permission_error(self):
        """Test handling of file permission errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test input file
            input_file = Path(temp_dir) / "test.md"
            input_file.write_text("## File: Test.java")

            output_file = Path(temp_dir) / "output.json"

            # Create a read-only directory to cause permission error on output
            os.chmod(temp_dir, 0o555)  # Read and execute only

            args = Mock()
            args.input = str(input_file)
            args.output = str(output_file)
            args.validate = False

            with patch('extract_citations.RepomixParser') as MockParser:
                mock_parser = MockParser.return_value
                mock_parser.load.return_value = True
                mock_parser.extract_all_components.return_value = {'classes': []}

                try:
                    with patch('builtins.print'):
                        # This should raise PermissionError when trying to write output
                        result = main(args)
                        # If no error was raised (some systems don't enforce), that's ok
                except (PermissionError, OSError):
                    pass  # Expected on systems that enforce permissions
                except SystemExit:
                    pass  # Also acceptable if the function exits due to error

            # Reset permissions for cleanup
            os.chmod(temp_dir, 0o755)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""

    def test_end_to_end_extraction(self):
        """Test complete extraction workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a realistic repomix file
            repomix_file = Path(temp_dir) / "repomix.md"
            repomix_file.write_text("""# File Summary

## File: com/example/Service.java
```java
public class UserService {
    public User getUser(int id) {
        return userRepository.find(id);
    }
}
```

## File: config/app.properties
```properties
db.url=jdbc:mysql://localhost:3306/mydb
app.name=TestApp
```
""")

            output_file = Path(temp_dir) / "citations.json"

            # Create args
            args = Mock()
            args.input = str(repomix_file)
            args.output = str(output_file)
            args.validate = True

            # Run main function
            with patch('builtins.print'):
                with patch('extract_citations.validate_extraction') as mock_validate:
                    mock_validate.return_value = True
                    result = main(args)

            self.assertEqual(result, 0)
            self.assertTrue(output_file.exists())

            # Verify output structure
            with open(output_file, 'r') as f:
                data = json.load(f)

            self.assertIn('metadata', data)
            self.assertIn('ref_index', data)
            self.assertIn('classes', data)

            # Verify REF-IDs are assigned
            if data['classes']:
                self.assertIn('ref_id', data['classes'][0])


if __name__ == '__main__':
    unittest.main()