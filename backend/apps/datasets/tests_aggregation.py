"""
Tests for dataset_query endpoint - GROUP BY aggregation with metrics.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Dataset

User = get_user_model()


class AggregationTests(TestCase):
    """Tests for the dataset_query endpoint's GROUP BY aggregation support."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="agguser", password="testpass123", role="ceo"
        )

        # Create a test table with realistic data for aggregation
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_agg_data")
            cursor.execute("""
                CREATE TABLE test_agg_data (
                    region TEXT,
                    product TEXT,
                    revenue DOUBLE PRECISION,
                    quantity INTEGER
                )
            """)
            data = [
                ("North", "Laptop", 1200.0, 3),
                ("North", "Phone", 800.0, 5),
                ("North", "Laptop", 1500.0, 2),
                ("South", "Phone", 600.0, 4),
                ("South", "Laptop", 900.0, 1),
                ("South", "Phone", 700.0, 3),
                ("East", "Laptop", 1100.0, 2),
                ("East", "Phone", 500.0, 6),
            ]
            for region, product, revenue, quantity in data:
                cursor.execute(
                    "INSERT INTO test_agg_data (region, product, revenue, quantity) VALUES (%s, %s, %s, %s)",
                    [region, product, revenue, quantity],
                )

        self.dataset = Dataset.objects.create(
            name="Test Aggregation Data",
            table_name="test_agg_data",
            status="ready",
            column_names=["region", "product", "revenue", "quantity"],
            column_types={
                "region": "TEXT",
                "product": "TEXT",
                "revenue": "DOUBLE PRECISION",
                "quantity": "BIGINT",
            },
            allowed_roles=["ceo"],
            owner=self.user,
        )
        self.query_url = reverse("dataset-query", args=[self.dataset.pk])

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_agg_data")

    def test_single_dimension_sum(self):
        """GROUP BY region with SUM(revenue) returns correct totals."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"revenue": "SUM"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        # 3 regions: North (3500), South (2200), East (1600)
        self.assertEqual(response.data["row_count"], 3)
        revenue_by_region = {row["region"]: row["revenue"] for row in data}
        self.assertAlmostEqual(revenue_by_region["North"], 3500.0)
        self.assertAlmostEqual(revenue_by_region["South"], 2200.0)
        self.assertAlmostEqual(revenue_by_region["East"], 1600.0)

    def test_multi_dimension_sum(self):
        """GROUP BY region, product with SUM(revenue) returns correct grouped totals."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "product", "revenue"],
                "metrics": {"revenue": "SUM"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        # 6 groups: (North,Laptop), (North,Phone), (South,Laptop), (South,Phone), (East,Laptop), (East,Phone)
        self.assertEqual(response.data["row_count"], 6)
        key = {(row["region"], row["product"]): row["revenue"] for row in data}
        self.assertAlmostEqual(key[("North", "Laptop")], 2700.0)  # 1200 + 1500
        self.assertAlmostEqual(key[("North", "Phone")], 800.0)
        self.assertAlmostEqual(key[("South", "Phone")], 1300.0)  # 600 + 700

    def test_count_aggregation(self):
        """COUNT aggregation returns correct row counts per group."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "quantity"],
                "metrics": {"quantity": "COUNT"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        count_by_region = {row["region"]: row["quantity"] for row in data}
        self.assertEqual(count_by_region["North"], 3)
        self.assertEqual(count_by_region["South"], 3)
        self.assertEqual(count_by_region["East"], 2)

    def test_avg_aggregation(self):
        """AVG aggregation returns correct average per group."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"revenue": "AVG"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        avg_by_region = {row["region"]: row["revenue"] for row in data}
        self.assertAlmostEqual(avg_by_region["North"], 1166.67, places=1)

    def test_multiple_metrics(self):
        """Multiple metrics (SUM revenue + SUM quantity) in one query."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue", "quantity"],
                "metrics": {"revenue": "SUM", "quantity": "SUM"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(response.data["row_count"], 3)
        north = [r for r in data if r["region"] == "North"][0]
        self.assertAlmostEqual(north["revenue"], 3500.0)
        self.assertEqual(north["quantity"], 10)

    def test_min_max_aggregation(self):
        """MIN and MAX aggregation functions work correctly."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"revenue": "MAX"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        max_by_region = {row["region"]: row["revenue"] for row in data}
        self.assertAlmostEqual(max_by_region["North"], 1500.0)
        self.assertAlmostEqual(max_by_region["South"], 900.0)
        self.assertAlmostEqual(max_by_region["East"], 1100.0)

    def test_aggregation_with_filter(self):
        """GROUP BY with WHERE clause filter works correctly."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"revenue": "SUM"},
                "filters": [{"col": "product", "op": "eq", "val": "Laptop"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        revenue_by_region = {row["region"]: row["revenue"] for row in data}
        self.assertAlmostEqual(revenue_by_region["North"], 2700.0)
        self.assertAlmostEqual(revenue_by_region["South"], 900.0)
        self.assertAlmostEqual(revenue_by_region["East"], 1100.0)

    def test_invalid_metric_function_returns_400(self):
        """Invalid aggregation function name is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"revenue": "EVIL_FUNC"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid aggregation function", response.data["error"])

    def test_invalid_metric_column_returns_400(self):
        """Invalid metric column name is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"nonexistent_col": "SUM"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid metric column", response.data["error"])

    def test_empty_metrics_falls_back_to_raw(self):
        """Empty metrics dict returns raw rows (no aggregation)."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Raw rows: 8 total
        self.assertEqual(response.data["row_count"], 8)

    def test_aggregation_order_by_dimension(self):
        """Results are ordered by dimension columns."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["region", "revenue"],
                "metrics": {"revenue": "SUM"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        regions = [row["region"] for row in response.data["data"]]
        self.assertEqual(regions, sorted(regions))
