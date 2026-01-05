import unittest
import sys
import os

# Adicionar root ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honorarios.utils.updater import GitHubUpdater

class TestUpdater(unittest.TestCase):
    def test_version_compare(self):
        updater = GitHubUpdater("owner", "repo", "1.0.0")
        
        # Testar maior
        self.assertEqual(updater._compare_versions("1.0.1", "1.0.0"), 1)
        self.assertEqual(updater._compare_versions("1.1.0", "1.0.0"), 1)
        self.assertEqual(updater._compare_versions("2.0.0", "1.0.0"), 1)
        
        # Testar menor
        self.assertEqual(updater._compare_versions("0.9.9", "1.0.0"), -1)
        self.assertEqual(updater._compare_versions("1.0.0", "1.0.1"), -1)
        
        # Testar igual
        self.assertEqual(updater._compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(updater._compare_versions("1.0", "1.0.0"), 0) # Padding check

if __name__ == '__main__':
    unittest.main()
