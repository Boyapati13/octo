import sys
import asyncio
from pathlib import Path

# Ensure the octo directory is in the python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("mcp package is not installed. Please run: pip install mcp")
    sys.exit(1)

# Create the MCP server
mcp = FastMCP("OCTO-Pro")

@mcp.tool()
async def octo_deerflow_task(goal: str, mode: str = "standard") -> str:
    """
    Submits an arbitrary long-horizon task to DeerFlow's LangGraph super-agent.
    
    Args:
        goal: What the agent should accomplish (e.g., "Research the latest async python patterns").
        mode: Execution mode. Options: "flash" (fast), "standard" (balanced), "pro" (planning), "ultra" (full sub-agent orchestration).
    """
    try:
        from actions.deerflow_task import deerflow_task
        
        result = deerflow_task({
            "goal": goal,
            "mode": mode,
            "save": False
        })
        return str(result)
    except Exception as e:
        return f"Error executing DeerFlow task: {str(e)}"

@mcp.tool()
async def octo_dev_agent(description: str, language: str = "python", project_name: str = "OCTO_Project") -> str:
    """
    Instructs OCTO's dev_agent to autonomously plan, write, install dependencies, and self-heal a complete coding project.
    
    Args:
        description: Detailed description of the project you want to build.
        language: Programming language (default: "python").
        project_name: A folder name for the project (no spaces).
    """
    try:
        from actions.dev_agent import dev_agent
        
        result = dev_agent({
            "description": description,
            "language": language,
            "project_name": project_name,
            "timeout": 30
        })
        return str(result)
    except Exception as e:
        return f"Error executing dev_agent: {str(e)}"

@mcp.tool()
async def octo_deep_research(topic: str) -> str:
    """
    Triggers OCTO's deep web-crawling and synthesis module for extensive research tasks.
    
    Args:
        topic: The specific topic to research deeply.
    """
    try:
        from actions.deep_research import deep_research
        
        result = deep_research({
            "topic": topic,
            "report_type": "detailed",
            "save": False
        })
        return str(result)
    except Exception as e:
        return f"Error executing deep research: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
