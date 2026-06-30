# Programmatic Documentation Synchronization Guide

When maintaining large architecture documents (like UML class diagrams, workflows, and use cases), relying on manual edits or standard command-line tools like `sed` often leads to corrupted Markdown formatting or broken Mermaid diagrams.

This guide outlines the programmatic approach used to synchronize SafeMARC's `docs/architecture/` files with the active codebase. Agents should reference this methodology to perform safe, automated bulk updates.

## 1. Establishing a Source of Truth (AST Parsing)

Before modifying the documentation, always extract the *actual* state of the codebase by parsing the Abstract Syntax Tree (AST). This avoids relying on outdated human knowledge or partial searches.

**Example: Extracting Classes and Methods**
```python
import ast
import os

class_methods = {}

for root, _, files in os.walk('src'):
    for file in files:
        if not file.endswith('.py'): continue
        filepath = os.path.join(root, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                class_methods[node.name] = set(methods)
```

## 2. Safely Injecting Missing Elements (Regex)

Mermaid diagrams require strict indentation and bracket placement. To inject missing methods into a specific class block without breaking the surrounding Markdown, use a targeted multi-line Python Regex.

**Example: Injecting Methods into `PreviewWidget`**
```python
import re

uml_file = 'docs/architecture/uml_classes.md'
with open(uml_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Define methods to inject (extracted from the AST step)
methods_to_add = ['on_hit_toggled', 'resizeEvent', 'wheelEvent']
class_name = 'PreviewWidget'

# Regex Breakdown:
# Group 1 captures 'class ClassName {' and its existing contents non-greedily
# Group 2 captures the closing brace '}' on its own line
pattern = re.compile(r'(class ' + class_name + r' \{.*?)(^\s+\})', re.MULTILINE | re.DOTALL)

def replacement_logic(match):
    existing_block = match.group(1)
    closing_brace = match.group(2)
    
    new_methods = []
    for mth in methods_to_add:
        # Prevent duplicates
        if f"{mth}(" not in existing_block and f"{mth} " not in existing_block:
            new_methods.append(f"        +{mth}() void")
            
    if new_methods:
        # Reconstruct block with perfect indentation
        return existing_block + "\n".join(new_methods) + "\n" + closing_brace
        
    return match.group(0)

# Apply and save
content = pattern.sub(replacement_logic, content)
```

## 3. Auditing and Removing Stale Elements

Codebases evolve; methods are renamed or deleted. Simply injecting new methods leaves behind "stale" methods in the UML diagram. You must perform a reverse-check.

**Example: Finding Stale Methods in UML**
```python
import re

# 1. Parse the UML diagram to find all currently listed methods
pattern = re.compile(r'class (\w+) \{(.*?)\}', re.MULTILINE | re.DOTALL)
for match in pattern.finditer(content):
    cls_name = match.group(1)
    if cls_name not in class_methods:
        continue # Class might be an abstract or external concept
    
    block = match.group(2)
    # Find all standard Mermaid method declarations (e.g. +methodName( )
    for mth_match in re.finditer(r'^[ \t]*[+-]([a-zA-Z0-9_]+)\(', block, re.MULTILINE):
        mth_name = mth_match.group(1)
        
        # 2. Cross-reference against the AST
        if mth_name not in class_methods[cls_name]:
            print(f"Stale Method Found: {cls_name}.{mth_name}")
            # Action: Remove these from the markdown file programmatically or manually.
```

## Summary for AI Agents
When tasked with synchronizing `docs/architecture/` files in the future:
1. **Do not use `sed`** for complex multi-line edits.
2. **Do not assume codebase state**; run an AST script to build a dictionary of the actual classes and functions.
3. **Use Python Regex (`re.DOTALL | re.MULTILINE`)** to target specific blocks for injection.
4. **Always perform a reverse-check** to delete deprecated methods and variables that are no longer in the codebase.
