#!/usr/bin/env python3
"""Fix indentation in app_multi_bootstrap.py"""

import sys

# Read the file
with open(r'c:\vs\advanced_panel\process\app_multi_bootstrap.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with 'if __name__ ==', and the next line with 'with gr.Blocks'
# Then indent everything after 'with gr.Blocks' until 'demo.launch'

in_gradio_block = False
start_indent_line = -1
end_indent_line = -1

for i, line in enumerate(lines):
    if '__main__' in line and 'GRADIO INTERFACE' in ''.join(lines[max(0,i-5):i]):
        in_gradio_block = True
    elif in_gradio_block and 'with gr.Blocks' in line:
        start_indent_line = i + 1  # Start indenting from next line
    elif in_gradio_block and 'demo.launch' in line:
        end_indent_line = i + 1  # Include this line
        break

print(f'Start indent line: {start_indent_line} (0-indexed: {start_indent_line})')
print(f'End indent line: {end_indent_line} (0-indexed: {end_indent_line})')
print(f'Total lines to indent: {end_indent_line - start_indent_line}')

if start_indent_line > 0:
    print(f'\nFirst line to indent (line {start_indent_line + 1}):')
    print(repr(lines[start_indent_line][:80]))
    print(f'\nLast line to indent (line {end_indent_line}):')
    print(repr(lines[end_indent_line - 1][:80]))
    
    # Now perform the indentation
    new_lines = lines[:start_indent_line]
    for line in lines[start_indent_line:end_indent_line]:
        # Add 4 spaces to each line (unless it's already indented or empty)
        if line.strip():  # Not empty
            new_lines.append('    ' + line)
        else:
            new_lines.append(line)
    
    new_lines.extend(lines[end_indent_line:])
    
    # Write back
    with open(r'c:\vs\advanced_panel\process\app_multi_bootstrap.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print('\n✓ File updated successfully!')
else:
    print('\n✗ Could not find the section to indent')
