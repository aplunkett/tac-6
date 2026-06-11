"""
Tests for the CSV export endpoints:
- GET  /api/export/table/{table_name}
- POST /api/export/query
"""

import io
import os
import sqlite3

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from server import app

DB_PATH = "db/database.db"
TEST_TABLE = "export_test_users"

client = TestClient(app)


@pytest.fixture
def seeded_db():
    """Seed the application database with a known table and clean it up after."""
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TEST_TABLE}")
    cursor.execute(
        f"""
        CREATE TABLE {TEST_TABLE} (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            note TEXT
        )
        """
    )
    cursor.execute(
        f"INSERT INTO {TEST_TABLE} (name, note) VALUES (?, ?)",
        ("Alice", "hello"),
    )
    # A value containing a comma to verify CSV escaping
    cursor.execute(
        f"INSERT INTO {TEST_TABLE} (name, note) VALUES (?, ?)",
        ("Bob", "a, b, c"),
    )
    conn.commit()
    conn.close()

    yield TEST_TABLE

    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DROP TABLE IF EXISTS {TEST_TABLE}")
    conn.commit()
    conn.close()


class TestExportTable:
    def test_export_table_success(self, seeded_db):
        response = client.get(f"/api/export/table/{seeded_db}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="{seeded_db}.csv"'
        )

        # Parse the CSV body and verify header + rows
        df = pd.read_csv(io.StringIO(response.text))
        assert list(df.columns) == ["id", "name", "note"]
        assert len(df) == 2
        assert "Alice" in df["name"].values
        # Comma-containing value is preserved (CSV escaping handled by pandas)
        assert "a, b, c" in df["note"].values

    def test_export_table_invalid_name(self, seeded_db):
        response = client.get("/api/export/table/users;%20DROP%20TABLE%20users")
        assert response.status_code == 400

    def test_export_table_not_found(self, seeded_db):
        response = client.get("/api/export/table/nonexistent_table_xyz")
        assert response.status_code == 404


class TestExportQuery:
    def test_export_query_success(self, seeded_db):
        response = client.post(
            "/api/export/query",
            json={"sql": f"SELECT name, note FROM {seeded_db} ORDER BY name"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="query_results.csv"'
        )

        df = pd.read_csv(io.StringIO(response.text))
        assert list(df.columns) == ["name", "note"]
        assert len(df) == 2
        assert list(df["name"].values) == ["Alice", "Bob"]

    def test_export_query_dangerous(self, seeded_db):
        response = client.post(
            "/api/export/query",
            json={"sql": f"DROP TABLE {seeded_db}"},
        )
        assert response.status_code == 400

    def test_export_query_empty_results(self, seeded_db):
        response = client.post(
            "/api/export/query",
            json={"sql": f"SELECT id, name FROM {seeded_db} WHERE 1 = 0"},
        )
        # Empty result set should not crash and should contain no data rows
        assert response.status_code == 200
        lines = [line for line in response.text.splitlines() if line.strip()]
        assert len(lines) <= 1  # at most a header row, never data rows
