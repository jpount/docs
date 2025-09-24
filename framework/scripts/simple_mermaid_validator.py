#!/usr/bin/env python3
"""
Simple Mermaid Validator - Mimics document-viewer.html approach
Uses Mermaid CLI to validate syntax just like the browser does
"""

import os
import re
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

def extract_mermaid_diagrams(content: str, file_path: str) -> List[Dict]:
    """Extract all Mermaid diagrams from markdown or .mmd files"""
    diagrams = []
    
    # For .mmd files, the entire content is a diagram
    if file_path.endswith('.mmd'):
        diagrams.append({
            'content': content,
            'line_start': 1,
            'type': 'standalone'
        })
        return diagrams
    
    # For .md files, extract from code blocks
    # Pattern for ```mermaid or ```mmd blocks
    pattern = r'```(?:mermaid|mmd)\s*\n(.*?)\n```'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        diagram_content = match.group(1)
        line_start = content[:match.start()].count('\n') + 1
        diagrams.append({
            'content': diagram_content,
            'line_start': line_start,
            'type': 'embedded'
        })
    
    return diagrams

def validate_with_mermaid_cli(diagram_content: str) -> Tuple[bool, str]:
    """
    Validate diagram using Mermaid CLI (mmdc)
    This mimics what document-viewer.html does with mermaid.render()
    """
    try:
        # Check if mmdc is installed
        result = subprocess.run(['which', 'mmdc'], capture_output=True, text=True)
        if result.returncode != 0:
            # Try to use npx if mmdc not globally installed
            mmdc_cmd = ['npx', '@mermaid-js/mermaid-cli']
        else:
            mmdc_cmd = ['mmdc']
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp_input:
            tmp_input.write(diagram_content)
            tmp_input_path = tmp_input.name
        
        tmp_output_path = tmp_input_path.replace('.mmd', '.svg')
        
        try:
            # Run mermaid CLI to validate
            cmd = mmdc_cmd + ['-i', tmp_input_path, '-o', tmp_output_path, '-t', 'default']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # Clean up temp files
            os.unlink(tmp_input_path)
            if os.path.exists(tmp_output_path):
                os.unlink(tmp_output_path)
            
            if result.returncode == 0:
                return True, "Valid"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            os.unlink(tmp_input_path)
            if os.path.exists(tmp_output_path):
                os.unlink(tmp_output_path)
            return False, "Timeout: Diagram took too long to render"
            
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def apply_basic_fixes(content: str) -> str:
    """
    Apply the same basic fixes that work in document-viewer.html
    These are minimal, safe transformations that don't change semantics
    """
    # Remove trailing whitespace
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    # Ensure file ends with newline
    if not content.endswith('\n'):
        content += '\n'
    
    # Fix common issues that document-viewer.html handles
    # 1. Fix indentation for comments (they should start at column 1)
    content = re.sub(r'^[ \t]+(%%.*)$', r'\1', content, flags=re.MULTILINE)
    
    # 2. Fix multiple spaces after colons in Notes
    content = re.sub(r'(Note\s+(?:over|right of|left of)\s+[^:]+:)\s{2,}', r'\1 ', content)
    
    # 3. Remove @ symbols from stereotypes (class diagrams)
    content = re.sub(r'<<@(\w+)>>', r'<<\1>>', content)
    
    # 4. Fix excessive blank lines (max 2)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

def validate_file(file_path: str) -> Dict:
    """Validate a single file containing Mermaid diagrams"""
    results = {
        'file': file_path,
        'valid': True,
        'diagrams': [],
        'errors': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        results['valid'] = False
        results['errors'].append(f"Could not read file: {str(e)}")
        return results
    
    # Extract diagrams
    diagrams = extract_mermaid_diagrams(content, file_path)
    
    if not diagrams:
        results['errors'].append("No Mermaid diagrams found")
        return results
    
    # Validate each diagram
    for i, diagram in enumerate(diagrams):
        diagram_content = diagram['content']
        
        # Validate with Mermaid CLI
        is_valid, message = validate_with_mermaid_cli(diagram_content)
        
        diagram_result = {
            'index': i + 1,
            'line_start': diagram['line_start'],
            'type': diagram['type'],
            'valid': is_valid,
            'message': message
        }
        
        if not is_valid:
            results['valid'] = False
            results['errors'].append(f"Diagram {i+1} at line {diagram['line_start']}: {message}")
        
        results['diagrams'].append(diagram_result)
    
    return results

def fix_file(file_path: str) -> bool:
    """Apply basic fixes to a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes
        fixed_content = apply_basic_fixes(content)
        
        # Only write if content changed
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {str(e)}")
        return False

def main():
    """Main function to validate and optionally fix Mermaid diagrams"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Mermaid validator that mimics browser validation')
    parser.add_argument('path', nargs='?', default='output', help='Path to file or directory to validate')
    parser.add_argument('--fix', action='store_true', help='Apply basic fixes to files')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    files_to_validate = []
    
    if path.is_file():
        if path.suffix in ['.md', '.mmd']:
            files_to_validate.append(path)
    elif path.is_dir():
        # Find all .md and .mmd files
        files_to_validate.extend(path.glob('**/*.md'))
        files_to_validate.extend(path.glob('**/*.mmd'))
    else:
        print(f"Error: {path} is not a valid file or directory")
        return 1
    
    if not files_to_validate:
        print("No .md or .mmd files found")
        return 0
    
    # Apply fixes if requested
    if args.fix:
        fixed_count = 0
        for file_path in files_to_validate:
            if fix_file(str(file_path)):
                fixed_count += 1
                print(f"Fixed: {file_path}")
        print(f"\nFixed {fixed_count} files")
    
    # Validate all files
    all_results = []
    total_valid = 0
    total_invalid = 0
    
    for file_path in files_to_validate:
        result = validate_file(str(file_path))
        all_results.append(result)
        
        if result['valid']:
            total_valid += 1
            if not args.json:
                print(f"✅ {file_path}: Valid")
        else:
            total_invalid += 1
            if not args.json:
                print(f"❌ {file_path}: Invalid")
                for error in result['errors']:
                    print(f"   - {error}")
    
    # Output results
    if args.json:
        print(json.dumps({
            'summary': {
                'total_files': len(files_to_validate),
                'valid': total_valid,
                'invalid': total_invalid
            },
            'files': all_results
        }, indent=2))
    else:
        print(f"\nSummary: {total_valid} valid, {total_invalid} invalid out of {len(files_to_validate)} files")
    
    return 0 if total_invalid == 0 else 1

if __name__ == '__main__':
    exit(main())