"""Tests for the sobriety_core module."""
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sobriety_db as db
import sobriety_core as core


class TestCalcHelpers(unittest.TestCase):
    """Test calculation helper functions."""

    def test_calc_days(self):
        start = date.today() - timedelta(days=42)
        self.assertEqual(core.calc_days(start), 42)

    def test_calc_days_today(self):
        self.assertEqual(core.calc_days(date.today()), 0)

    def test_calc_breakdown_basic(self):
        bd = core.calc_breakdown(45)
        self.assertEqual(bd['weeks'], 6)
        self.assertEqual(bd['months'], 1)
        self.assertEqual(bd['month_remainder'], 15)
        self.assertEqual(bd['years'], 0)
        self.assertEqual(bd['year_remainder'], 45)

    def test_calc_breakdown_year(self):
        bd = core.calc_breakdown(400)
        self.assertEqual(bd['years'], 1)
        self.assertEqual(bd['year_remainder'], 35)

    def test_calc_breakdown_zero(self):
        bd = core.calc_breakdown(0)
        self.assertEqual(bd['weeks'], 0)
        self.assertEqual(bd['months'], 0)


class TestQuotes(unittest.TestCase):
    """Test quote functionality."""

    def test_local_quote_returns_string(self):
        q = core.get_random_quote(allow_network=False)
        self.assertIsInstance(q, str)
        self.assertTrue(len(q) > 0)

    def test_local_quote_from_list(self):
        q = core.get_random_quote(allow_network=False)
        self.assertIn(q, core.QUOTES)

    def test_network_fallback(self):
        # With network disabled, should always get a local quote
        for _ in range(10):
            q = core.get_random_quote(allow_network=False)
            self.assertIn(q, core.QUOTES)


class TestBackwardCompat(unittest.TestCase):
    """Test backward-compatible load_data/save_data functions."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = Path(self.tmp.name)
        self._orig_db = db.DB_FILE
        db.DB_FILE = self.db_path

    def tearDown(self):
        db.DB_FILE = self._orig_db
        if self.db_path.exists():
            os.unlink(self.db_path)

    def test_save_and_load(self):
        d = date(2024, 3, 15)
        core.save_data(d)
        loaded = core.load_data()
        self.assertEqual(loaded, d)

    def test_load_empty(self):
        result = core.load_data()
        self.assertIsNone(result)

    def test_save_updates_existing(self):
        core.save_data(date(2024, 1, 1))
        core.save_data(date(2024, 6, 15))
        self.assertEqual(core.load_data(), date(2024, 6, 15))
        # Should still have only one tracker
        conn = db.get_connection()
        trackers = db.get_trackers(conn)
        conn.close()
        self.assertEqual(len(trackers), 1)


if __name__ == "__main__":
    unittest.main()
