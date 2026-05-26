import json
import logging
import os
import uuid
from typing import Callable, Optional

# Instead of re-inventing the wheel and hitting `DeerFlowClient` path depth errors,
# we use the robust HTTP endpoints provided in deerflow_bridge if the gateway is running.
# If the gateway is not running, we try the embedded client directly, but proxy it securely.
from deerflow_bridge import is_http_running, _http_stream, get_or_create_thread, _get_embedded_client

log = logging.getLogger(__name__)

def multi_agent_loop(
    parameters: dict,
    on_progress: Optional[Callable[[str], None]] = None,
    player=None,
    speak=None,
) -> str:
    """
    Executes a task iteratively using the full multi-agent structure.
    It hooks into DeerFlow's LangGraph backend (either via HTTP gateway or embedded),
    allowing it to plan, code, use MCP tools, execute shell commands, and verify logic.
    """
    p = parameters or {}
    task = p.get("task", "").strip()
    working_dir = p.get("working_dir", "").strip()
    session_id = p.get("session_id", "default")
    model = p.get("model", "auto")

    if not task:
        return "No task provided."

    thread_id = get_or_create_thread(session_id)

    # If a working dir is provided, wrap the prompt to give the agent context.
    context_task = task
    if working_dir:
        context_task = f"[Context: You are operating in project directory {working_dir}]\n{task}"

    if on_progress:
        on_progress("Initializing multi-agent swarm...\n")

    # PREFERRED: HTTP Gateway (Runs in isolated Sandbox modes, prevents path depth errors)
    if is_http_running():
        try:
            if on_progress:
                on_progress("[Using Gateway API for LangGraph orchestration]\n")

            body = {
                "message": context_task,
                "model": model,
                "stream": True,
                "subagents": True, # enable full swarm capabilities
                "thread_id": thread_id
            }

            chunks = []
            for chunk in _http_stream("/chat", body):
                # The stream from gateway yields server-sent events
                if chunk.startswith("data: "):
                    data_str = chunk[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        # Depending on the event type, extract delta
                        if data.get("type") == "ai" and "content" in data:
                            delta = data["content"]
                            chunks.append(delta)
                            if on_progress:
                                on_progress(delta)
                    except json.JSONDecodeError:
                        pass

            final_output = "".join(chunks)
            return final_output if final_output else "Task completed (no output)."

        except Exception as e:
            err_msg = f"Multi-agent HTTP execution failed: {e}"
            log.error(err_msg)
            return err_msg

    # FALLBACK: Embedded client
    client = _get_embedded_client()
    if client:
        try:
            if on_progress:
                on_progress("[Using Embedded LangGraph Orchestration]\n")

            chunks_dict = {}
            last_id = ""
            for event in client.stream(context_task, thread_id=thread_id, subagent_enabled=True):
                if event.type == "messages-tuple" and event.data.get("type") == "ai":
                    msg_id = event.data.get("id") or ""
                    delta = event.data.get("content", "")
                    if delta:
                        chunks_dict.setdefault(msg_id, []).append(delta)
                        last_id = msg_id
                        if on_progress:
                            on_progress(delta)

            final_output = "".join(chunks_dict.get(last_id, ()))
            return final_output if final_output else "Task completed (no output)."
        except Exception as e:
            err_msg = f"Multi-agent embedded execution failed: {e}"
            log.error(err_msg)
            return err_msg

    # TOTAL FALLBACK
    return "Multi-agent framework (DeerFlow Gateway/Embedded) is completely unavailable. Please start the gateway."
