import pytest
from pathlib import Path
from unittest.mock import MagicMock

from agent.hermes_bridge import (
    create_scheduled,
    list_scheduled,
    delete_scheduled,
    _validate_cron,
    write_gateway_config,
    _cron_matches,
)
import datetime as _dt


def test_validate_cron_valid():
    _validate_cron("0 12 * * *")
    _validate_cron("*/5 * * * *")


def test_validate_cron_invalid():
    with pytest.raises(ValueError, match="Invalid cron expression"):
        _validate_cron("0 12")


def test_create_scheduled(mocker):
    mock_con = MagicMock()
    mock_connect = mocker.patch("sqlite3.connect", return_value=mock_con)

    result = create_scheduled("test prompt", "0 12 * * *", "test label")

    assert result is not None
    assert result["prompt"] == "test prompt"
    assert result["schedule"] == "0 12 * * *"
    assert result["label"] == "test label"
    assert result["enabled"] is True
    assert "id" in result

    assert mock_con.execute.call_count == 2
    assert mock_con.commit.call_count == 2


def test_create_scheduled_invalid_cron():
    result = create_scheduled("test prompt", "invalid cron")
    assert result is None


def test_list_scheduled(mocker):
    mock_con = MagicMock()
    mock_connect = mocker.patch("sqlite3.connect", return_value=mock_con)

    mock_execute = MagicMock()
    mock_execute.fetchall.return_value = [
        ("id1", "prompt1", "0 12 * * *", "label1", 1, "2023-01-01T00:00:00"),
        ("id2", "prompt2", "*/5 * * * *", "", 0, "2023-01-02T00:00:00")
    ]
    mock_con.execute.return_value = mock_execute

    results = list_scheduled()

    assert len(results) == 2
    assert results[0]["id"] == "id1"
    assert results[0]["enabled"] is True
    assert results[1]["id"] == "id2"
    assert results[1]["enabled"] is False


def test_delete_scheduled(mocker):
    mock_con = MagicMock()
    mock_connect = mocker.patch("sqlite3.connect", return_value=mock_con)

    delete_scheduled("test_id")

    mock_con.execute.assert_any_call("DELETE FROM jobs WHERE id=?", ("test_id",))
    assert mock_con.commit.call_count == 2


def test_write_gateway_config(mocker):
    mock_path = MagicMock()
    mocker.patch("agent.hermes_bridge.GW_CFG_PATH", mock_path)

    test_data = {"test_key": "test_value"}
    write_gateway_config(test_data)

    mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_path.write_text.assert_called_once()
    args, kwargs = mock_path.write_text.call_args
    import json
    assert json.loads(args[0]) == test_data

def test_cron_matches():
    now = _dt.datetime(2023, 10, 25, 12, 30) # Wednesday
    assert _cron_matches("30 12 25 10 *", now)
    assert _cron_matches("*/30 * * * *", now)
    assert _cron_matches("30 12 * * *", now)
    assert _cron_matches("30 12 * * 2", now) # 2 = Wednesday in 0-6 where 0 is Monday
    assert not _cron_matches("31 12 25 10 *", now)
