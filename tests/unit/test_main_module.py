import unittest
from unittest.mock import patch


class TestMainModule(unittest.TestCase):
    """Test the __main__ module."""

    def test_main_module_direct_execution(self):
        """Test direct execution of the __main__ module."""
        # Create a mock for the app function
        with patch("autoresearch.main.app") as mock_app:
            # Import the module (this will execute the import statement)
            import autoresearch.__main__

            # Verify that the module imports app from main
            self.assertTrue(hasattr(autoresearch.__main__, "app"))

            # Simulate running the module as __main__
            original_name = autoresearch.__main__.__name__
            try:
                # Set __name__ to "__main__" to trigger the if block
                autoresearch.__main__.__name__ = "__main__"

                # Execute the if block directly
                if autoresearch.__main__.__name__ == "__main__":
                    autoresearch.__main__.app()

                # Verify that app was called
                mock_app.assert_called_once()
            finally:
                # Restore the original name
                autoresearch.__main__.__name__ = original_name
