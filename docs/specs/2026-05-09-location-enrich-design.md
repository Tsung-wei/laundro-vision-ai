# Location Enrich API and Integration Design

**Date:** 2026-05-09 **Status:** Approved for Implementation

## Overview

This document specifies the design for the `/locations/enrich` backend API and its integration with the Streamlit
frontend. The goal is to determine if there are competitors within 1000m of a given address, driving the "competitor
knock-out" logic in the UI.

## Architecture & Configuration

We will use an abstraction for the Map Provider to allow swapping between different mapping services.

### 1. Configuration (`pydantic-settings`)

- Create `src/laundro_vision_ai/core/config.py` using `pydantic-settings`.
- Define `MAP_PROVIDER` which defaults to `"OSM"` (OpenStreetMap) but can also be `"MOCK"` (for testing) or `"GOOGLE"`.

### 2. Map Provider Strategy

- Define an abstract base class `MapProvider` in `src/laundro_vision_ai/services/location.py`.
- The interface will have two main responsibilities:
  1. **Geocoding**: Converting an address string into latitude/longitude coordinates.
  2. **Competitor Search (1000m)**: Finding competitor laundromats within a 1000-meter radius to determine the
     `has_competitor_in_1000m` flag.
  3. **Target Audience POI Search (200m)**: Finding convenience stores (CVS), McDonald's, and Starbucks within a
     200-meter radius to populate `cvs_mcd_in_200m` and `has_starbucks` (used to pre-fill Q1 in the UI).
- **Implementations**:
  - `OSMMapProvider`: Uses free OSM APIs (Default).
    - **Geocoding**: `https://nominatim.openstreetmap.org/search` (Requires `User-Agent` header).
    - **Competitor Search (1000m)**: `https://overpass-api.de/api/interpreter` using Overpass QL to query `shop=laundry`
      within 1000m.
    - **Audience POI Search (200m)**: Overpass QL query within 200m for `shop=convenience`, `amenity=fast_food`
      (filtering for McDonald's), and `amenity=cafe` (filtering for Starbucks).
  - `MockMapProvider`: Returns fixed/randomized coordinates and POI data for unit tests and local UI testing.
  - `GoogleMapProvider`: Stubbed out for future implementation. Will require `GOOGLE_MAPS_API_KEY`.
    - **Geocoding**: `https://maps.googleapis.com/maps/api/geocode/json?address=...`
    - **Competitor Search (1000m)**:
      `https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=lat,lng&radius=1000&type=laundry`
    - **Audience POI Search (200m)**: `nearbysearch` with `radius=200` for `type=convenience_store`, and keyword
      searches for McDonald's and Starbucks.
- A factory function `get_map_provider()` will read `config.MAP_PROVIDER` and return the configured instance.

### Provider Interface & Scoring Logic

The abstract base class defines the following interface:

```python
from abc import ABC, abstractmethod

class MapProvider(ABC):
    @abstractmethod
    def geocode(self, address: str) -> tuple[float, float]:
        """Converts an address string into (latitude, longitude)."""
        pass

    @abstractmethod
    def enrich_location(self, lat: float, lng: float) -> dict:
        """Performs POI searches and returns the enrichment data dictionary."""
        pass
```

**Q1 Scoring Logic (Executed in Backend):** The `enrich_location` method or a central service calculates
`recommended_q1_score` (1-5) based on POI data:

- **Score 1:** If `has_starbucks` is `True`, or if `cvs_mcd_in_200m` is empty.
- **Score 5:** If "McDonald's" / "麥當勞" is in `cvs_mcd_in_200m`, OR if `len(cvs_mcd_in_200m) >= 2`.
- **Score 3:** If `len(cvs_mcd_in_200m) == 1`. _(Scores 2 and 4 are reserved for manual consultant overrides)._

## API Endpoints and Schemas

### Schemas (`src/laundro_vision_ai/models/schemas.py`)

- `LocationEnrichRequest`:
  - `address` (str): The full address constructed by the UI.
  - `lat` (Optional[float]): Can be provided if known, otherwise the backend will geocode the address.
  - `lng` (Optional[float]).
- `LocationEnrichResponse`:
  - `has_competitor_in_1000m` (bool)
  - `competitors_data` (list)
  - `cvs_mcd_in_200m` (list[str])
  - `has_starbucks` (bool)
  - `recommended_q1_score` (int): The backend-calculated 1-5 score for Q1 based on the POI data.

### FastAPI Route (`src/laundro_vision_ai/api/main.py`)

- `POST /api/v1/locations/enrich`
- Flow:
  1. Receive `LocationEnrichRequest`.
  2. Instantiate the configured `MapProvider`.
  3. If `lat`/`lng` are missing, call the provider's geocoding method with the `address`.
  4. Call the provider's POI search method.
  5. Return the structured `LocationEnrichResponse`.

## Streamlit Frontend Integration

### Updates in `src/laundro_vision_ai/ui/app.py`

- In `render_init()`:
  - Concatenate the selected `city`, `district`, and `address` text input into a single full address string.
  - When the "搜尋周邊" (Search Nearby) button is clicked, make an HTTP POST request to `/api/v1/locations/enrich` with
    the address.
  - Parse the JSON response.
  - Set `st.session_state.has_competitor = response["has_competitor_in_1000m"]`.
  - Set `st.session_state.recommended_q1_score = response["recommended_q1_score"]`.
  - The existing state machine logic will automatically route the user to either `COMPETITOR_EVAL` or `TARGET_EVAL`
    based on this flag.
- In `render_target_eval()`:
  - Refactor the hardcoded `q1 = 5` into an actual `st.radio` component so the consultant can override it.
  - Calculate the default index: `default_index = st.session_state.get("recommended_q1_score", 5) - 1`.
  - Render: `q1 = st.radio("Q1. CVS / 麥當勞", [1, 2, 3, 4, 5], index=default_index, horizontal=True)`.
  - Provide UI context (e.g., via `st.info(f"API 探測結果: {cvs_list}")`) showing the raw POI data so the consultant
    knows why the score was pre-filled.
  - Handle potential errors (e.g., API timeout or geocoding failure) gracefully by showing an `st.error` message.
