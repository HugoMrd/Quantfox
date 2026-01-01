"""
Integration tests that verify actual API responses with expected values.
These tests require the Docker services to be running.

Run with: pytest tests/test_integration.py -v
"""
import pytest
import requests

BASE_URL = "http://localhost:8000"

# Expected averages calculated from init.sql data
# Each day's average is calculated from the prices in the SQL file
EXPECTED_AVERAGES = {
    "2025-01-01": 101.05,  # (101.25 + 102.10 + 99.80) / 3
    "2025-01-02": 102.45,  # (103.50 + 102.75 + 101.10) / 3
    "2025-01-03": 99.43,   # (98.40 + 100.20 + 99.70) / 3
    "2025-01-04": 104.70,  # (104.00 + 104.80 + 105.30) / 3
    "2025-01-05": 97.40,   # (97.20 + 96.90 + 98.10) / 3
    "2025-01-06": 100.38,  # (99.50 + 100.25 + 101.00 + 100.75) / 4
    "2025-01-07": 102.75,  # (102.30 + 103.10 + 102.85) / 3
    "2025-01-08": 104.87,  # (104.50 + 105.20 + 104.90) / 3
    "2025-01-09": 103.20,  # (103.80 + 102.60 + 103.20) / 3
    "2025-01-10": 106.89,  # (106.00 + 107.25 + 106.80 + 107.50) / 4
    "2025-01-11": 108.17,  # (108.10 + 107.90 + 108.50) / 3
    "2025-01-12": 109.18,  # (109.20 + 108.75 + 109.60) / 3
    "2025-01-13": 110.89,  # (110.00 + 111.25 + 110.80 + 111.50) / 4
    "2025-01-14": 111.92,  # (112.00 + 111.50 + 112.25) / 3
    "2025-01-15": 113.78,  # (113.10 + 114.00 + 113.75 + 114.25) / 4
    "2025-01-16": 112.83,  # (112.50 + 113.20 + 112.80) / 3
    "2025-01-17": 110.92,  # (111.00 + 110.50 + 111.25) / 3
    "2025-01-18": 109.89,  # (109.80 + 110.25 + 109.50 + 110.00) / 4
    "2025-01-19": 108.75,  # (108.40 + 109.10 + 108.75) / 3
    "2025-01-20": 107.13,  # (107.20 + 106.80 + 107.50 + 107.00) / 4
    "2025-01-21": 105.90,  # (105.60 + 106.20 + 105.90) / 3
    "2025-01-22": 104.67,  # (104.30 + 105.00 + 104.70) / 3
    "2025-01-23": 103.91,  # (103.50 + 104.10 + 103.80 + 104.25) / 4
    "2025-01-24": 103.02,  # (102.80 + 103.30 + 102.95) / 3
    "2025-01-25": 101.75,  # (101.50 + 102.00 + 101.75) / 3
    "2025-01-26": 101.04,  # (100.80 + 101.30 + 100.95 + 101.10) / 4
    "2025-01-27": 99.90,   # (99.60 + 100.20 + 99.90) / 3
    "2025-01-28": 98.70,   # (98.40 + 99.00 + 98.70) / 3
    "2025-01-29": 97.63,   # (97.20 + 97.80 + 97.50 + 98.00) / 4
    "2025-01-30": 96.80,   # (96.50 + 97.10 + 96.80) / 3
    "2025-01-31": 96.03,   # (95.80 + 96.30 + 95.90 + 96.10) / 4
}


def is_api_available():
    """Check if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


# Skip all tests if API is not available
pytestmark = pytest.mark.skipif(
    not is_api_available(),
    reason="API not available. Start Docker services with: docker compose up -d"
)


class TestSingleDayQueries:
    """Test queries for individual days."""

    def test_january_1(self):
        """Test average for January 1st."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-01"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["date"] == "2025-01-01"
        assert data[0]["average_price"] == pytest.approx(EXPECTED_AVERAGES["2025-01-01"], rel=0.01)

    def test_january_15(self):
        """Test average for January 15th (highest average)."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-15", "end_date": "2025-01-15"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["date"] == "2025-01-15"
        assert data[0]["average_price"] == pytest.approx(EXPECTED_AVERAGES["2025-01-15"], rel=0.01)

    def test_january_31(self):
        """Test average for January 31st."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-31", "end_date": "2025-01-31"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["date"] == "2025-01-31"
        assert data[0]["average_price"] == pytest.approx(EXPECTED_AVERAGES["2025-01-31"], rel=0.01)


class TestMultiDayQueries:
    """Test queries spanning multiple days."""

    def test_first_two_days(self):
        """Test January 1-2."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-02"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

        dates = {item["date"]: item["average_price"] for item in data}
        assert dates["2025-01-01"] == pytest.approx(EXPECTED_AVERAGES["2025-01-01"], rel=0.01)
        assert dates["2025-01-02"] == pytest.approx(EXPECTED_AVERAGES["2025-01-02"], rel=0.01)

    def test_first_week(self):
        """Test January 1-7 (first week)."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-07"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 7

        dates = {item["date"]: item["average_price"] for item in data}
        for day in range(1, 8):
            date_str = f"2025-01-0{day}"
            assert date_str in dates
            assert dates[date_str] == pytest.approx(EXPECTED_AVERAGES[date_str], rel=0.01)

    def test_second_week(self):
        """Test January 8-14 (second week)."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-08", "end_date": "2025-01-14"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 7

        dates = {item["date"]: item["average_price"] for item in data}
        for day in range(8, 15):
            date_str = f"2025-01-{day:02d}"
            assert date_str in dates
            assert dates[date_str] == pytest.approx(EXPECTED_AVERAGES[date_str], rel=0.01)

    def test_mid_month(self):
        """Test January 10-20."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-10", "end_date": "2025-01-20"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 11

        dates = {item["date"]: item["average_price"] for item in data}
        for day in range(10, 21):
            date_str = f"2025-01-{day:02d}"
            assert date_str in dates
            assert dates[date_str] == pytest.approx(EXPECTED_AVERAGES[date_str], rel=0.01)

    def test_full_month(self):
        """Test entire month of January (31 days)."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 31

        dates = {item["date"]: item["average_price"] for item in data}
        for day in range(1, 32):
            date_str = f"2025-01-{day:02d}"
            assert date_str in dates
            assert dates[date_str] == pytest.approx(EXPECTED_AVERAGES[date_str], rel=0.01)


class TestPriceTrends:
    """Test that price trends match expected patterns."""

    def test_peak_price_mid_month(self):
        """Verify January 15th has the highest average price."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        data = response.json()["data"]

        # Find the day with highest average
        max_day = max(data, key=lambda x: x["average_price"])
        assert max_day["date"] == "2025-01-15"
        assert max_day["average_price"] == pytest.approx(113.78, rel=0.01)

    def test_lowest_price_end_month(self):
        """Verify January 31st has the lowest average price."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        data = response.json()["data"]

        # Find the day with lowest average
        min_day = min(data, key=lambda x: x["average_price"])
        assert min_day["date"] == "2025-01-31"
        assert min_day["average_price"] == pytest.approx(96.03, rel=0.01)

    def test_price_increases_first_half(self):
        """Verify general upward trend in first half of month."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01", "end_date": "2025-01-15"}
        )
        data = response.json()["data"]

        first_day = next(d for d in data if d["date"] == "2025-01-01")
        last_day = next(d for d in data if d["date"] == "2025-01-15")

        # Price should increase from start to mid-month
        assert last_day["average_price"] > first_day["average_price"]

    def test_price_decreases_second_half(self):
        """Verify general downward trend in second half of month."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-15", "end_date": "2025-01-31"}
        )
        data = response.json()["data"]

        first_day = next(d for d in data if d["date"] == "2025-01-15")
        last_day = next(d for d in data if d["date"] == "2025-01-31")

        # Price should decrease from mid-month to end
        assert last_day["average_price"] < first_day["average_price"]


class TestSpecificRanges:
    """Test specific date ranges with exact values."""

    def test_weekend_jan_4_5(self):
        """Test first weekend of January."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-04", "end_date": "2025-01-05"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

        dates = {item["date"]: item["average_price"] for item in data}
        assert dates["2025-01-04"] == pytest.approx(104.70, rel=0.01)
        assert dates["2025-01-05"] == pytest.approx(97.40, rel=0.01)

    def test_last_three_days(self):
        """Test last three days of January."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-29", "end_date": "2025-01-31"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 3

        dates = {item["date"]: item["average_price"] for item in data}
        assert dates["2025-01-29"] == pytest.approx(97.63, rel=0.01)
        assert dates["2025-01-30"] == pytest.approx(96.80, rel=0.01)
        assert dates["2025-01-31"] == pytest.approx(96.03, rel=0.01)

    def test_days_with_4_prices(self):
        """Test days that have 4 price entries (more data points)."""
        # Days with 4 prices: 6, 10, 13, 15, 18, 20, 23, 26, 29, 31
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-06", "end_date": "2025-01-06"}
        )
        data = response.json()["data"]
        assert data[0]["average_price"] == pytest.approx(100.38, rel=0.01)


class TestHealthEndpoint:
    """Test health check endpoint through Rust API."""

    def test_rust_api_health(self):
        """Test Rust API health endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rust-api"


class TestErrorCases:
    """Test error responses from the API."""

    def test_invalid_date_format(self):
        """Test API returns error for invalid date format."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "01-01-2025", "end_date": "2025-01-31"}
        )
        assert response.status_code == 400

    def test_missing_start_date(self):
        """Test API returns error when start_date is missing."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"end_date": "2025-01-31"}
        )
        assert response.status_code == 400

    def test_missing_end_date(self):
        """Test API returns error when end_date is missing."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-01"}
        )
        assert response.status_code == 400

    def test_end_before_start(self):
        """Test API returns error when end_date is before start_date."""
        response = requests.get(
            f"{BASE_URL}/prices/average",
            params={"start_date": "2025-01-31", "end_date": "2025-01-01"}
        )
        assert response.status_code == 400
