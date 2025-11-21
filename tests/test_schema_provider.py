import os
import sys
import unittest
from types import SimpleNamespace

from text2sql.schema_provider import SchemaProvider

class TestSchemaProviderMySQL(unittest.TestCase):
    def setUp(self):
        # mock pymysql
        class FakeCursor:
            def __init__(self):
                self._sql = None
                self._params = None
            def execute(self, sql, params=None):
                self._sql = sql
                self._params = params
            def fetchall(self):
                return [("t1", "c1"), ("t1", "c2"), ("t2", "a")]
        class FakeConn:
            def __init__(self):
                self.cursor_obj = FakeCursor()
            def cursor(self):
                return self.cursor_obj
            def close(self):
                pass
        sys.modules['pymysql'] = SimpleNamespace(connect=lambda **kw: FakeConn())
        self.db_url = "mysql://root:pw@localhost:3306/db"
        self.sp = SchemaProvider()

    def test_load_mysql(self):
        schema = self.sp.load(self.db_url, "mysql")
        self.assertIn("t1", schema["tables"]) 
        self.assertIn("t2", schema["tables"]) 
        info_path = os.path.join(os.path.dirname(__file__), "..", "db_info", "db.json")
        self.assertTrue(os.path.exists(os.path.abspath(info_path)))

    def test_string_rules(self):
        cols = [
            {"name": "code", "type": "string", "pattern": r"^[A-Z]{3}\d{2}$"},
            {"name": "desc", "type": "string", "max_length": 3},
            {"name": "opt", "type": "string"},
        ]
        ok1, out1, _ = self.sp._validate_and_normalize_row({"code": "ABC12", "desc": "abcdef", "opt": None}, cols)
        self.assertTrue(ok1)
        self.assertEqual(out1["desc"], "abc")
        bad, _, reason = self.sp._validate_and_normalize_row({"code": "ab12", "desc": "x"}, cols)
        self.assertFalse(bad)
        self.assertIn("pattern", reason)

if __name__ == "__main__":
    unittest.main()