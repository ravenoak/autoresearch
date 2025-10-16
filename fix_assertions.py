#!/usr/bin/env python3
import re

files = [
    'tests/behavior/steps/lmstudio_integration_steps.py',
    'tests/behavior/steps/openrouter_integration_steps.py',
    'tests/behavior/steps/logging_steps.py'
]

for file_path in files:
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace remaining assert_that patterns
    content = re.sub(r'assert_that\(([^,]+),\s*equal_to\(([^)]+)\)\)', r'assert \1 == \2', content)
    content = re.sub(r'assert_that\(([^,]+),\s*is_not\(equal_to\(([^)]+)\)\)\)', r'assert \1 != \2', content)
    content = re.sub(r'assert_that\(hasattr\(([^,]+),\s*[\'"]([^\'"]+)[\'"]\)\)', r'assert hasattr(\1, "\2")', content)
    content = re.sub(r'assert_that\(([^,]+),\s*[\'"]([^\'"]+)[\'"]\s+in\s+([^)]+)\)', r'assert "\2" in \3', content)

    with open(file_path, 'w') as f:
        f.write(content)

print('Fixed remaining hamcrest assertions')
