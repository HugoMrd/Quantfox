import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


# Mock config before importing app
@pytest.fixture(autouse=True)
def mock_config():
    mock_cfg = MagicMock()
    mock_cfg.database.connection_string = "host=localhost dbname=test"
    mock_cfg.celery.broker_url = "redis://localhost:6379/0"
    mock_cfg.celery.result_backend = "redis://localhost:6379/1"
    mock_cfg.server.host = "0.0.0.0"
    mock_cfg.server.port = 8001

    with patch("app.config.get_config", return_value=mock_cfg):
        with patch("app.celery_app.get_config", return_value=mock_cfg):
            yield mock_cfg


@pytest.fixture
def client(mock_config):
    from app.main import app
    return TestClient(app)


class TestHealthCheck:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "python-api"


class TestDateValidation:
    def test_missing_start_date(self, client):
        response = client.get("/prices/average?end_date=2025-01-31")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "MISSING_PARAMETER"
        assert "start_date" in data["error"]["message"]

    def test_missing_end_date(self, client):
        response = client.get("/prices/average?start_date=2025-01-01")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "MISSING_PARAMETER"
        assert "end_date" in data["error"]["message"]

    def test_missing_both_dates(self, client):
        response = client.get("/prices/average")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_invalid_start_date_format_dd_mm_yyyy(self, client):
        response = client.get("/prices/average?start_date=01-01-2025&end_date=2025-01-31")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_FORMAT"
        assert "start_date" in data["error"]["message"]

    def test_invalid_end_date_format_dd_mm_yyyy(self, client):
        response = client.get("/prices/average?start_date=2025-01-01&end_date=31-01-2025")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_FORMAT"
        assert "end_date" in data["error"]["message"]

    def test_invalid_date_format_with_slashes(self, client):
        response = client.get("/prices/average?start_date=2025/01/01&end_date=2025-01-31")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_FORMAT"

    def test_invalid_date_format_text(self, client):
        response = client.get("/prices/average?start_date=january&end_date=2025-01-31")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_FORMAT"

    def test_invalid_date_format_incomplete(self, client):
        response = client.get("/prices/average?start_date=2025-01&end_date=2025-01-31")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_FORMAT"

    def test_invalid_date_range_end_before_start(self, client):
        response = client.get("/prices/average?start_date=2025-01-31&end_date=2025-01-01")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_RANGE"

    def test_invalid_date_range_different_months(self, client):
        response = client.get("/prices/average?start_date=2025-02-15&end_date=2025-01-15")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_DATE_RANGE"


class TestValidDateRanges:
    def test_equal_dates_valid(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [{"date": "2025-01-15", "average_price": 113.78}]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-15&end_date=2025-01-15")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 1
            assert data["data"][0]["date"] == "2025-01-15"

    def test_first_week_of_january(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-01", "average_price": 101.05},
                {"date": "2025-01-02", "average_price": 102.45},
                {"date": "2025-01-03", "average_price": 99.43},
                {"date": "2025-01-04", "average_price": 104.70},
                {"date": "2025-01-05", "average_price": 97.40},
                {"date": "2025-01-06", "average_price": 100.38},
                {"date": "2025-01-07", "average_price": 102.75},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-01&end_date=2025-01-07")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 7

    def test_second_week_of_january(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-08", "average_price": 104.87},
                {"date": "2025-01-09", "average_price": 103.20},
                {"date": "2025-01-10", "average_price": 106.89},
                {"date": "2025-01-11", "average_price": 108.17},
                {"date": "2025-01-12", "average_price": 109.18},
                {"date": "2025-01-13", "average_price": 110.89},
                {"date": "2025-01-14", "average_price": 111.92},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-08&end_date=2025-01-14")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 7

    def test_third_week_of_january(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-15", "average_price": 113.78},
                {"date": "2025-01-16", "average_price": 112.83},
                {"date": "2025-01-17", "average_price": 110.92},
                {"date": "2025-01-18", "average_price": 109.89},
                {"date": "2025-01-19", "average_price": 108.75},
                {"date": "2025-01-20", "average_price": 107.13},
                {"date": "2025-01-21", "average_price": 105.90},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-15&end_date=2025-01-21")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 7

    def test_fourth_week_of_january(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-22", "average_price": 104.67},
                {"date": "2025-01-23", "average_price": 103.91},
                {"date": "2025-01-24", "average_price": 103.02},
                {"date": "2025-01-25", "average_price": 101.75},
                {"date": "2025-01-26", "average_price": 101.04},
                {"date": "2025-01-27", "average_price": 99.90},
                {"date": "2025-01-28", "average_price": 98.70},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-22&end_date=2025-01-28")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 7

    def test_last_days_of_january(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-29", "average_price": 97.63},
                {"date": "2025-01-30", "average_price": 96.80},
                {"date": "2025-01-31", "average_price": 96.03},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-29&end_date=2025-01-31")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 3

    def test_full_month_january(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [{"date": f"2025-01-{i:02d}", "average_price": 100.0 + i} for i in range(1, 32)]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-01&end_date=2025-01-31")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 31

    def test_mid_month_range(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-10", "average_price": 106.89},
                {"date": "2025-01-11", "average_price": 108.17},
                {"date": "2025-01-12", "average_price": 109.18},
                {"date": "2025-01-13", "average_price": 110.89},
                {"date": "2025-01-14", "average_price": 111.92},
                {"date": "2025-01-15", "average_price": 113.78},
                {"date": "2025-01-16", "average_price": 112.83},
                {"date": "2025-01-17", "average_price": 110.92},
                {"date": "2025-01-18", "average_price": 109.89},
                {"date": "2025-01-19", "average_price": 108.75},
                {"date": "2025-01-20", "average_price": 107.13},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-10&end_date=2025-01-20")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 11


class TestResponseFormat:
    def test_response_has_data_key(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [{"date": "2025-01-01", "average_price": 101.05}]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-01&end_date=2025-01-01")
            assert response.status_code == 200
            data = response.json()
            assert "data" in data

    def test_each_item_has_date_and_average_price(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [
                {"date": "2025-01-01", "average_price": 101.05},
                {"date": "2025-01-02", "average_price": 102.45},
            ]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-01&end_date=2025-01-02")
            assert response.status_code == 200
            data = response.json()
            for item in data["data"]:
                assert "date" in item
                assert "average_price" in item

    def test_average_price_is_numeric(self, client):
        with patch("app.main.compute_daily_averages_task") as mock_task:
            mock_result = MagicMock()
            mock_result.get.return_value = [{"date": "2025-01-01", "average_price": 101.05}]
            mock_task.delay.return_value = mock_result

            response = client.get("/prices/average?start_date=2025-01-01&end_date=2025-01-01")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["data"][0]["average_price"], (int, float))


class TestErrorResponseFormat:
    def test_error_has_code_and_message(self, client):
        response = client.get("/prices/average")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    def test_error_code_is_string(self, client):
        response = client.get("/prices/average")
        assert response.status_code == 400
        data = response.json()
        assert isinstance(data["error"]["code"], str)

    def test_error_message_is_string(self, client):
        response = client.get("/prices/average")
        assert response.status_code == 400
        data = response.json()
        assert isinstance(data["error"]["message"], str)
