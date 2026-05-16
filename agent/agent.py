from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a


def describe_infrastructure() -> dict:
    """Returns a description of AI infrastructure components running in the cluster."""
    return {
        "cluster": "kind-abox",
        "components": {
            "kagent": {
                "version": "0.9.4",
                "namespace": "kagent",
                "description": "Kubernetes-native LLM agent management (kagent.dev)",
                "agents": ["k8s-inspector"],
            },
            "agentgateway": {
                "namespace": "agentgateway-system",
                "description": "AI traffic gateway supporting MCP, A2A, and OpenAI-compatible APIs",
                "backends": {
                    "gemini": {
                        "model": "gemini-3.1-flash-lite",
                        "provider": "Google",
                        "path": "/gemini",
                    },
                    "kagent-tools-mcp": {
                        "protocol": "StreamableHTTP",
                        "path": "/kagent-mcp",
                    },
                },
            },
        },
    }


def list_ai_agents() -> dict:
    """Lists all AI agents deployed in the cluster with their capabilities."""
    return {
        "agents": [
            {
                "name": "k8s-inspector",
                "framework": "kagent",
                "namespace": "kagent",
                "type": "Declarative",
                "model": "gemini-3.1-flash-lite via agentgateway",
                "description": "Read-only Kubernetes cluster inspector",
                "tools": [
                    "k8s_get_available_api_resources",
                    "k8s_get_cluster_configuration",
                    "k8s_get_resources",
                    "k8s_get_resource_yaml",
                    "k8s_get_events",
                    "k8s_get_pod_logs",
                    "k8s_check_service_connectivity",
                ],
            },
            {
                "name": "ai-infra-advisor",
                "framework": "Google ADK",
                "namespace": "a2a-agent",
                "type": "A2A",
                "model": "gemini-3.1-flash-lite via agentgateway",
                "description": "AI infrastructure advisor — this agent",
                "well_known_uri": "/ai-infra-advisor/.well-known/agent-card.json",
            },
        ]
    }


def get_mcp_endpoints() -> dict:
    """Returns MCP server endpoints exposed in the cluster via agentgateway."""
    return {
        "endpoints": [
            {
                "name": "kagent-tools",
                "gateway_path": "/kagent-mcp",
                "protocol": "StreamableHTTP",
                "backend": "kagent-tools.kagent.svc.cluster.local:8084",
                "tool_count": 124,
                "description": "Full suite of Kubernetes management tools from kagent",
            }
        ]
    }


root_agent = Agent(
    model=LiteLlm(model="openai/gemini-3.1-flash-lite"),
    name="ai-infra-advisor",
    description=(
        "AI infrastructure advisor for the k8s lab cluster. "
        "Provides information about deployed AI components, agents, and MCP endpoints."
    ),
    instruction=(
        "You are an AI infrastructure advisor for a Kubernetes lab cluster running in a Codespace. "
        "You have knowledge about the AI components running in the cluster: kagent agents, "
        "agentgateway backends, and MCP servers. Help users understand the AI infrastructure "
        "topology, available agents, and how to interact with them. "
        "Use your tools to retrieve current infrastructure state before answering."
    ),
    tools=[describe_infrastructure, list_ai_agents, get_mcp_endpoints],
)

a2a_app = to_a2a(root_agent, port=8000)
