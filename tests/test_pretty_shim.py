import unittest
import sys
from unittest.mock import patch, MagicMock


class PrettyShimImportTest(unittest.TestCase):
    """Test that pretty_shim handles missing pretty_j1939 gracefully."""

    def test_import_without_pretty_j1939(self):
        """pretty_shim should import without error even if pretty_j1939 is not installed."""
        # Remove any cached imports
        modules_to_remove = [
            k for k in sys.modules
            if k.startswith('pretty_j1939') or k == 'bitstring'
            or k.startswith('truckdevil.libs.pretty_shim')
            or k.startswith('libs.pretty_shim')
        ]
        saved = {}
        for m in modules_to_remove:
            saved[m] = sys.modules.pop(m)

        # Simulate missing pretty_j1939 and bitstring
        with patch.dict(sys.modules, {'pretty_j1939': None, 'bitstring': None,
                                       'pretty_j1939.describe': None,
                                       'pretty_j1939.render': None,
                                       'pretty_j1939.__main__': None}):
            # Force reimport
            if 'truckdevil.libs.pretty_shim' in sys.modules:
                del sys.modules['truckdevil.libs.pretty_shim']

            try:
                from truckdevil.libs.pretty_shim import PrettyShim, PRETTY_AVAILABLE
                self.assertFalse(PRETTY_AVAILABLE)
            except ImportError:
                self.fail("pretty_shim should not raise ImportError when pretty_j1939 is not installed")
            finally:
                # Restore saved modules
                sys.modules.update(saved)

    def test_pretty_available_flag(self):
        """PRETTY_AVAILABLE should reflect whether pretty_j1939 is importable."""
        from truckdevil.libs.pretty_shim import PRETTY_AVAILABLE
        # We don't have pretty_j1939 installed in test env, so it should be False
        self.assertIsInstance(PRETTY_AVAILABLE, bool)

    def test_no_unused_json_import(self):
        """pretty_shim.py should not import json (it was removed as unused)."""
        import inspect
        from truckdevil.libs import pretty_shim
        source = inspect.getsource(pretty_shim)
        # json should not be imported at the top level
        lines = source.split('\n')
        top_level_json_imports = [
            line for line in lines
            if line.strip().startswith('import json')
        ]
        self.assertEqual(len(top_level_json_imports), 0,
                         "json should not be imported in pretty_shim.py")


class PrettyShimClassTest(unittest.TestCase):
    """Test PrettyShim class behavior when pretty_j1939 is not available."""

    def test_is_available_returns_bool(self):
        from truckdevil.libs.pretty_shim import PrettyShim
        result = PrettyShim.is_available()
        self.assertIsInstance(result, bool)

    def test_get_pretty_output_without_init(self):
        """get_pretty_output should return a message when not initialized."""
        from truckdevil.libs.pretty_shim import PrettyShim
        shim = PrettyShim.__new__(PrettyShim)
        shim.describer = None
        shim.renderer = None
        msg = MagicMock()
        result = shim.get_pretty_output(msg)
        self.assertEqual(result, "pretty_j1939 not initialized or available.")


class J1939ImportsTest(unittest.TestCase):
    """Test that j1939.py does not have unused imports."""

    def test_no_shlex_import_in_j1939(self):
        """j1939.py should not import shlex (it was removed as unused)."""
        import inspect
        # We can't easily import j1939.py due to its dependencies, so read the file
        with open('truckdevil/j1939/j1939.py', 'r') as f:
            source = f.read()
        lines = source.split('\n')
        shlex_imports = [
            line for line in lines
            if line.strip() == 'import shlex'
        ]
        self.assertEqual(len(shlex_imports), 0,
                         "shlex should not be imported in j1939.py")

    def test_pretty_verbose_documented(self):
        """print_messages docstring should document pretty/verbose mutual exclusivity."""
        with open('truckdevil/j1939/j1939.py', 'r') as f:
            source = f.read()
        self.assertIn('Mutually exclusive with verbose', source,
                      "print_messages should document that pretty and verbose are mutually exclusive")


if __name__ == '__main__':
    unittest.main()
