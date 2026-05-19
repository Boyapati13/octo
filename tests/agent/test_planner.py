import json
import pytest
from unittest.mock import MagicMock
import sys
import os

# Ensure core can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.planner import create_plan

def test_create_plan_happy_path(mocker):
    # Mock text_llm before it's imported in create_plan
    mock_text_llm = MagicMock()
    mock_text_llm.ask.return_value = '''
    ```json
    {
        "goal": "do something",
        "steps": [
            {
                "step": 1,
                "tool": "web_search",
                "description": "search",
                "parameters": {"query": "something"}
            }
        ]
    }
    ```
    '''
    mocker.patch.dict("sys.modules", {"core": MagicMock(text_llm=mock_text_llm)})

    plan = create_plan(goal="do something", context="context")

    assert plan["goal"] == "do something"
    assert len(plan["steps"]) == 1
    assert plan["steps"][0]["tool"] == "web_search"
    mock_text_llm.ask.assert_called_once()
    assert "Context: context" in mock_text_llm.ask.call_args[0][0]

def test_create_plan_generated_code_replacement(mocker):
    mock_text_llm = MagicMock()
    mock_text_llm.ask.return_value = json.dumps({
        "goal": "write code",
        "steps": [
            {
                "step": 1,
                "tool": "generated_code",
                "description": "write python code for me",
                "parameters": {}
            }
        ]
    })
    mocker.patch.dict("sys.modules", {"core": MagicMock(text_llm=mock_text_llm)})

    plan = create_plan(goal="write code")

    assert plan["goal"] == "write code"
    assert len(plan["steps"]) == 1
    assert plan["steps"][0]["tool"] == "web_search"
    assert plan["steps"][0]["parameters"]["query"] == "write python code for me"

def test_create_plan_invalid_structure(mocker):
    mock_text_llm = MagicMock()
    mock_text_llm.ask.return_value = json.dumps({
        "goal": "do something",
        # missing "steps"
    })
    mocker.patch.dict("sys.modules", {"core": MagicMock(text_llm=mock_text_llm)})

    plan = create_plan(goal="do something")

    # Should return fallback plan
    assert plan["goal"] == "do something"
    assert len(plan["steps"]) == 1
    assert plan["steps"][0]["tool"] == "web_search"
    assert plan["steps"][0]["description"] == "Search for: do something"

def test_create_plan_json_decode_error(mocker):
    mock_text_llm = MagicMock()
    mock_text_llm.ask.return_value = "invalid json {"
    mocker.patch.dict("sys.modules", {"core": MagicMock(text_llm=mock_text_llm)})

    plan = create_plan(goal="do something")

    assert plan["goal"] == "do something"
    assert len(plan["steps"]) == 1
    assert plan["steps"][0]["tool"] == "web_search"

def test_create_plan_exception(mocker):
    mock_text_llm = MagicMock()
    mock_text_llm.ask.side_effect = Exception("LLM Error")
    mocker.patch.dict("sys.modules", {"core": MagicMock(text_llm=mock_text_llm)})

    plan = create_plan(goal="do something")

    assert plan["goal"] == "do something"
    assert len(plan["steps"]) == 1
    assert plan["steps"][0]["tool"] == "web_search"
