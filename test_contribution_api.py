#!/usr/bin/env python3
"""Test script for contribution API endpoints."""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

import httpx


BASE_URL = "http://localhost:8000"
EXAMPLES_DIR = Path("examples_v2")


async def test_yaml_validation(file_path: Path) -> Dict[str, Any]:
    """Test YAML validation endpoint.

    Args:
        file_path: Path to YAML file

    Returns:
        Validation result
    """
    print(f"\n{'='*60}")
    print(f"Testing validation: {file_path.name}")
    print('='*60)

    async with httpx.AsyncClient() as client:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/x-yaml')}
            response = await client.post(
                f"{BASE_URL}/contribute/yaml/validate",
                files=files,
                timeout=30.0
            )

    result = response.json()

    print(f"Status: {response.status_code}")
    print(f"Valid: {result.get('valid')}")

    if not result.get('valid'):
        print("\nErrors:")
        for error in result.get('errors', []):
            print(f"  - {error}")

    if result.get('warnings'):
        print("\nWarnings:")
        for warning in result.get('warnings', []):
            print(f"  - {warning}")

    return result


async def test_yaml_import(file_path: Path, auto_index: bool = True) -> Dict[str, Any]:
    """Test YAML import endpoint.

    Args:
        file_path: Path to YAML file
        auto_index: Whether to auto-index tools

    Returns:
        Import result
    """
    print(f"\n{'='*60}")
    print(f"Testing import: {file_path.name}")
    print('='*60)

    async with httpx.AsyncClient() as client:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/x-yaml')}
            response = await client.post(
                f"{BASE_URL}/contribute/yaml/import?auto_index={str(auto_index).lower()}",
                files=files,
                timeout=30.0
            )

    result = response.json()

    print(f"Status: {response.status_code}")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")

    if result.get('success'):
        print(f"SubAgent: {result.get('subagent_name')}")
        print(f"Tool: {result.get('tool_name')}")
    else:
        if result.get('errors'):
            print("\nErrors:")
            for error in result.get('errors', []):
                print(f"  - {error}")

    return result


async def test_search_tools(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Test tool search endpoint.

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        Search results
    """
    print(f"\n{'='*60}")
    print(f"Testing search: '{query}'")
    print('='*60)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/search/tools",
            json={"query": query, "top_k": top_k},
            timeout=30.0
        )

    result = response.json()

    print(f"Status: {response.status_code}")
    print(f"Total results: {result.get('total')}")
    print(f"Query time: {result.get('query_time_ms'):.2f}ms")

    print("\nResults:")
    for i, tool in enumerate(result.get('results', []), 1):
        print(f"\n{i}. {tool.get('display_name')} ({tool.get('name')})")
        print(f"   Score: {tool.get('score', 'N/A')}")
        print(f"   Category: {tool.get('category')}")
        print(f"   SubAgent: {tool.get('subagent_name')}")
        print(f"   Description: {tool.get('description')[:100]}...")

    return result


async def test_facets() -> Dict[str, Any]:
    """Test facets endpoint.

    Returns:
        Facets data
    """
    print(f"\n{'='*60}")
    print("Testing facets endpoint")
    print('='*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/search/facets",
            timeout=30.0
        )

    result = response.json()

    print(f"Status: {response.status_code}")

    print("\nCategories:")
    for facet in result.get('categories', [])[:10]:
        print(f"  {facet['value']}: {facet['count']}")

    print("\nTags:")
    for facet in result.get('tags', [])[:10]:
        print(f"  {facet['value']}: {facet['count']}")

    print("\nProtocols:")
    for facet in result.get('protocols', []):
        print(f"  {facet['value']}: {facet['count']}")

    print("\nSubAgents:")
    for facet in result.get('subagents', [])[:10]:
        print(f"  {facet['value']}: {facet['count']}")

    return result


async def test_statistics() -> Dict[str, Any]:
    """Test statistics endpoint.

    Returns:
        Statistics data
    """
    print(f"\n{'='*60}")
    print("Testing statistics endpoint")
    print('='*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/search/statistics",
            timeout=30.0
        )

    result = response.json()

    print(f"Status: {response.status_code}")
    print(f"\nTotal Tools: {result.get('total_tools')}")
    print(f"Total SubAgents: {result.get('total_subagents')}")
    print(f"Recent Tools (30d): {result.get('recent_tools_30d')}")

    print("\nCategories:")
    for cat, count in result.get('categories', {}).items():
        print(f"  {cat}: {count}")

    print("\nProtocols:")
    for proto, count in result.get('protocols', {}).items():
        print(f"  {proto}: {count}")

    return result


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CONTRIBUTION API TEST SUITE")
    print("="*60)

    # Get all YAML files
    yaml_files = sorted(EXAMPLES_DIR.glob("*.yaml"))

    if not yaml_files:
        print("\nNo YAML files found in examples_v2/")
        return

    print(f"\nFound {len(yaml_files)} YAML files")

    # Test 1: Validate all YAML files
    print("\n" + "="*60)
    print("PHASE 1: YAML VALIDATION")
    print("="*60)

    validation_results = {}
    for yaml_file in yaml_files:
        result = await test_yaml_validation(yaml_file)
        validation_results[yaml_file.name] = result

    # Summary
    valid_count = sum(1 for r in validation_results.values() if r.get('valid'))
    print(f"\n{'='*60}")
    print(f"Validation Summary: {valid_count}/{len(yaml_files)} valid")
    print('='*60)

    # Test 2: Import valid YAML files
    print("\n" + "="*60)
    print("PHASE 2: YAML IMPORT")
    print("="*60)

    import_results = {}
    for yaml_file in yaml_files:
        if validation_results[yaml_file.name].get('valid'):
            result = await test_yaml_import(yaml_file, auto_index=True)
            import_results[yaml_file.name] = result
        else:
            print(f"\nSkipping import of {yaml_file.name} (validation failed)")

    # Summary
    success_count = sum(1 for r in import_results.values() if r.get('success'))
    print(f"\n{'='*60}")
    print(f"Import Summary: {success_count}/{len(import_results)} successful")
    print('='*60)

    # Note about duplicates
    if success_count < len(import_results):
        print("\nNote: Some imports may have failed due to duplicates (already imported)")
        print("This is expected if running the test multiple times.")

    # Test 3: Search functionality
    print("\n" + "="*60)
    print("PHASE 3: SEARCH TESTING")
    print("="*60)

    # Test different search queries
    search_queries = [
        "web search",
        "image processing",
        "encryption security",
        "database migrations",
        "weather forecast",
        "machine learning inference",
    ]

    for query in search_queries:
        await test_search_tools(query, top_k=3)

    # Test 4: Facets
    print("\n" + "="*60)
    print("PHASE 4: FACETS AND STATISTICS")
    print("="*60)

    await test_facets()
    await test_statistics()

    # Final summary
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print(f"\nYAML Files: {len(yaml_files)}")
    print(f"Valid YAMLs: {valid_count}")
    print(f"Successful Imports: {success_count}")
    print("\nAll tests completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
