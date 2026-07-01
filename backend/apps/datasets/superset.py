"""
Superset API client for headless integration.
Used to register datasets, generate guest tokens, and query chart data.
"""

import requests
from django.conf import settings


class SupersetClient:
    """Communicates with Superset REST API for dataset management and querying."""

    def __init__(self):
        self.base_url = settings.SUPERSET_API_URL
        self.session = requests.Session()
        self._access_token = None

    def _get_access_token(self) -> str:
        """Authenticate with Superset and get an access token."""
        if self._access_token:
            return self._access_token

        response = self.session.post(
            f"{self.base_url}/security/login",
            json={
                "username": settings.SUPERSET_USERNAME,
                "password": settings.SUPERSET_PASSWORD,
                "provider": "db",
            },
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self._access_token}"})
        return self._access_token

    def _ensure_auth(self):
        """Make sure we have a valid token."""
        self._get_access_token()

    def register_database(self, name: str, db_uri: str) -> int:
        """Register a database connection in Superset."""
        self._ensure_auth()
        response = self.session.post(
            f"{self.base_url}/database/",
            json={
                "database_name": name,
                "sqlalchemy_uri": db_uri,
                "expose_in_sqllab": True,
                "allow_ctas": True,
                "allow_cvas": True,
                "allow_dml": True,
                "allow_run_async": True,
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def register_dataset(self, database_id: int, table_name: str, schema: str = "public") -> int:
        """Register a table as a dataset in Superset."""
        self._ensure_auth()
        response = self.session.post(
            f"{self.base_url}/dataset/",
            json={
                "database": database_id,
                "table_name": table_name,
                "schema": schema,
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_datasets(self) -> list:
        """List all datasets in Superset."""
        self._ensure_auth()
        response = self.session.get(f"{self.base_url}/dataset/")
        response.raise_for_status()
        return response.json().get("result", [])

    def generate_guest_token(
        self,
        user_role: str,
        datasets: list[int],
        rls_filters: list[dict] | None = None,
    ) -> str:
        """
        Generate a guest token with row-level security filters.
        The RLS filters ensure users only see data for their role.
        """
        self._ensure_auth()

        rls_clauses = []
        if rls_filters:
            for f in rls_filters:
                rls_clauses.append({
                    "clause": f"{f['column']} = '{f['value']}'",
                })

        response = self.session.post(
            f"{self.base_url}/security/guest_token/",
            json={
                "user": {"username": "nexivo_guest", "first_name": "Nexivo", "last_name": "Guest"},
                "resources": [{"type": "dashboard", "id": "all"}],
                "rls": rls_clauses,
            },
        )
        response.raise_for_status()
        return response.json()["token"]

    def sync_rls(self, dataset_id: int, rls_filters: list[dict]) -> None:
        """
        Sync row-level security (RLS) rules for a dataset in Superset.
        Each rule: {"clause": "column = 'value'"}
        """
        self._ensure_auth()
        response = self.session.put(
            f"{self.base_url}/dataset/{dataset_id}/",
            json={
                "sqlalchemy_uri": None,  # Don't touch the connection
                "rls": rls_filters,
            },
        )
        response.raise_for_status()


# Singleton instance
superset_client = SupersetClient()
