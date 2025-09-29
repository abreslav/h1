import pytest
from django.test import TestCase
from django_app.models import Demo


class TestDemo(TestCase):

    @pytest.mark.timeout(30)
    def test_str(self):
        """
        Test kind: unit_tests
        Original method: Demo.__str__
        """
        # Test __str__ method returns the name field
        demo = Demo(name="Test Demo", description="Test description")
        self.assertEqual(str(demo), "Test Demo")

        # Test with different name
        demo2 = Demo(name="Another Demo", description="Another description")
        self.assertEqual(str(demo2), "Another Demo")

        # Test with empty name
        demo3 = Demo(name="", description="Some description")
        self.assertEqual(str(demo3), "")