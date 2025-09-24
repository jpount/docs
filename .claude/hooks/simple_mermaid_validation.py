#!/usr/bin/env python3
"""
Simple Pre-Write Mermaid Validation Hook
Validates Mermaid diagrams before writing to prevent syntax errors
"""

import sys
import re
import json
from pathlib import Path

def extract_mermaid_from_content(content: str, file_path: str) -> list:
    """Extract Mermaid diagrams from content"""
    diagrams = []
    
    # For .mmd files, entire content is a diagram
    if file_path.endswith('.mmd'):
        diagrams.append(content)
    else:
        # For .md files, extract from code blocks
        pattern = r'```(?:mermaid|mmd)\s*\n(.*?)\n```'
        diagrams.extend(re.findall(pattern, content, re.DOTALL))
    
    return diagrams

def apply_safe_fixes(content: str) -> str:
    """
    Apply only the safest fixes that document-viewer.html handles well
    These are the same transformations the browser applies
    """
    # 1. Remove trailing whitespace from lines
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    # 2. Ensure file ends with newline
    if content and not content.endswith('\n'):
        content += '\n'
    
    # 3. Fix comment indentation (comments must start at column 1)
    content = re.sub(r'^[ \t]+(%%.*)$', r'\1', content, flags=re.MULTILINE)
    
    # 4. Fix multiple spaces after colons in Notes
    content = re.sub(r'(Note\s+(?:over|right of|left of)\s+[^:]+:)\s{2,}', r'\1 ', content)
    
    # 5. Remove @ symbols from stereotypes
    content = re.sub(r'<<@(\w+)>>', r'<<\1>>', content)
    
    # 6. Reduce excessive blank lines (max 2 consecutive)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

def validate_basic_syntax(diagram: str) -> tuple:
    """
    Basic syntax validation that catches obvious errors
    Returns (is_valid, error_message)
    """
    # Check if diagram is empty
    if not diagram.strip():
        return False, "Empty diagram"
    
    # Check for valid diagram type at the start
    valid_starts = [
        'graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 
        'stateDiagram', 'stateDiagram-v2', 'erDiagram', 'journey', 
        'gantt', 'pie', 'gitGraph', 'mindmap', 'timeline', 'quadrantChart',
        'sankey', 'block-beta', 'C4Context', 'C4Container', 'C4Component', 'C4Dynamic'
    ]
    
    first_line = diagram.strip().split('\n')[0].strip()
    # Remove comments from first line
    if '%%' in first_line:
        first_line = first_line.split('%%')[0].strip()
    
    if first_line and not any(first_line.startswith(start) for start in valid_starts):
        # Allow if first line is a comment
        if not first_line.startswith('%%'):
            return False, f"Invalid diagram type: {first_line[:50]}"
    
    # Check for balanced brackets/braces
    open_brackets = diagram.count('[')
    close_brackets = diagram.count(']')
    if open_brackets != close_brackets:
        return False, f"Unbalanced square brackets: {open_brackets} [ vs {close_brackets} ]"
    
    open_braces = diagram.count('{')
    close_braces = diagram.count('}')
    if open_braces != close_braces:
        return False, f"Unbalanced curly braces: {open_braces} {{ vs {close_braces} }}"
    
    open_parens = diagram.count('(')
    close_parens = diagram.count(')')
    if open_parens != close_parens:
        return False, f"Unbalanced parentheses: {open_parens} ( vs {close_parens} )"
    
    return True, "Valid"

def main():
    """Main validation function called by Claude Code hook"""
    # Read input from stdin (Claude Code provides file path and content)
    try:
        input_data = json.loads(sys.stdin.read())
        file_path = input_data.get('file_path', '')
        content = input_data.get('content', '')
    except:
        # Fallback for testing
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            with open(file_path, 'r') as f:
                content = f.read()
        else:
            print("Error: No input provided")
            sys.exit(1)
    
    # Check if this is a file we should validate
    if not (file_path.endswith('.md') or file_path.endswith('.mmd')):
        # Not a Mermaid file, allow it
        print(json.dumps({'valid': True}))
        sys.exit(0)
    
    # Apply safe fixes
    fixed_content = apply_safe_fixes(content)
    
    # Extract and validate diagrams
    diagrams = extract_mermaid_from_content(fixed_content, file_path)
    
    if not diagrams and file_path.endswith('.mmd'):
        print(json.dumps({
            'valid': False,
            'error': 'Empty Mermaid diagram file',
            'fixed_content': fixed_content
        }))
        sys.exit(1)
    
    errors = []
    for i, diagram in enumerate(diagrams):
        is_valid, error = validate_basic_syntax(diagram)
        if not is_valid:
            errors.append(f"Diagram {i+1}: {error}")
    
    if errors:
        print(json.dumps({
            'valid': False,
            'errors': errors,
            'fixed_content': fixed_content
        }))
        sys.exit(1)
    else:
        print(json.dumps({
            'valid': True,
            'fixed_content': fixed_content if fixed_content != content else None
        }))
        sys.exit(0)

if __name__ == '__main__':
    main()