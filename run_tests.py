import unittest
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test modules
from tests.test_oauth import TestOAuth
from tests.test_templates import TestTemplates
from tests.test_mail_merge import TestMailMerge

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestOAuth))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTemplates))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMailMerge))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(not result.wasSuccessful()) 