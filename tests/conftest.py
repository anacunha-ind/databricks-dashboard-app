"""Pytest configuration and shared fixtures.

Mocks external dependencies (streamlit, psycopg2, databricks-sdk) so the app
modules can be imported without a live Databricks environment.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add app source to path so 'import queries' and 'import charts' work
APP_SRC = Path(__file__).parent.parent / "bundles/dashboard-metrics/src/app"
sys.path.insert(0, str(APP_SRC))

# Mock streamlit before any app module is imported — prevents st.cache_data/
# st.cache_resource from executing at import time.
_st = MagicMock()
_st.cache_data = lambda *_, **__: (lambda f: f)  # passthrough decorator
_st.cache_resource = lambda *_, **__: (lambda f: f)  # passthrough decorator
sys.modules.setdefault("streamlit", _st)

# Mock psycopg2 — replaced per-test with unittest.mock.patch as needed
sys.modules.setdefault("psycopg2", MagicMock())

# Mock Databricks SDK
_sdk = MagicMock()
sys.modules.setdefault("databricks", _sdk)
sys.modules.setdefault("databricks.sdk", _sdk)
sys.modules.setdefault("databricks.sdk.service", MagicMock())
sys.modules.setdefault("databricks.sdk.service.sql", MagicMock())

# Mock altair so chart tests can verify structure without rendering
sys.modules.setdefault("altair", MagicMock())
