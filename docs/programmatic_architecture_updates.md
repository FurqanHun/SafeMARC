# Programmatic Documentation Synchronization Guide

When maintaining large architecture documents (like UML class diagrams, workflows, and use cases), relying on manual edits or standard command-line tools like `sed` often leads to corrupted Markdown formatting or broken Mermaid diagrams.

This guide outlines the programmatic approach used to synchronize SafeMARC's `docs/architecture/` files with the active codebase. Agents should reference this methodology to perform safe, automated bulk updates.

## 1. Establishing a Source of Truth (AST Parsing)

Before modifying the documentation, always extract the *actual* state of the codebase by parsing the Abstract Syntax Tree (AST). This avoids relying on outdated human knowledge or partial searches.

```python
import ast
import os

class_data = {}
ui_prefixes = ('btn_', 'lbl_', 'txt_', 'chk_', 'cmb_', 'tab_', 'shortcut_', 'slider_', 'radio_', 'grid_', 'scroll_', 'list_', 'search_')

for root, _, files in os.walk('src'):
    for file in files:
        if not file.endswith('.py'): continue
        filepath = os.path.join(root, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_name = node.name
                if cls_name not in class_data:
                    class_data[cls_name] = {'methods': set(), 'props': set()}
                
                for body_node in node.body:
                    # Capture class-level type hints
                    if isinstance(body_node, ast.AnnAssign) and isinstance(body_node.target, ast.Name):
                        if not body_node.target.id.startswith(ui_prefixes):
                            class_data[cls_name]['props'].add(body_node.target.id)
                            
                    # Capture class-level assigns (e.g. Qt Signals)
                    elif isinstance(body_node, ast.Assign):
                        for target in body_node.targets:
                            if isinstance(target, ast.Name):
                                if not target.id.startswith(ui_prefixes):
                                    class_data[cls_name]['props'].add(target.id)
                                    
                    # Capture methods and __init__ variables
                    elif isinstance(body_node, ast.FunctionDef):
                        class_data[cls_name]['methods'].add(body_node.name)
                        if body_node.name == "__init__":
                            for init_node in ast.walk(body_node):
                                if isinstance(init_node, ast.Assign):
                                    for target in init_node.targets:
                                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                            if not target.attr.startswith(ui_prefixes):
                                                class_data[cls_name]['props'].add(target.attr)
```

> **Note**: To maintain a clean architecture diagram, we explicitly filter out GUI noise (e.g., PySide6 widgets prefixed with `btn_`, `lbl_`) from the property lists.

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

## 4. Mathematical Validation (AST vs UML Set Difference)

To guarantee that the UML diagram is strictly 1:1 with the codebase and eliminate human error, use an automated set difference script.

**Workflow for Automated Verification:**
1. **Extract AST Classes**: Use an AST script (similar to the one in Step 1) to recursively traverse `src/` and output a JSON dictionary mapping every class to its exact bytecode methods, properties, and signals.
2. **Extract UML Classes**: Write a script to parse `uml_classes.md` using Regex to extract the methods, attributes, and signals defined in the Mermaid class diagrams.
3. **Filter Exclusions**: Apply a filter to the AST properties to exclude explicitly ignored UI prefixes (e.g., `btn_`, `lbl_`) as per the diagram's rules.
4. **Calculate Set Differences**: Use Python sets to compute `ast_methods - uml_methods` and `uml_methods - ast_methods` (and similarly for properties/signals). 
5. **Iterate**: The script will print exact discrepancies. Update the Markdown using targeted replacement (as in Step 2) until the script outputs **zero discrepancies**.

```python
# Example logic for strict mathematical comparison:
ast_attributes = set(ast_class_info['attributes'])
ast_attributes = {attr for attr in ast_attributes if not attr.startswith(ignored_prefixes)}

missing_in_uml = ast_attributes - uml_info['attributes']
extra_in_uml = uml_info['attributes'] - ast_attributes

if missing_in_uml:
    print(f"Missing in UML: {missing_in_uml}")
if extra_in_uml:
    print(f"Extra in UML (stale): {extra_in_uml}")
```

## Summary for AI Agents
When tasked with synchronizing `docs/architecture/` files in the future:
1. **Do not use `sed`** for complex multi-line edits.
2. **Do not assume codebase state**; run an AST script to build a dictionary of the actual classes, functions, and properties.
3. **Filter GUI Noise**: When extracting properties via `ast.Assign` or `ast.AnnAssign`, strip out common Qt GUI prefixes (`btn_`, `lbl_`, etc.) so the architecture diagrams reflect pure system state.
4. **Use Python Regex (`re.DOTALL | re.MULTILINE`)** to target specific blocks for injection.
5. **Always perform a reverse-check** to delete deprecated methods and variables that are no longer in the codebase.
6. **Perform Strict Set Difference Validation**: Write and run a verification script to mathematically prove that AST properties matches UML properties 1:1, ensuring zero human error.
