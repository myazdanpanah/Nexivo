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

    def test_duplicate_create_is_idempotent(self):
        """Calling create_table_from_dataframe twice produces same data (TRUNCATE makes it idempotent)."""
        df = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})
        create_table_from_dataframe(df, self.table_name)
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{self.table_name}"')
            count = cursor.fetchone()[0]
        # TRUNCATE before insert makes it idempotent — only 2 rows.
        self.assertEqual(count, 2)

    def test_nan_none_inserted_as_null(self):
        """NaN and None values in DataFrame are inserted as NULLs in PostgreSQL."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "score": [100.0, float("nan"), None],
            "note": ["ok", None, float("nan")],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT name, score, note FROM "{self.table_name}" ORDER BY name')
            rows = cursor.fetchall()

        self.assertEqual(len(rows), 3)
        # Bob's score should be NULL (was NaN)
        bob = [r for r in rows if r[0] == "Bob"][0]
        self.assertIsNone(bob[1])
        # Charlie's score should be NULL (was None)
        charlie = [r for r in rows if r[0] == "Charlie"][0]
        self.assertIsNone(charlie[1])
        # Charlie's note should be NULL (was NaN)
        self.assertIsNone(charlie[2])
        # Alice's values should be non-NULL
        alice = [r for r in rows if r[0] == "Alice"][0]
        self.assertIsNotNone(alice[1])
        self.assertIsNotNone(alice[2])

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


class ParseEdgeCaseTests(TestCase):
    """Tests for real-world parser edge cases: mixed types, large files, Unicode/Farsi."""

    def setUp(self):
        self.table_name = f"test_edge_{generate_table_name('edge').rsplit('_', 1)[1]}"

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS "{self.table_name}"')

    def test_mixed_type_csv_columns(self):
        """CSV with columns of mixed types (int, float, string, bool) parses correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("id,name,amount,active\n")
            f.write("1,Alice,100.5,true\n")
            f.write("2,Bob,200,false\n")
            f.write("3,Charlie,0,TRUE\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 3)
            self.assertEqual(col_names, ["id", "name", "amount", "active"])
            # Verify types are correctly inferred
            self.assertEqual(col_types["id"], "BIGINT")
            self.assertEqual(col_types["amount"], "DOUBLE PRECISION")
            self.assertEqual(col_types["name"], "TEXT")
        finally:
            os.unlink(tmp_path)

    def test_mixed_types_inserted_correctly(self):
        """DataFrame with mixed column types is inserted and retrievable from PostgreSQL."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95.5, 87.0, 72.3],
            "passed": [True, True, False],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT id, name, score, passed FROM "{self.table_name}" ORDER BY id')
            rows = cursor.fetchall()

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], (1, "Alice", 95.5, True))
        self.assertEqual(rows[1], (2, "Bob", 87.0, True))
        self.assertEqual(rows[2], (3, "Charlie", 72.3, False))

    def test_large_csv_file(self):
        """Parser handles a CSV file with 1000 rows without error."""
        import csv

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "value"])
            for i in range(1000):
                writer.writerow([i, f"user_{i}", i * 1.5])
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 1000)
            self.assertEqual(col_names, ["id", "name", "value"])
            # Verify data integrity for first and last rows
            self.assertEqual(df.iloc[0]["name"], "user_0")
            self.assertEqual(df.iloc[999]["name"], "user_999")
            self.assertAlmostEqual(df.iloc[500]["value"], 750.0)
        finally:
            os.unlink(tmp_path)

    def test_large_file_inserted_correctly(self):
        """1000-row DataFrame is fully inserted into PostgreSQL."""
        df = pd.DataFrame({
            "id": range(1000),
            "name": [f"user_{i}" for i in range(1000)],
            "value": [i * 1.5 for i in range(1000)],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{self.table_name}"')
            count = cursor.fetchone()[0]
        self.assertEqual(count, 1000)

    def test_unicode_farsi_csv(self):
        """CSV with Farsi/Arabic Unicode characters parses correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("نام,مبلغ,شهر\n")
            f.write("علی,1000000,تهران\n")
            f.write("محمد,2500000,اصفهان\n")
            f.write("فاطمه,750000,شیراز\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 3)
            # Column names should be cleaned but keep Farsi characters
            self.assertIn("نام", col_names)
            self.assertIn("مبلغ", col_names)
            self.assertIn("شهر", col_names)
            # Verify Farsi data is preserved
            self.assertEqual(df.iloc[0]["نام"], "علی")
            self.assertEqual(df.iloc[0]["شهر"], "تهران")
            self.assertEqual(df.iloc[2]["نام"], "فاطمه")
        finally:
            os.unlink(tmp_path)

    def test_unicode_farsi_xlsx(self):
        """Excel file with Farsi/Arabic content parses correctly."""
        df = pd.DataFrame({
            "نام": ["علی", "محمد", "فاطمه"],
            "مبلغ": [1000000, 2500000, 750000],
            "شهر": ["تهران", "اصفهان", "شیراز"],
        })
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name
        df.to_excel(tmp_path, index=False)

        try:
            parsed_df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(parsed_df), 3)
            self.assertIn("نام", col_names)
            self.assertIn("مبلغ", col_names)
            self.assertEqual(parsed_df.iloc[0]["نام"], "علی")
            self.assertEqual(parsed_df.iloc[1]["شهر"], "اصفهان")
        finally:
            os.unlink(tmp_path)

    def test_farsi_data_inserted_into_postgresql(self):
        """Farsi/Arabic data is correctly stored and retrieved from PostgreSQL."""
        df = pd.DataFrame({
            "نام": ["علی", "محمد", "فاطمه"],
            "مبلغ": [1000000, 2500000, 750000],
            "شهر": ["تهران", "اصفهان", "شیراز"],
        })
        create_table_from_dataframe(df, self.table_name)

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT "نام", "مبلغ", "شهر" FROM "{self.table_name}" ORDER BY "مبلغ"')
            rows = cursor.fetchall()

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], ("فاطمه", 750000, "شیراز"))
        self.assertEqual(rows[1], ("علی", 1000000, "تهران"))
        self.assertEqual(rows[2], ("محمد", 2500000, "اصفهان"))

    def test_empty_cells_in_csv(self):
        """CSV with empty cells handles them as NaN/None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("name,amount\n")
            f.write("Alice,100\n")
            f.write(",200\n")
            f.write("Charlie,\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 3)
            # Bob row has empty name
            self.assertTrue(pd.isna(df.at[1, "name"]))
            # Charlie row has empty amount
            self.assertTrue(pd.isna(df.at[2, "amount"]))
        finally:
            os.unlink(tmp_path)

    def test_mixed_types_with_empty_cells_csv(self):
        """CSV with mixed types AND empty cells tests type inference and NaN together."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("id,name,score,active\n")
            f.write("1,Alice,95.5,true\n")
            f.write(",Bob,80,false\n")
            f.write("3,,72.3,TRUE\n")
            f.write("4,Dave,,\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 4)
            # Row 1 (Bob): empty id -> NaN
            self.assertTrue(pd.isna(df.at[1, "id"]))
            # Row 2 (Charlie): empty name -> NaN
            self.assertTrue(pd.isna(df.at[2, "name"]))
            # Row 3 (Dave): empty score and active -> NaN
            self.assertTrue(pd.isna(df.at[3, "score"]))
            self.assertTrue(pd.isna(df.at[3, "active"]))
            # Verify non-empty values are correct
            self.assertEqual(df.at[0, "name"], "Alice")
            self.assertAlmostEqual(df.at[0, "score"], 95.5)
            # Insert into PostgreSQL and verify NULLs
            create_table_from_dataframe(df, self.table_name)
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{self.table_name}" ORDER BY id')
                rows = cursor.fetchall()
                col_names_db = [desc[0] for desc in cursor.description]
            self.assertEqual(len(rows), 4)
            # Find Bob's row (id is NULL)
            bob_row = [r for r in rows if r[col_names_db.index("name")] == "Bob"][0]
            self.assertIsNone(bob_row[col_names_db.index("id")])
        finally:
            os.unlink(tmp_path)

    def test_bilingual_farsi_latin_column_names(self):
        """CSV with mixed Farsi and Latin column names with spaces is cleaned correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("فروش Q1-2024 , نام محصول , Price (USD)\n")
            f.write("1000,لپ تاپ,500\n")
            f.write("2000,گوشی,300\n")
            tmp_path = f.name

        try:
            df, col_names, col_types = parse_excel_file(tmp_path)
            self.assertEqual(len(df), 2)
            # Column names should be cleaned: lowercase, spaces->underscores, hyphens->underscores
            self.assertIn("فروش_q1_2024", col_names)
            self.assertIn("نام_محصول", col_names)
            self.assertIn("price_usd", col_names)
            # Verify data is preserved
            self.assertEqual(df.iloc[0][col_names[0]], 1000)
            self.assertEqual(df.iloc[0][col_names[1]], "لپ تاپ")
            self.assertEqual(df.iloc[1][col_names[2]], 300)
        finally:
            os.unlink(tmp_path)


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
