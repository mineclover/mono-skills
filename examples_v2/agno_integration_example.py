#!/usr/bin/env python3
"""
Example: Integrating Agno agents with SubAgent Registry

This example shows how to:
1. Deploy an agent on Agno
2. Register the deployment in SubAgent Registry
3. Update health status periodically
4. Discover and use running agents from the registry
"""

import asyncio
import httpx
from typing import List, Dict, Any


# Registry API configuration
REGISTRY_URL = "http://localhost:8000"


# ============================================================================
# Step 1: Deploy Agent on Agno
# ============================================================================

async def deploy_agent_on_agno(agent_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Deploy an agent on Agno platform.

    In a real scenario, you would use Agno's SDK or API.
    This is a simplified example.

    Args:
        agent_config: Agent configuration

    Returns:
        Deployment info including agent_id and endpoint_url
    """
    print("\n=== Deploying Agent on Agno ===")
    print(f"Agent Name: {agent_config['name']}")
    print(f"Tools: {', '.join(agent_config['tools'])}")

    # Simulated Agno deployment
    # In reality, you'd call Agno's API:
    # agno_client.agents.create(...)

    deployment_info = {
        "agent_id": "agno_agent_abc123",
        "agent_name": agent_config["name"],
        "endpoint_url": f"https://api.agno.example.com/agents/{agent_config['name']}",
        "api_key": "agno_api_key_xyz789",
        "status": "running",
    }

    print(f"✓ Agent deployed successfully!")
    print(f"  Agent ID: {deployment_info['agent_id']}")
    print(f"  Endpoint: {deployment_info['endpoint_url']}")

    return deployment_info


# ============================================================================
# Step 2: Register Deployment in SubAgent Registry
# ============================================================================

async def register_in_registry(
    tool_name: str,
    subagent_name: str,
    agno_deployment: Dict[str, str],
    environment: str = "production",
) -> str:
    """
    Register the Agno deployment in SubAgent Registry.

    Args:
        tool_name: Name of the tool (from registry)
        subagent_name: Name of the subagent (from registry)
        agno_deployment: Agno deployment info
        environment: deployment environment

    Returns:
        Deployment ID from registry
    """
    print("\n=== Registering in SubAgent Registry ===")

    async with httpx.AsyncClient() as client:
        # Register deployment
        deployment_data = {
            "tool_name": tool_name,
            "subagent_name": subagent_name,
            "deployment_name": f"{tool_name}-{environment}",
            "description": f"Agno deployment of {tool_name}",
            "environment": environment,
            "region": "us-east-1",
            "endpoint": {
                "url": agno_deployment["endpoint_url"],
                "method": "POST",
                "auth_type": "bearer",
                "headers": {
                    "Authorization": f"Bearer {agno_deployment['api_key']}",
                    "Content-Type": "application/json",
                },
                "health_check_url": f"{agno_deployment['endpoint_url']}/health",
                "timeout_ms": 30000,
            },
            "metadata": {
                "platform": "agno",
                "platform_version": "1.0.0",
                "deployed_by": "devops-team",
                "deployment_config": {
                    "agent_id": agno_deployment["agent_id"],
                    "agent_name": agno_deployment["agent_name"],
                },
                "tags": ["production", "agno", "web-search"],
            },
        }

        response = await client.post(
            f"{REGISTRY_URL}/deployments/",
            json=deployment_data,
            timeout=30.0,
        )

        if response.status_code == 201:
            result = response.json()
            deployment_id = result["deployment_id"]
            print(f"✓ Registered in registry!")
            print(f"  Deployment ID: {deployment_id}")
            return deployment_id
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Error: {response.text}")
            raise Exception(f"Failed to register deployment: {response.text}")


# ============================================================================
# Step 3: Update Health Status
# ============================================================================

async def update_health_status(
    deployment_id: str,
    status: str = "running",
    uptime_seconds: int = 0,
    request_count: int = 0,
    avg_latency_ms: float = 0.0,
):
    """
    Update health status in the registry.

    This should be called periodically (e.g., every 60 seconds) to
    keep the registry updated about the agent's status.

    Args:
        deployment_id: Registry deployment ID
        status: Current status (running, stopped, error, etc.)
        uptime_seconds: Uptime in seconds
        request_count: Total request count
        avg_latency_ms: Average latency in milliseconds
    """
    async with httpx.AsyncClient() as client:
        health_data = {
            "status": status,
            "uptime_seconds": uptime_seconds,
            "request_count": request_count,
            "avg_latency_ms": avg_latency_ms,
        }

        response = await client.post(
            f"{REGISTRY_URL}/deployments/{deployment_id}/health",
            json=health_data,
            timeout=30.0,
        )

        if response.status_code == 200:
            print(f"✓ Health status updated: {status}")
        else:
            print(f"✗ Health update failed: {response.status_code}")


async def health_monitor_loop(deployment_id: str, interval_seconds: int = 60):
    """
    Continuously monitor and report health status.

    Args:
        deployment_id: Registry deployment ID
        interval_seconds: Update interval
    """
    print(f"\n=== Starting Health Monitor (interval: {interval_seconds}s) ===")

    uptime = 0
    request_count = 0

    while True:
        try:
            # Simulate metrics (in reality, get from Agno or your monitoring system)
            uptime += interval_seconds
            request_count += 15  # Simulated requests
            avg_latency = 250.5  # Simulated latency

            await update_health_status(
                deployment_id=deployment_id,
                status="running",
                uptime_seconds=uptime,
                request_count=request_count,
                avg_latency_ms=avg_latency,
            )

            await asyncio.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n✓ Health monitor stopped")
            break
        except Exception as e:
            print(f"✗ Error in health monitor: {e}")
            await asyncio.sleep(interval_seconds)


# ============================================================================
# Step 4: Discover Running Agents
# ============================================================================

async def discover_running_tools(environment: str = "production"):
    """
    Discover what tools are currently running and available.

    This helps users find deployed agents they can use immediately
    without installing anything locally.

    Args:
        environment: Environment to search (production, staging, etc.)
    """
    print(f"\n=== Discovering Running Tools ({environment}) ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{REGISTRY_URL}/tools/running",
            params={"environment": environment, "limit": 10},
            timeout=30.0,
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total']} running tools:\n")

            for tool in result["results"]:
                print(f"• {tool['display_name']} ({tool['name']})")
                print(f"  Category: {tool['category']}")
                print(f"  Running deployments: {tool['running_deployments']}")

                for deployment in tool["deployments"][:2]:  # Show first 2
                    print(f"  - {deployment['deployment_name']}")
                    print(f"    Endpoint: {deployment['endpoint']['url']}")
                    print(f"    Status: {deployment['status']['status']}")
                print()
        else:
            print(f"✗ Discovery failed: {response.status_code}")


async def find_tool_deployments(tool_name: str):
    """
    Find all deployments of a specific tool.

    Args:
        tool_name: Name of the tool to find
    """
    print(f"\n=== Finding Deployments for '{tool_name}' ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{REGISTRY_URL}/tools/{tool_name}/deployments",
            timeout=30.0,
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Tool: {result['display_name']}")
            print(f"Total deployments: {result['total_deployments']}")
            print(f"Running: {result['running_deployments']}")
            print(f"Production: {result['production_deployments']}\n")

            for deployment in result["deployments"]:
                print(f"• {deployment['deployment_name']}")
                print(f"  Environment: {deployment['environment']}")
                print(f"  Platform: {deployment['metadata']['platform']}")
                print(f"  Endpoint: {deployment['endpoint']['url']}")
                print(f"  Status: {deployment['status']['status']}")
                print()
        else:
            print(f"✗ Not found: {response.status_code}")


async def discover_agno_agents():
    """
    Discover all tools deployed on Agno platform.
    """
    print("\n=== Discovering Agno Deployments ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{REGISTRY_URL}/tools/by-platform/agno",
            params={"environment": "production", "limit": 20},
            timeout=30.0,
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total']} tools on Agno:\n")

            for tool in result["results"]:
                print(f"• {tool['display_name']}")
                print(f"  Deployments: {tool['total_deployments']}")
                for deployment in tool["deployments"]:
                    print(f"  - {deployment['deployment_name']}: {deployment['endpoint']['url']}")
                print()
        else:
            print(f"✗ Discovery failed: {response.status_code}")


# ============================================================================
# Main Integration Flow
# ============================================================================

async def main_deployment_flow():
    """
    Complete flow: Deploy on Agno → Register in Registry → Monitor Health
    """
    print("="*60)
    print("AGNO + SUBAGENT REGISTRY INTEGRATION EXAMPLE")
    print("="*60)

    # Agent configuration
    agent_config = {
        "name": "web-search-agent",
        "tools": ["web_search", "extract_content"],
        "model": "claude-3-sonnet",
        "memory_enabled": True,
    }

    try:
        # Step 1: Deploy on Agno
        agno_deployment = await deploy_agent_on_agno(agent_config)

        # Step 2: Register in Registry
        deployment_id = await register_in_registry(
            tool_name="web_search",
            subagent_name="tavily-search-toolkit",
            agno_deployment=agno_deployment,
            environment="production",
        )

        # Step 3: Initial health check
        await update_health_status(
            deployment_id=deployment_id,
            status="running",
            uptime_seconds=0,
            request_count=0,
            avg_latency_ms=0.0,
        )

        # Step 4: Start health monitoring (in background)
        print("\n✓ Deployment complete!")
        print(f"  Deployment ID: {deployment_id}")
        print("\nStarting health monitor...")
        print("Press Ctrl+C to stop\n")

        # Monitor health (this will run until interrupted)
        await health_monitor_loop(deployment_id, interval_seconds=10)

    except Exception as e:
        print(f"\n✗ Error: {e}")


async def main_discovery_flow():
    """
    Complete flow: Discover running tools and agents
    """
    print("="*60)
    print("DISCOVERING RUNNING TOOLS FROM REGISTRY")
    print("="*60)

    # Discover all running tools
    await discover_running_tools("production")

    # Find specific tool deployments
    await find_tool_deployments("web_search")

    # Find all Agno agents
    await discover_agno_agents()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "discover":
        # Discovery mode
        asyncio.run(main_discovery_flow())
    else:
        # Deployment mode
        asyncio.run(main_deployment_flow())
