import pytest
from unittest.mock import patch, MagicMock


def _mock_response(items):
    r = MagicMock()
    r.json.return_value = {'items': items}
    r.raise_for_status = MagicMock()
    return r


def test_fetch_directory_items_returns_all_items():
    """Single request with size=500; returns all items from API."""
    items = [{'item': {'name': f's{i}', 'title': f'S{i}', 'additionalFields': {}}} for i in range(267)]
    with patch('lambda_handler.get', return_value=_mock_response(items)) as mock_get:
        from lambda_handler import fetch_directory_items
        result = fetch_directory_items()
        assert len(result) == 267
        assert mock_get.call_count == 1
        url = mock_get.call_args[0][0]
        assert 'size=500' in url
        assert 'from=' not in url


def test_fetch_directory_items_handles_error_gracefully():
    """Network error on first page returns empty list (logged, not raised)."""
    with patch('lambda_handler.get', side_effect=Exception("timeout")):
        from lambda_handler import fetch_directory_items
        result = fetch_directory_items()
        assert result == []


def test_scraping_guard_raises_on_empty_result():
    """get_data_from_scrape raises RuntimeError when < 100 services are parsed."""
    mock_response = MagicMock()
    mock_response.content = b'<html><body><script>no nav data here</script></body></html>'
    mock_response.raise_for_status = MagicMock()
    with patch('lambda_handler.get', return_value=mock_response):
        from lambda_handler import get_data_from_scrape
        with pytest.raises(RuntimeError, match="Scraping returned only"):
            get_data_from_scrape()
