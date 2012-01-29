from jinja2 import Environment
from django.test import TestCase


class TestLoadExtension(TestCase):

    def test_load(self):
        from django_cofingo.extensions import LoadExtension
        env = Environment(extensions=[LoadExtension])

        # the load tag is a no-op
        self.assertEqual(env.from_string('a{% load %}b').render(), 'ab')
        self.assertEqual(
            env.from_string('a{% load news.photos %}b').render(), 'ab')
        self.assertEqual(
            env.from_string('a{% load "news.photos" %}b').render(), 'ab')

        # [bug] invalid code was generated under certain circumstances
        self.assertEqual(
            env.from_string('{% set x=1 %}{% load "news.photos" %}').render(),
            '')


class TestSpacelessExtension(TestCase):

    def test_spaceless(self):
        from django_cofingo.extensions import SpacelessExtension
        env = Environment(extensions=[SpacelessExtension])

        result = env.from_string("""{% spaceless %}
                <p>
                    <a href="foo/">Foo</a>
                </p>
            {% endspaceless %}""").render()
        expected = '<p><a href="foo/">Foo</a></p>'
        self.assertEqual(result, expected)

    def test_spaceless_strong(self):
        from django_cofingo.extensions import SpacelessExtension
        env = Environment(extensions=[SpacelessExtension])

        result = env.from_string("""{% spaceless %}
                <strong>
                    Hello
                </strong>
            {% endspaceless %}""").render()
        expected = u'<strong>\n                    Hello' \
                    '\n                </strong>'
        self.assertEqual(result, expected)


class TestUrlExtension(TestCase):
    def setUp(self):
        from django_cofingo.extensions import URLExtension

        self.env = Environment(extensions=[URLExtension])

    def _from_string(self, source):
        from django_cofingo import Template
        return self.env.from_string(source, template_class=Template)

    def test_url(self):
        from jinja2.exceptions import TemplateSyntaxError
        from django.core.urlresolvers import NoReverseMatch

        for template, context, expected_result in (
            # various ways to specify the view
            ('{% url urls_app.views.index %}', {}, '/url_test/'),
            ('{% url apps.urls_app.views.index %}', {}, '/url_test/'),
            ('{% url "apps.urls_app.views.index" %}', {}, '/url_test/'),
            ('{% url "apps.urls_app.views.indexXX"[:-2] %}', {}, '/url_test/'),
            ('{% url the-index-view %}', {}, '/url_test/'),

            # various ways to specify the arguments
            ('{% url urls_app.views.sum 1,2 %}', {}, '/url_test/sum/1,2'),
            ('{% url urls_app.views.sum left=1,right=2 %}', {},
             '/url_test/sum/1,2'),
            ('{% url urls_app.views.sum l,2 %}', {'l': 1},
             '/url_test/sum/1,2'),
            ('{% url urls_app.views.sum left=l,right=2 %}', {'l': 1},
             '/url_test/sum/1,2'),

            # full expressive syntax
            ('{% url urls_app.views.sum left=2*3,right=z()|length %}',
                    {'z': lambda: 'u'}, '/url_test/sum/6,1'),

            # regression: string view followed by a string argument works
            ('{% url "urls_app.views.sum" "1","2" %}', {},
             '/url_test/sum/1,2'),

            # failures
            ('{% url %}', {}, TemplateSyntaxError),
            ('{% url 1,2,3 %}', {}, TemplateSyntaxError),
            ('{% url inexistant-view %}', {}, NoReverseMatch),

            # ValueError, not TemplateSyntaxError:
            # We actually support parsing a mixture of positional and keyword
            # arguments, but reverse() doesn't handle them.
            ('{% url urls_app.views.sum left=1,2 %}', {'l': 1}, ValueError),

            # as-syntax
            ('{% url urls_app.views.index as url %}', {}, ''),
            ('{% url urls_app.views.index as url %}{{url}}', {}, '/url_test/'),
            ('{% url inexistent as url %}{{ url }}', {}, ''),    # no exception
        ):
            try:
                actual_result = self._from_string(template).render(context)
            except Exception, e:
                self.assertEqual(type(e), expected_result)
            else:
                self.assertEqual(actual_result, expected_result)

    def test_url_current_app(self):
        """Test that the url can deal with the current_app context setting."""
        from django.template import RequestContext
        from django.http import HttpRequest

        template = self._from_string('{% url testapp:the-index-view %}')
        result = template.render(RequestContext(HttpRequest()))
        self.assertEqual(result, '/app/one/')

        result = template.render(
            RequestContext(HttpRequest(), current_app='two'))
        self.assertEqual(result, '/app/two/')


class TestWithExtension(TestCase):
    def test_with(self):
        from django_cofingo.extensions import WithExtension
        env = Environment(extensions=[WithExtension])

        template = env.from_string(
            '{{ x }}{% with y as x %}{{ x }}{% endwith %}{{ x }}')
        result = template.render({'x': 'x', 'y': 'y'})
        self.assertEqual(result, 'xyx')


class TestCacheExtension(TestCase):
    def test_cache(self):
        from django_cofingo.extensions import CacheExtension
        env = Environment(extensions=[CacheExtension])

        x = 0
        result = env.from_string(
            '{%cache 500 "ab"%}{{x}}{%endcache%}').render({'x': x})
        self.assertEqual(result, '0')

        # cache is used; Jinja2 expressions work
        x += 1
        result = env.from_string(
            '{%cache 50*10 "a"+"b"%}{{x}}{%endcache%}').render({'x': x})
        self.assertEqual(result, '0')

        # vary-arguments can be used
        x += 1
        result = env.from_string(
            '{%cache 50*10 "ab" x "foo"%}{{x}}{%endcache%}').render({'x': x})
        self.assertEqual(result, '2')

        x += 1
        result = env.from_string(
            '{%cache 50*10 "ab" x "foo"%}{{x}}{%endcache%}').render({'x': x})
        self.assertEqual(result, '3')
