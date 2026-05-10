import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from laundro_vision_ai.api.main import app

client = TestClient(app)


def test_evaluate_competitor_endpoint():
    response = client.post(
        "/api/v1/assessments/evaluate-competitor",
        json={
            "q2_residential": 4,
            "q3_visibility": 4,
            "q4_signage": 4,
            "q5_motorcycle": 4,
            "q7_machine_status": 4,
            "q8_cleanliness": 4,
        },
    )
    assert response.status_code == 200
    assert response.json()["knock_out"] is True


def test_calculate_score_endpoint():
    response = client.post(
        "/api/v1/assessments/calculate-score",
        json={
            "has_competitor": False,
            "q1_cvs": 5,
            "q2_residential": 5,
            "q3_visibility": 5,
            "q4_signage": 5,
            "q5_motorcycle": 5,
        },
    )
    assert response.status_code == 200
    assert response.json()["total_score"] == 5.0


def test_enrich_location_endpoint():
    # Using MOCK provider for consistency and avoiding external calls in unit tests
    os.environ["MAP_PROVIDER"] = "MOCK"
    from laundro_vision_ai.core.config import get_settings

    get_settings.cache_clear()

    response = client.post("/api/v1/locations/enrich", json={"address": "Taipei"})
    assert response.status_code == 200
    data = response.json()
    assert "has_competitor_in_1000m" in data
    assert "recommended_q1_score" in data
    assert data["recommended_q1_score"] in [1, 2, 3, 4, 5]


def test_enrich_location_endpoint_empty_address_geocoding_fails():
    # No explicit MAP_PROVIDER env setting needed, autouse fixture handles it.
    os.environ["MAP_PROVIDER"] = "MOCK"  # Ensure mock provider is used
    from laundro_vision_ai.core.config import get_settings

    get_settings.cache_clear()

    # Mock the geocode method to raise ValueError when address is an empty string or invalid
    with patch("laundro_vision_ai.services.location.MockMapProvider.geocode") as mock_geocode:
        mock_geocode.side_effect = ValueError("Address cannot be empty or invalid")
        response = client.post("/api/v1/locations/enrich", json={"address": ""})
        assert response.status_code == 400
        assert response.json()["detail"] == "Address cannot be empty or invalid"


def test_enrich_location_endpoint_geocode_fails():
    os.environ["MAP_PROVIDER"] = "MOCK"
    from laundro_vision_ai.core.config import get_settings

    get_settings.cache_clear()

    with patch("laundro_vision_ai.services.location.MockMapProvider.geocode") as mock_geocode:
        mock_geocode.side_effect = ValueError("Geocoding failed")
        response = client.post("/api/v1/locations/enrich", json={"address": "Invalid Address"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Geocoding failed"


def test_enrich_location_endpoint_poi_search_fails():
    os.environ["MAP_PROVIDER"] = "MOCK"
    from laundro_vision_ai.core.config import get_settings

    get_settings.cache_clear()

    with patch("laundro_vision_ai.services.location.MockMapProvider.enrich_location") as mock_enrich:
        mock_enrich.side_effect = Exception("POI search error")
        response = client.post("/api/v1/locations/enrich", json={"address": "Taipei"})
        assert response.status_code == 500
        assert response.json()["detail"] == "POI search failed: POI search error"


def test_enrich_location_endpoint_with_lat_lng():
    os.environ["MAP_PROVIDER"] = "MOCK"
    from laundro_vision_ai.core.config import get_settings

    get_settings.cache_clear()

    mock_enrich_return = {
        "has_competitor_in_1000m": True,
        "competitors_data": ["Mock Laundry"],
        "cvs_mcd_in_200m": ["7-11"],
        "has_starbucks": False,
    }
    with patch(
        "laundro_vision_ai.services.location.MockMapProvider.enrich_location", return_value=mock_enrich_return
    ) as mock_enrich:
        response = client.post(
            "/api/v1/locations/enrich",
            json={
                "address": "Dummy Address",  # Required by Pydantic schema
                "lat": 25.0,
                "lng": 121.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_competitor_in_1000m"] is True
        assert data["recommended_q1_score"] == 3  # Based on cvs_mcd_in_200m having one item
        mock_enrich.assert_called_once_with(25.0, 121.0)
