import pytest
from unittest.mock import patch
from datetime import datetime

# Import the module to be tested
from memory import memory_manager

@pytest.fixture
def mock_datetime():
    with patch("memory.memory_manager.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2023, 10, 27)
        yield mock_dt

def test_update_memory_invalid_input():
    with patch("memory.memory_manager.load_memory") as mock_load, \
         patch("memory.memory_manager.save_memory") as mock_save:

        mock_load.return_value = {"notes": {}}

        # Test with None
        result = memory_manager.update_memory(None)
        assert result == {"notes": {}}
        mock_save.assert_not_called()

        # Test with empty dict
        result = memory_manager.update_memory({})
        assert result == {"notes": {}}
        mock_save.assert_not_called()

        # Test with invalid type (list)
        result = memory_manager.update_memory(["not", "a", "dict"])
        assert result == {"notes": {}}
        mock_save.assert_not_called()

def test_update_memory_new_entry(mock_datetime):
    with patch("memory.memory_manager.load_memory") as mock_load, \
         patch("memory.memory_manager.save_memory") as mock_save:

        mock_load.return_value = {"notes": {}}

        update = {"notes": {"color": "blue"}}
        result = memory_manager.update_memory(update)

        expected_memory = {
            "notes": {
                "color": {"value": "blue", "updated": "2023-10-27"}
            }
        }

        assert result == expected_memory
        mock_save.assert_called_once_with(expected_memory)

def test_update_memory_existing_entry_new_value(mock_datetime):
    with patch("memory.memory_manager.load_memory") as mock_load, \
         patch("memory.memory_manager.save_memory") as mock_save:

        mock_load.return_value = {
            "notes": {
                "color": {"value": "red", "updated": "2023-10-26"}
            }
        }

        update = {"notes": {"color": "blue"}}
        result = memory_manager.update_memory(update)

        expected_memory = {
            "notes": {
                "color": {"value": "blue", "updated": "2023-10-27"}
            }
        }

        assert result == expected_memory
        mock_save.assert_called_once_with(expected_memory)

def test_update_memory_existing_entry_same_value(mock_datetime):
    with patch("memory.memory_manager.load_memory") as mock_load, \
         patch("memory.memory_manager.save_memory") as mock_save:

        mock_load.return_value = {
            "notes": {
                "color": {"value": "red", "updated": "2023-10-26"}
            }
        }

        update = {"notes": {"color": "red"}}
        result = memory_manager.update_memory(update)

        # Value is same, should not save
        expected_memory = {
            "notes": {
                "color": {"value": "red", "updated": "2023-10-26"}
            }
        }
        assert result == expected_memory
        mock_save.assert_not_called()

def test_update_memory_recursive_merge(mock_datetime):
    with patch("memory.memory_manager.load_memory") as mock_load, \
         patch("memory.memory_manager.save_memory") as mock_save:

        mock_load.return_value = {
            "preferences": {
                "food": {"value": "pizza", "updated": "2023-10-26"}
            }
        }

        update = {
            "preferences": {"drink": "water"},
            "projects": {"ai": "learning"}
        }
        result = memory_manager.update_memory(update)

        expected_memory = {
            "preferences": {
                "food": {"value": "pizza", "updated": "2023-10-26"},
                "drink": {"value": "water", "updated": "2023-10-27"}
            },
            "projects": {
                "ai": {"value": "learning", "updated": "2023-10-27"}
            }
        }

        assert result == expected_memory
        mock_save.assert_called_once_with(expected_memory)

def test_update_memory_ignore_empty_or_none(mock_datetime):
    with patch("memory.memory_manager.load_memory") as mock_load, \
         patch("memory.memory_manager.save_memory") as mock_save:

        mock_load.return_value = {
            "notes": {
                "color": {"value": "red", "updated": "2023-10-26"}
            }
        }

        # None and empty strings should be ignored
        update = {
            "notes": {
                "shape": None,
                "size": "",
                "texture": "   ",
                "color": "red"  # unchanged
            }
        }
        result = memory_manager.update_memory(update)

        expected_memory = {
            "notes": {
                "color": {"value": "red", "updated": "2023-10-26"}
            }
        }

        assert result == expected_memory
        mock_save.assert_not_called()
