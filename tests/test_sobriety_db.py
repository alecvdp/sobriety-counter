"""Tests for the SQLite database layer."""
import os
import sys
import tempfile
import json
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sobriety_db as db


class TestDatabase(unittest.TestCase):
    """Test database operations with a temporary DB file."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = Path(self.tmp.name)
        self._orig_db = db.DB_FILE
        db.DB_FILE = self.db_path
        self.conn = db.get_connection()

    def tearDown(self):
        self.conn.close()
        db.DB_FILE = self._orig_db
        if self.db_path.exists():
            os.unlink(self.db_path)

    # --- Trackers ---

    def test_add_and_get_tracker(self):
        tid = db.add_tracker(self.conn, "Test", "Alcohol", date(2024, 1, 1))
        tracker = db.get_tracker(self.conn, tid)
        self.assertEqual(tracker['name'], "Test")
        self.assertEqual(tracker['category'], "Alcohol")
        self.assertEqual(tracker['start_date'], "2024-01-01")

    def test_get_trackers(self):
        db.add_tracker(self.conn, "A", "Alcohol", date(2024, 1, 1))
        db.add_tracker(self.conn, "B", "Smoking", date(2024, 6, 1))
        trackers = db.get_trackers(self.conn)
        self.assertEqual(len(trackers), 2)

    def test_update_tracker(self):
        tid = db.add_tracker(self.conn, "Old", "Alcohol", date(2024, 1, 1))
        db.update_tracker(self.conn, tid, name="New", start_date=date(2024, 6, 1))
        tracker = db.get_tracker(self.conn, tid)
        self.assertEqual(tracker['name'], "New")
        self.assertEqual(tracker['start_date'], "2024-06-01")

    def test_delete_tracker(self):
        tid = db.add_tracker(self.conn, "Gone", "Custom", date(2024, 1, 1))
        db.delete_tracker(self.conn, tid)
        self.assertIsNone(db.get_tracker(self.conn, tid))

    def test_delete_cascade_journal(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.add_journal_entry(self.conn, tid, "2024-06-01", 3, "hello")
        db.delete_tracker(self.conn, tid)
        entries = db.get_journal_entries(self.conn, tid)
        self.assertEqual(len(entries), 0)

    def test_delete_cascade_milestones(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.check_new_milestones(self.conn, tid, 10)
        db.delete_tracker(self.conn, tid)
        milestones = db.get_achieved_milestones(self.conn, tid)
        self.assertEqual(len(milestones), 0)

    # --- Journal ---

    def test_add_and_get_journal_entry(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.add_journal_entry(self.conn, tid, "2024-06-15", 4, "Feeling great!")
        entry = db.get_journal_entry(self.conn, tid, "2024-06-15")
        self.assertIsNotNone(entry)
        self.assertEqual(entry['mood'], 4)
        self.assertEqual(entry['content'], "Feeling great!")

    def test_journal_upsert(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.add_journal_entry(self.conn, tid, "2024-06-15", 3, "OK")
        db.add_journal_entry(self.conn, tid, "2024-06-15", 5, "Actually great!")
        entry = db.get_journal_entry(self.conn, tid, "2024-06-15")
        self.assertEqual(entry['mood'], 5)
        self.assertEqual(entry['content'], "Actually great!")

    def test_journal_entries_ordering(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.add_journal_entry(self.conn, tid, "2024-06-10", 3, "A")
        db.add_journal_entry(self.conn, tid, "2024-06-15", 4, "B")
        db.add_journal_entry(self.conn, tid, "2024-06-12", 2, "C")
        entries = db.get_journal_entries(self.conn, tid)
        dates = [e['entry_date'] for e in entries]
        self.assertEqual(dates, ["2024-06-15", "2024-06-12", "2024-06-10"])

    def test_journal_accepts_date_objects(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.add_journal_entry(self.conn, tid, date(2024, 7, 1), 3, "date obj")
        entry = db.get_journal_entry(self.conn, tid, date(2024, 7, 1))
        self.assertIsNotNone(entry)

    # --- Milestones ---

    def test_check_new_milestones(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        new = db.check_new_milestones(self.conn, tid, 8)
        days_reached = [d for d, _, _ in new]
        self.assertIn(1, days_reached)
        self.assertIn(3, days_reached)
        self.assertIn(7, days_reached)
        self.assertNotIn(14, days_reached)

    def test_milestones_not_retriggered(self):
        tid = db.add_tracker(self.conn, "T", "Custom", date(2024, 1, 1))
        db.check_new_milestones(self.conn, tid, 8)
        new = db.check_new_milestones(self.conn, tid, 8)
        self.assertEqual(len(new), 0)

    def test_get_next_milestone(self):
        nxt = db.get_next_milestone(5)
        self.assertEqual(nxt[0], 7)
        self.assertEqual(nxt[1], "One Week")

    def test_get_next_milestone_all_done(self):
        nxt = db.get_next_milestone(9999)
        self.assertIsNone(nxt)

    # --- Settings ---

    def test_settings(self):
        db.set_setting(self.conn, "theme", "ocean")
        self.assertEqual(db.get_setting(self.conn, "theme"), "ocean")

    def test_settings_default(self):
        self.assertEqual(db.get_setting(self.conn, "missing", "fallback"), "fallback")

    def test_settings_upsert(self):
        db.set_setting(self.conn, "key", "a")
        db.set_setting(self.conn, "key", "b")
        self.assertEqual(db.get_setting(self.conn, "key"), "b")

    def test_get_all_settings(self):
        db.set_setting(self.conn, "a", "1")
        db.set_setting(self.conn, "b", "2")
        settings = db.get_all_settings(self.conn)
        self.assertEqual(settings, {"a": "1", "b": "2"})

    # --- Migration ---

    def test_migrate_from_json(self):
        json_path = self.db_path.parent / ".sobriety_test_migrate.json"
        try:
            with open(json_path, 'w') as f:
                json.dump({"start_date": "2023-06-15"}, f)
            with patch.object(db, 'LEGACY_JSON', json_path):
                db.migrate_from_json()
            trackers = db.get_trackers(self.conn)
            self.assertEqual(len(trackers), 1)
            self.assertEqual(trackers[0]['start_date'], "2023-06-15")
            self.assertEqual(trackers[0]['name'], "My Sobriety")
        finally:
            if json_path.exists():
                os.unlink(json_path)

    def test_migrate_skips_if_trackers_exist(self):
        db.add_tracker(self.conn, "Existing", "Custom", date(2024, 1, 1))
        json_path = self.db_path.parent / ".sobriety_test_migrate2.json"
        try:
            with open(json_path, 'w') as f:
                json.dump({"start_date": "2020-01-01"}, f)
            with patch.object(db, 'LEGACY_JSON', json_path):
                db.migrate_from_json()
            trackers = db.get_trackers(self.conn)
            self.assertEqual(len(trackers), 1)
            self.assertEqual(trackers[0]['name'], "Existing")
        finally:
            if json_path.exists():
                os.unlink(json_path)


if __name__ == "__main__":
    unittest.main()
