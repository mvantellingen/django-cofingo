from jinja2 import Environment
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase


class TestEnvironment(TestCase):

    def test_getattr(self):
        from django_cofingo import env

        class Foo(object):
            @property
            def item(self):
                raise ObjectDoesNotExist()

        tmpl = env.from_string('{{ foo.item }}', {'foo': Foo()})
        self.assertEqual(tmpl.render(), '')

    def test_getattr(self):
        from django_cofingo import env

        class Foo(object):
            def __getitem__(self, key):
                raise ObjectDoesNotExist()

        tmpl = env.from_string("{{ foo['item'] }}", {'foo': Foo()})
        self.assertEqual(tmpl.render(), '')
