#!/usr/bin/env python3
"""Simple YAML validation script for tool contribution examples."""

import sys
from pathlib import Path
from typing import Dict, List, Any

import yaml


def validate_subagent(data: Dict[str, Any]) -> tuple[bool, List[str], List[str]]:
    """Validate SubAgent data.

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Required fields
    required_fields = ["name", "version", "description", "category"]
    for field in required_fields:
        if field not in data:
            errors.append(f"SubAgent: Missing required field '{field}'")

    # Check installations
    if "installations" not in data or not data["installations"]:
        warnings.append("SubAgent: No installation methods provided")
    else:
        for i, inst in enumerate(data["installations"]):
            if "method" not in inst:
                errors.append(f"Installation {i}: Missing 'method' field")
            if "platform_id" not in inst:
                errors.append(f"Installation {i}: Missing 'platform_id' field")
            if "requires_install" not in inst:
                errors.append(f"Installation {i}: Missing 'requires_install' field")

    # Check activations
    if "activations" not in data or not data["activations"]:
        warnings.append("SubAgent: No activation methods provided")
    else:
        for i, act in enumerate(data["activations"]):
            if "type" not in act:
                errors.append(f"Activation {i}: Missing 'type' field")
            if "platform_id" not in act:
                errors.append(f"Activation {i}: Missing 'platform_id' field")

    return len(errors) == 0, errors, warnings


def validate_tool(data: Dict[str, Any], index: int) -> tuple[bool, List[str], List[str]]:
    """Validate Tool data.

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    prefix = f"Tool {index}"

    # Required fields
    required_fields = ["name", "display_name", "description", "category", "parameters"]
    for field in required_fields:
        if field not in data:
            errors.append(f"{prefix}: Missing required field '{field}'")

    # Check prompts
    if "prompts" not in data or not data["prompts"]:
        warnings.append(f"{prefix}: No prompts provided")
    else:
        for i, prompt in enumerate(data["prompts"]):
            if "name" not in prompt:
                errors.append(f"{prefix} Prompt {i}: Missing 'name' field")
            if "template_type" not in prompt:
                errors.append(f"{prefix} Prompt {i}: Missing 'template_type' field")

    # Check subagent_name
    if "subagent_name" not in data:
        errors.append(f"{prefix}: Missing 'subagent_name' field")

    # Check parameters schema
    if "parameters" in data:
        params = data["parameters"]
        if "type" not in params:
            errors.append(f"{prefix}: Parameters missing 'type' field")
        if "properties" not in params:
            errors.append(f"{prefix}: Parameters missing 'properties' field")

    # Check structured_output if present
    if "structured_output" in data:
        output = data["structured_output"]
        if "name" not in output:
            errors.append(f"{prefix}: Structured output missing 'name' field")
        if "json_schema" not in output:
            errors.append(f"{prefix}: Structured output missing 'json_schema' field")

    # Check activations
    if "activations" not in data or not data["activations"]:
        warnings.append(f"{prefix}: No activations provided")

    return len(errors) == 0, errors, warnings


def validate_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Validate a YAML file.

    Returns:
        Validation result dictionary
    """
    result = {
        "file": file_path.name,
        "valid": False,
        "errors": [],
        "warnings": [],
    }

    try:
        # Read and parse YAML
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        # Check top-level structure
        if "subagent" not in data:
            result["errors"].append("Missing 'subagent' section")
        if "tools" not in data or not data["tools"]:
            result["errors"].append("Missing or empty 'tools' section")

        if result["errors"]:
            return result

        # Validate SubAgent
        valid, errors, warnings = validate_subagent(data["subagent"])
        result["errors"].extend(errors)
        result["warnings"].extend(warnings)

        # Validate Tools
        for i, tool_data in enumerate(data.get("tools", [])):
            valid, errors, warnings = validate_tool(tool_data, i)
            result["errors"].extend(errors)
            result["warnings"].extend(warnings)

        # Set overall validity
        result["valid"] = len(result["errors"]) == 0

    except yaml.YAMLError as e:
        result["errors"].append(f"YAML syntax error: {str(e)}")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")

    return result


def print_result(result: Dict[str, Any]):
    """Print validation result."""
    print(f"\n{'='*60}")
    print(f"File: {result['file']}")
    print('='*60)

    if result['valid']:
        print("✓ VALID")
    else:
        print("✗ INVALID")

    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  • {error}")

    if result['warnings']:
        print(f"\nWarnings ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"  • {warning}")


def main():
    """Main validation function."""
    examples_dir = Path("examples_v2")

    if not examples_dir.exists():
        print(f"Error: Directory '{examples_dir}' not found")
        sys.exit(1)

    yaml_files = sorted(examples_dir.glob("*.yaml"))

    if not yaml_files:
        print(f"No YAML files found in '{examples_dir}'")
        sys.exit(1)

    print("="*60)
    print("YAML VALIDATION TEST")
    print("="*60)
    print(f"\nFound {len(yaml_files)} YAML files")

    results = []
    for yaml_file in yaml_files:
        result = validate_yaml_file(yaml_file)
        results.append(result)
        print_result(result)

    # Summary
    valid_count = sum(1 for r in results if r['valid'])
    total_errors = sum(len(r['errors']) for r in results)
    total_warnings = sum(len(r['warnings']) for r in results)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total files: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {len(results) - valid_count}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")

    if valid_count == len(results):
        print("\n✓ All files are valid!")
        sys.exit(0)
    else:
        print(f"\n✗ {len(results) - valid_count} file(s) have errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
