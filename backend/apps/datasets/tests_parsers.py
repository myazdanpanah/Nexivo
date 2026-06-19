"""
Tests for the datasets parsers module.
Covers: parse_excel_file, generate_table_name, create_table_from_dataframe, drop_table.
"""

import os
import tempfile

import pandas as pd
from django.db import connection
from django.test import TestCase

from .parsers import (
    create_table_from_dataframe,
    drop_table,
    generate_table_name,
    parse_excel_file,
)


class ParseExcelFileTests(TestCase):
    """Tests for parse_excel_file function."""

    def test_parse_csv_file(self):
        """CSV file is parsed correctly with column cleaning."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Full Name,Amount-USD,Date\n")
            f.write("Alice,100.5,2024-01-15\n")
            f.write("Bob,200.0,2024-02-20\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)

            self.assertEqual(len(df), 2)
            # Column names should be cleaned: lowercase, spaces->underscores, hyphens->underscores
            self.assertEqual(col_names, ["full_name", "amount_usd", "date"])
            self.assertIn("full_name", col_types)
            self.assertIn("amount_usd", col_types)
        finally:
            os.unlink(tmp_path)

    def test_parse_xlsx_file(self):
        """Excel .xlsx file is parsed correctly."""
        df = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [95, 87]})
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name
        df.to_excel(tmp_path, index=False)

        try:
            parsed_df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(parsed_df), 2)
            self.assertIn("name", col_names)
            self.assertIn("score", col_names)
            self.assertEqual(col_types["score"], "BIGINT")
        finally:
            os.unlink(tmp_path)

    def test_parse_csv_with_whitespace_columns(self):
        """Column names with whitespace are cleaned properly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(" First Name , Last Name \n")
            f.write("Alice,Smith\n")
            tmp_path = f.name

        try:
            _, col_names, _ = parse_excel_file(tmp_path)
            self.assertEqual(col_names, ["first_name", "last_name"])
        finally:
            os.unlink(tmp_path)

    def test_parse_unsupported_format_raises_error(self):
        """Unsupported file format raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            with self.assertRaises(ValueError) as ctx:
                parse_excel_file(tmp_path)
            self.assertIn("Unsupported file format", str(ctx.exception))
        finally:
            os.unlink(tmp_path)

    def test_parse_empty_csv(self):
        """Empty CSV with only headers returns empty DataFrame."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2,col3\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 0)
            self.assertEqual(col_names, ["col1", "col2", "col3"])
        finally:
            os.unlink(tmp_path)


class GenerateTableNameTests(TestCase):
    """Tests for generate_table_name function."""

    def test_basic_name(self):
        """Basic name generates a valid table name."""
        result = generate_table_name("Sales Data")
        self.assertTrue(result.startswith("nexivo_data_sales_data_"))
        self.assertTrue(len(result) > len("nexivo_data_sales_data_"))

    def test_special_characters_removed(self):
        """Special characters are removed from table name."""
        result = generate_table_name("Sales! @Data# 2024")
        # Only alphanumeric and underscores allowed after cleaning
        prefix = result.rsplit("_", 1)[0]  # Remove unique suffix
        self.assertEqual(prefix, "nexivo_data_sales_data_2024")

    def test_unique_suffix(self):
        """Each call produces a different unique suffix."""
        names = {generate_table_name("test") for _ in range(100)}
        self.assertEqual(len(names), 100)  # All should be unique

    def test_empty_name(self):
        """Empty name generates a valid (minimal) table name."""
        result = generate_table_name("")
        self.assertTrue(result.startswith("nexivo_data_"))

    def test_underscores_preserved(self):
        """Existing underscores in the name are preserved."""
        result = generate_table_name("my_data_set")
        self.assertIn("my_data_set", result)

    def test_only_alphanumeric_and_underscores(self):
        """Generated name contains only alphanumeric chars and underscores."""
        result = generate_table_name("Test! @#$% Data")
        import re
        self.assertTrue(re.match(r"^[a-zA-Z0-9_]+$", result))


class CreateTableFromDataframeTests(TestCase):
    """Tests for create_table_from_dataframe function."""

    def setUp(self):
        self.table_name = f"test_parser_{generate_table_name('unit_test').rsplit('_', 1)[1]}"

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS "{self.table_name}"')

    def test_creates_table_and_inserts_data(self):
        """Table is created and data is inserted correctly."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "amount": [100.5, 200.0],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{self.table_name}" ORDER BY name')
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

        self.assertEqual(len(rows), 2)
        self.assertIn("name", col_names)
        self.assertIn("amount", col_names)
        # Data integrity check
        names = {row[0] for row in rows}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_empty_dataframe_creates_empty_table(self):
        """Empty DataFrame creates table with no rows."""
        df = pd.DataFrame({"col1": pd.Series([], dtype="int64"), "col2": pd.Series([], dtype="object")})
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{self.table_name}"')
            count = cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_postgresql_types_correct(self):
        """Column types in PostgreSQL match expected types."""
        df = pd.DataFrame({
            "int_col": [1, 2],
            "float_col": [1.5, 2.5],
            "text_col": ["hello", "world"],
            "bool_col": [True, False],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = %s ORDER BY ordinal_position",
                [self.table_name],
            )
            columns = {row[0]: row[1] for row in cursor.fetchall()}

        self.assertEqual(columns["int_col"], "bigint")
        self.assertEqual(columns["float_col"], "double precision")
        self.assertEqual(columns["text_col"], "text")
        self.assertEqual(columns["bool_col"], "boolean")

    def test_duplicate_create_does_not_fail(self):
        """Creating the same table twice does not raise an error."""
        df = pd.DataFrame({"id": [1], "value": ["test"]})
        create_table_from_dataframe(df, self.table_name)
        create_table_from_dataframe(df, self.table_name)  # Should not raise

    def test_special_characters_in_data(self):
        """Data with special characters is inserted correctly."""
        df = pd.DataFrame({
            "text": ["hello 'world'", 'test "quotes"', "line\nbreak"],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT text FROM "{self.table_name}"')
            rows = cursor.fetchall()
        self.assertEqual(len(rows), 3)


class DropTableTests(TestCase):
    """Tests for drop_table function."""

    def test_drop_existing_table(self):
        """Dropping an existing table succeeds."""
        table = "test_drop_existing"
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE TABLE "{table}" (id INT)')
        drop_table(table)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
                [table],
            )
            self.assertFalse(cursor.fetchone()[0])

    def test_drop_nonexistent_table_no_error(self):
        """Dropping a non-existent table does not raise an error."""
        drop_table("table_that_does_not_exist_xyz123")  # Should not raise

    def test_invalid_table_name_raises_error(self):
        """Table name with special characters raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            drop_table("invalid; DROP TABLE users; --")
        self.assertIn("Invalid table name", str(ctx.exception))

    def test_table_name_with_spaces_raises_error(self):
        """Table name with spaces raises ValueError."""
        with self.assertRaises(ValueError):
            drop_table("my table name")

    def test_only_alphanumeric_and_underscores_accepted(self):
        """Valid table names with alphanumeric and underscores work."""
        table = "test_valid_table_name_123"
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE TABLE "{table}" (id INT)')
        drop_table(table)  # Should not raise
