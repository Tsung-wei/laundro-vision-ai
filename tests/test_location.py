from laundro_vision_ai.services.location import MockMapProvider


def test_mock_provider_geocode():
    provider = MockMapProvider()
    lat, lng = provider.geocode("Taipei")
    assert isinstance(lat, float)
    assert isinstance(lng, float)


def test_mock_provider_enrich():
    provider = MockMapProvider()
    result = provider.enrich_location(25.0, 121.0)
    assert "has_competitor_in_1000m" in result
    assert result["has_starbucks"] is False
