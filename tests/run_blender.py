"""Run real Blender integration tests in a disposable factory scene."""
import sys
import unittest
from pathlib import Path

folder = Path(__file__).resolve().parent
sys.path.insert(0, str(folder))
result = unittest.TextTestRunner(verbosity=2).run(
    unittest.defaultTestLoader.discover(str(folder), pattern='test_blender.py'))
if not result.wasSuccessful():
    raise RuntimeError('Blender integration tests failed')
