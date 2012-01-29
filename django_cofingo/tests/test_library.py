from django.test import TestCase

from django_cofingo.library import Library


class TestLibrary(TestCase):
    def test_add_filter(self):
        library = Library()

        def func(value):
            return 'filter({})'.format(value)

        library.filter(func)
