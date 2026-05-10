import os

import pytest

from laundro_vision_ai.core.config import get_settings


@pytest.fixture(autouse=True)
def manage_map_provider_env():
    # Ensure original state is preserved
    original_map_provider = os.environ.get("MAP_PROVIDER")

    # Clear cache before each test that might alter settings
    get_settings.cache_clear()

    yield  # Run the test

    # Restore original state after test
    if original_map_provider is not None:
        os.environ["MAP_PROVIDER"] = original_map_provider
    else:
        if "MAP_PROVIDER" in os.environ:
            del os.environ["MAP_PROVIDER"]
    get_settings.cache_clear()
