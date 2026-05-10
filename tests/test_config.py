import os

from laundro_vision_ai.core.config import get_settings


def test_config_defaults():
    settings = get_settings()
    assert settings.MAP_PROVIDER == "OSM"


def test_config_override():
    os.environ["MAP_PROVIDER"] = "MOCK"  # Set for this test to explicitly override
    settings = get_settings()
    assert settings.MAP_PROVIDER == "MOCK"
