from django.test import TestCase
from django.test.client import Client


class TestLoader(TestCase):

    def test_render(self):
        client = Client()
        response = client.get('/fullstack/')

        content = response.content

        self.assertTrue('my-foo-filter' in content)
