#!/usr/bin/env python3
"""
Comprehensive test suite for simple_mermaid_validator.py
Tests Mermaid diagram extraction, validation, and fixing functionality.
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.simple_mermaid_validator import (
    extract_mermaid_diagrams,
    validate_with_mermaid_cli,
    apply_basic_fixes,
    validate_file,
    fix_file,
    main
)


class TestExtractMermaidDiagrams(unittest.TestCase):
    """Test Mermaid diagram extraction from files"""

    def test_extract_from_mmd_file(self):
        """Test extraction from standalone .mmd file"""
        content = """graph TD
    A[Start] --> B[Process]
    B --> C[End]"""

        diagrams = extract_mermaid_diagrams(content, "test.mmd")

        self.assertEqual(len(diagrams), 1)
        self.assertEqual(diagrams[0]['content'], content)
        self.assertEqual(diagrams[0]['line_start'], 1)
        self.assertEqual(diagrams[0]['type'], 'standalone')

    def test_extract_from_markdown_with_mermaid_block(self):
        """Test extraction from markdown with ```mermaid blocks"""
        content = """# Documentation

Some text here.

```mermaid
graph LR
    A --> B
```

More text.

```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```

Final text."""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 2)
        self.assertEqual(diagrams[0]['content'].strip(), "graph LR\n    A --> B")
        self.assertEqual(diagrams[0]['line_start'], 5)
        self.assertEqual(diagrams[0]['type'], 'embedded')

        self.assertEqual(diagrams[1]['content'].strip(), "sequenceDiagram\n    Alice->>Bob: Hello")
        self.assertEqual(diagrams[1]['line_start'], 12)  # Corrected line number
        self.assertEqual(diagrams[1]['type'], 'embedded')

    def test_extract_from_markdown_with_mmd_block(self):
        """Test extraction from markdown with ```mmd blocks"""
        content = """# Test

```mmd
classDiagram
    Class01 <|-- Class02
```
"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 1)
        self.assertEqual(diagrams[0]['content'].strip(), "classDiagram\n    Class01 <|-- Class02")
        self.assertEqual(diagrams[0]['type'], 'embedded')

    def test_extract_no_diagrams(self):
        """Test extraction when no diagrams present"""
        content = """# Documentation

Just regular text without any diagrams.

```python
# This is Python code, not Mermaid
print("Hello")
```
"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 0)

    def test_extract_empty_diagram(self):
        """Test extraction of empty diagram block"""
        content = """```mermaid

```"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 1)
        self.assertEqual(diagrams[0]['content'], "")

    def test_extract_nested_backticks(self):
        """Test extraction doesn't get confused by nested backticks"""
        content = """```mermaid
graph TD
    A["`Code`"] --> B
```"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 1)
        self.assertIn('"`Code`"', diagrams[0]['content'])

    def test_extract_multiple_diagrams_correct_line_numbers(self):
        """Test that line numbers are correctly calculated for multiple diagrams"""
        content = """Line 1
Line 2

```mermaid
graph TD
```

Line 8
Line 9

```mermaid
sequenceDiagram
```

Line 14"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 2)
        self.assertEqual(diagrams[0]['line_start'], 4)
        self.assertEqual(diagrams[1]['line_start'], 11)


class TestValidateWithMermaidCLI(unittest.TestCase):
    """Test Mermaid CLI validation"""

    @patch('subprocess.run')
    def test_validate_valid_diagram(self, mock_run):
        """Test validation of a valid diagram"""
        # Mock which command success
        which_result = Mock()
        which_result.returncode = 0

        # Mock mmdc command success
        mmdc_result = Mock()
        mmdc_result.returncode = 0
        mmdc_result.stderr = ""
        mmdc_result.stdout = ""

        mock_run.side_effect = [which_result, mmdc_result]

        with patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'), \
             patch('os.path.exists', return_value=True):

            is_valid, message = validate_with_mermaid_cli("graph TD\n    A --> B")

            self.assertTrue(is_valid)
            self.assertEqual(message, "Valid")

    @patch('subprocess.run')
    def test_validate_invalid_diagram(self, mock_run):
        """Test validation of an invalid diagram"""
        # Mock which command success
        which_result = Mock()
        which_result.returncode = 0

        # Mock mmdc command failure
        mmdc_result = Mock()
        mmdc_result.returncode = 1
        mmdc_result.stderr = "Syntax error in graph"
        mmdc_result.stdout = ""

        mock_run.side_effect = [which_result, mmdc_result]

        with patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'), \
             patch('os.path.exists', return_value=True):

            is_valid, message = validate_with_mermaid_cli("invalid diagram")

            self.assertFalse(is_valid)
            self.assertIn("Syntax error", message)

    @patch('subprocess.run')
    def test_validate_with_npx_fallback(self, mock_run):
        """Test validation falls back to npx when mmdc not installed"""
        # Mock which command failure (mmdc not found)
        which_result = Mock()
        which_result.returncode = 1

        # Mock npx command success
        npx_result = Mock()
        npx_result.returncode = 0
        npx_result.stderr = ""
        npx_result.stdout = ""

        mock_run.side_effect = [which_result, npx_result]

        with patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'), \
             patch('os.path.exists', return_value=True):

            is_valid, message = validate_with_mermaid_cli("graph TD\n    A --> B")

            self.assertTrue(is_valid)
            # Check that npx was used
            call_args = mock_run.call_args_list[1][0][0]
            self.assertIn('npx', call_args)

    @patch('subprocess.run')
    def test_validate_timeout(self, mock_run):
        """Test validation handles timeout"""
        # Mock which command success
        which_result = Mock()
        which_result.returncode = 0

        # Mock timeout
        mock_run.side_effect = [which_result, subprocess.TimeoutExpired('mmdc', 10)]

        with patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'), \
             patch('os.path.exists', return_value=True):

            is_valid, message = validate_with_mermaid_cli("complex diagram")

            self.assertFalse(is_valid)
            self.assertIn("Timeout", message)

    @patch('subprocess.run')
    def test_validate_exception_handling(self, mock_run):
        """Test validation handles unexpected exceptions"""
        mock_run.side_effect = Exception("Unexpected error")

        is_valid, message = validate_with_mermaid_cli("graph TD")

        self.assertFalse(is_valid)
        self.assertIn("Validation error", message)
        self.assertIn("Unexpected error", message)


class TestApplyBasicFixes(unittest.TestCase):
    """Test basic diagram fixes"""

    def test_remove_trailing_whitespace(self):
        """Test removal of trailing whitespace"""
        content = "graph TD  \n    A --> B   \n    C --> D"
        expected = "graph TD\n    A --> B\n    C --> D\n"

        result = apply_basic_fixes(content)

        self.assertEqual(result, expected)

    def test_ensure_newline_at_end(self):
        """Test ensuring file ends with newline"""
        content = "graph TD"

        result = apply_basic_fixes(content)

        self.assertTrue(result.endswith('\n'))

    def test_fix_comment_indentation(self):
        """Test fixing comment indentation"""
        content = """graph TD
    %% This comment is indented
        %% This one too
A --> B"""

        result = apply_basic_fixes(content)

        self.assertIn("%% This comment is indented", result)
        self.assertNotIn("    %%", result)  # Indentation should be removed

    def test_fix_multiple_spaces_in_notes(self):
        """Test fixing multiple spaces after colons in Notes"""
        content = "Note over Alice:    Too many spaces"
        expected = "Note over Alice: Too many spaces\n"

        result = apply_basic_fixes(content)

        self.assertEqual(result, expected)

    def test_remove_at_symbols_from_stereotypes(self):
        """Test removal of @ symbols from stereotypes"""
        content = """classDiagram
    class User {
        <<@interface>>
    }"""

        result = apply_basic_fixes(content)

        self.assertIn("<<interface>>", result)
        self.assertNotIn("<<@interface>>", result)

    def test_fix_excessive_blank_lines(self):
        """Test reducing excessive blank lines"""
        content = "graph TD\n\n\n\n\nA --> B\n\n\n\nC --> D"

        result = apply_basic_fixes(content)

        # Should have max 2 consecutive newlines (one blank line)
        self.assertNotIn("\n\n\n", result)
        self.assertIn("\n\n", result)

    def test_combined_fixes(self):
        """Test multiple fixes applied together"""
        content = """graph TD


    %% Comment with indent
    A --> B
    Note over C:     Multiple spaces
    <<@entity>>  """

        result = apply_basic_fixes(content)

        # Check all fixes applied
        self.assertNotIn("   \n", result)  # No trailing spaces
        self.assertNotIn("    %%", result)  # Comment not indented
        self.assertNotIn(":     ", result)  # No multiple spaces after colon
        self.assertNotIn("<<@entity>>", result)  # @ removed
        self.assertNotIn("\n\n\n", result)  # No excessive blank lines
        self.assertTrue(result.endswith('\n'))  # Ends with newline


class TestValidateFile(unittest.TestCase):
    """Test file validation functionality"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_validate_valid_mmd_file(self, mock_validate):
        """Test validation of valid .mmd file"""
        mock_validate.return_value = (True, "Valid")

        # Create test file
        test_file = Path(self.test_dir) / "test.mmd"
        test_file.write_text("graph TD\n    A --> B")

        result = validate_file(str(test_file))

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['diagrams']), 1)
        self.assertEqual(len(result['errors']), 0)
        self.assertTrue(result['diagrams'][0]['valid'])

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_validate_invalid_diagram(self, mock_validate):
        """Test validation of file with invalid diagram"""
        mock_validate.return_value = (False, "Syntax error")

        # Create test file
        test_file = Path(self.test_dir) / "test.md"
        test_file.write_text("```mermaid\ninvalid diagram\n```")

        result = validate_file(str(test_file))

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['diagrams']), 1)
        self.assertEqual(len(result['errors']), 1)
        self.assertIn("Syntax error", result['errors'][0])

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file"""
        result = validate_file("/nonexistent/file.md")

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['errors']), 1)
        self.assertIn("Could not read file", result['errors'][0])

    def test_validate_file_no_diagrams(self):
        """Test validation of file with no diagrams"""
        test_file = Path(self.test_dir) / "no_diagrams.md"
        test_file.write_text("# Just text\n\nNo diagrams here.")

        result = validate_file(str(test_file))

        self.assertTrue(result['valid'])  # Not invalid, just no diagrams
        self.assertEqual(len(result['diagrams']), 0)
        self.assertEqual(len(result['errors']), 1)
        self.assertIn("No Mermaid diagrams found", result['errors'][0])

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_validate_multiple_diagrams(self, mock_validate):
        """Test validation of file with multiple diagrams"""
        # First diagram valid, second invalid
        mock_validate.side_effect = [
            (True, "Valid"),
            (False, "Error in second diagram")
        ]

        test_file = Path(self.test_dir) / "multiple.md"
        test_file.write_text("""```mermaid
graph TD
```

```mermaid
invalid
```""")

        result = validate_file(str(test_file))

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['diagrams']), 2)
        self.assertTrue(result['diagrams'][0]['valid'])
        self.assertFalse(result['diagrams'][1]['valid'])
        self.assertEqual(len(result['errors']), 1)


class TestFixFile(unittest.TestCase):
    """Test file fixing functionality"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_fix_file_with_issues(self):
        """Test fixing a file with issues"""
        test_file = Path(self.test_dir) / "needs_fix.mmd"
        original = "graph TD  \n    A --> B   "
        test_file.write_text(original)

        result = fix_file(str(test_file))

        self.assertTrue(result)
        fixed_content = test_file.read_text()
        self.assertNotIn("  \n", fixed_content)
        self.assertTrue(fixed_content.endswith('\n'))

    def test_fix_file_no_changes_needed(self):
        """Test fixing a file that doesn't need changes"""
        test_file = Path(self.test_dir) / "good.mmd"
        original = "graph TD\n    A --> B\n"
        test_file.write_text(original)

        result = fix_file(str(test_file))

        self.assertFalse(result)  # No changes made
        self.assertEqual(test_file.read_text(), original)

    def test_fix_nonexistent_file(self):
        """Test fixing non-existent file"""
        with patch('builtins.print') as mock_print:
            result = fix_file("/nonexistent/file.mmd")

            self.assertFalse(result)
            mock_print.assert_called()

    def test_fix_file_permission_error(self):
        """Test fixing file with permission error"""
        test_file = Path(self.test_dir) / "readonly.mmd"
        test_file.write_text("graph TD")
        os.chmod(test_file, 0o444)  # Read-only

        with patch('builtins.print') as mock_print:
            result = fix_file(str(test_file))

            self.assertFalse(result)
            mock_print.assert_called()

        # Restore permissions for cleanup
        os.chmod(test_file, 0o644)


class TestMainFunction(unittest.TestCase):
    """Test main function and CLI interface"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('sys.argv', ['simple_mermaid_validator.py', '--help'])
    def test_help_argument(self):
        """Test --help argument"""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                main()
        self.assertEqual(cm.exception.code, 0)

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    @patch('sys.argv', ['simple_mermaid_validator.py'])
    def test_main_single_file(self, mock_validate):
        """Test validating a single file"""
        mock_validate.return_value = (True, "Valid")

        test_file = Path(self.test_dir) / "test.mmd"
        test_file.write_text("graph TD")

        with patch('sys.argv', ['simple_mermaid_validator.py', str(test_file)]):
            result = main()

        self.assertEqual(result, 0)

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_main_directory(self, mock_validate):
        """Test validating all files in directory"""
        mock_validate.return_value = (True, "Valid")

        # Create test files
        (Path(self.test_dir) / "test1.mmd").write_text("graph TD")
        (Path(self.test_dir) / "test2.md").write_text("```mermaid\ngraph LR\n```")
        (Path(self.test_dir) / "ignore.txt").write_text("not validated")

        with patch('sys.argv', ['simple_mermaid_validator.py', self.test_dir]):
            result = main()

        self.assertEqual(result, 0)
        # Should validate 2 files (.mmd and .md, not .txt)
        self.assertEqual(mock_validate.call_count, 2)

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_main_with_fix_flag(self, mock_validate):
        """Test main with --fix flag"""
        mock_validate.return_value = (True, "Valid")

        test_file = Path(self.test_dir) / "fix_me.mmd"
        test_file.write_text("graph TD  \n    A --> B   ")

        with patch('sys.argv', ['simple_mermaid_validator.py', str(test_file), '--fix']):
            with patch('builtins.print') as mock_print:
                result = main()

        self.assertEqual(result, 0)
        # Check file was fixed
        fixed_content = test_file.read_text()
        self.assertNotIn("  \n", fixed_content)

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_main_json_output(self, mock_validate):
        """Test main with --json flag"""
        mock_validate.return_value = (True, "Valid")

        test_file = Path(self.test_dir) / "test.mmd"
        test_file.write_text("graph TD")

        with patch('sys.argv', ['simple_mermaid_validator.py', str(test_file), '--json']):
            with patch('builtins.print') as mock_print:
                result = main()

        self.assertEqual(result, 0)
        # Check JSON was printed
        printed = mock_print.call_args[0][0]
        data = json.loads(printed)
        self.assertIn('summary', data)
        self.assertIn('files', data)
        self.assertEqual(data['summary']['valid'], 1)

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_main_invalid_file_returns_error(self, mock_validate):
        """Test main returns error code for invalid files"""
        mock_validate.return_value = (False, "Invalid")

        test_file = Path(self.test_dir) / "invalid.mmd"
        test_file.write_text("invalid")

        with patch('sys.argv', ['simple_mermaid_validator.py', str(test_file)]):
            result = main()

        self.assertEqual(result, 1)

    def test_main_nonexistent_path(self):
        """Test main with non-existent path"""
        with patch('sys.argv', ['simple_mermaid_validator.py', '/nonexistent/path']):
            with patch('builtins.print') as mock_print:
                result = main()

        self.assertEqual(result, 1)
        mock_print.assert_called()

    def test_main_no_files_found(self):
        """Test main when no .md/.mmd files found"""
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir()

        with patch('sys.argv', ['simple_mermaid_validator.py', str(empty_dir)]):
            with patch('builtins.print') as mock_print:
                result = main()

        self.assertEqual(result, 0)
        printed_messages = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("No .md or .mmd files found" in msg for msg in printed_messages))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_extract_diagram_with_special_characters(self):
        """Test extraction with special characters"""
        content = """```mermaid
graph TD
    A["Special < > & ' \" chars"]
    B[Unicode: 日本語 🚀]
```"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        self.assertEqual(len(diagrams), 1)
        self.assertIn('Special < > &', diagrams[0]['content'])
        self.assertIn('日本語 🚀', diagrams[0]['content'])

    def test_apply_fixes_empty_string(self):
        """Test applying fixes to empty string"""
        result = apply_basic_fixes("")

        self.assertEqual(result, "\n")

    def test_apply_fixes_only_whitespace(self):
        """Test applying fixes to whitespace-only content"""
        result = apply_basic_fixes("   \n  \n   ")

        # After removing trailing spaces and ensuring final newline
        self.assertEqual(result, "\n\n")

    @patch('scripts.simple_mermaid_validator.validate_with_mermaid_cli')
    def test_validate_extremely_large_diagram(self, mock_validate):
        """Test validation of extremely large diagram"""
        mock_validate.return_value = (True, "Valid")

        # Create a large diagram
        large_content = "graph TD\n"
        for i in range(1000):
            large_content += f"    A{i} --> B{i}\n"

        test_dir = tempfile.mkdtemp()
        try:
            test_file = Path(test_dir) / "large.mmd"
            test_file.write_text(large_content)

            result = validate_file(str(test_file))

            self.assertTrue(result['valid'])
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_extract_malformed_code_blocks(self):
        """Test extraction with malformed code blocks"""
        content = """```mermaid
graph TD
    A --> B
`` # Missing backtick

```mermaid
Never closed"""

        diagrams = extract_mermaid_diagrams(content, "test.md")

        # Should only find properly closed blocks
        # Due to regex, this might find 0 or 1 depending on implementation
        self.assertLessEqual(len(diagrams), 1)

    @patch('subprocess.run')
    def test_validate_cli_with_empty_stderr_stdout(self, mock_run):
        """Test CLI validation with empty output"""
        which_result = Mock()
        which_result.returncode = 0

        mmdc_result = Mock()
        mmdc_result.returncode = 1
        mmdc_result.stderr = ""
        mmdc_result.stdout = ""

        mock_run.side_effect = [which_result, mmdc_result]

        with patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'), \
             patch('os.path.exists', return_value=True):

            is_valid, message = validate_with_mermaid_cli("graph TD")

            self.assertFalse(is_valid)
            self.assertIn("Unknown error", message)

    def test_fix_file_unicode_content(self):
        """Test fixing file with unicode content"""
        test_dir = tempfile.mkdtemp()
        try:
            test_file = Path(test_dir) / "unicode.mmd"
            original = "graph TD  \n    A[日本語] --> B[🚀]   "
            test_file.write_text(original, encoding='utf-8')

            result = fix_file(str(test_file))

            self.assertTrue(result)
            fixed = test_file.read_text(encoding='utf-8')
            self.assertIn("日本語", fixed)
            self.assertIn("🚀", fixed)
            self.assertTrue(fixed.endswith('\n'))
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)