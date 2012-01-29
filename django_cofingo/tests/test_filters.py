from datetime import datetime, date
from django.test import TestCase


def r(s, context={}):
    from django_cofingo import env
    return env.from_string(s).render(context)


class TestFilters(TestCase):
    def test_django_builtins_available(self):
        """Many filters have not been re-implemented specifically for
        Coffin, but instead the Django version is used through an
        interop-layer.

        Make sure that those are properly made available in Jinja2.
        """
        from django_cofingo import filters
        assert not hasattr(filters, 'get_digit')  # has no port
        assert r('{{ "23475"|get_digit("2") }}') == '7'
        assert r('{{ unknown|get_digit("2") }}') == ''

    def test_jinja2_builtins(self):
        """Ensure that the Jinja2 builtins are available, and take
        precedence over the Django builtins (which we automatically convert
        and install).
        """
        # Django's default filter only accepts one argument.
        assert r('{{ unknown|default("2", True) }}') == '2'

    def test_default(self):
        """We make the Jinja2 default filter behave like Django's without
        arguments, but still support Jinja2 extended syntax.
        """
        assert r('{{ foo|default("default") }}') == 'default'
        assert r('{{ foo|default("default") }}', {'foo': False}) == 'default'
        assert r('{{ foo|default("default", False) }}', {'foo': False}) == 'False'

    def test_pluralize(self):
        assert r('vote{{ 0|pluralize }}') == 'votes'
        assert r('vote{{ 1|pluralize }}') == 'vote'
        assert r('class{{ 2|pluralize("es") }}') == 'classes'
        assert r('cand{{ 0|pluralize("y", "ies") }}') == 'candies'
        assert r('cand{{ 1|pluralize("y", "ies") }}') == 'candy'
        assert r('cand{{ 2|pluralize("y", "ies") }}') == 'candies'
        assert r('vote{{ [1,2,3]|pluralize }}') == 'votes'
        assert r('anonyme{{ 0|pluralize("r", "") }}') == 'anonyme'
        assert r('anonyme{{ 1|pluralize("r", "") }}') == 'anonymer'
        assert r('vote{{ 1|pluralize }}') == 'vote'

        with self.assertRaises(TypeError):
            r('vote{{ x|pluralize }}', {'x': object()})
        with self.assertRaises(ValueError):
            r('vote{{ x|pluralize }}', {'x': 'foo'})

    def test_floatformat(self):
        assert r('{{ 1.3434|floatformat }}') == '1.3'
        assert r('{{ 1.3511|floatformat }}') == '1.4'
        assert r('{{ 1.3|floatformat(2) }}') == '1.30'
        assert r('{{ 1.30|floatformat(-3) }}') == '1.300'
        assert r('{{ 1.000|floatformat(3) }}') == '1.000'
        assert r('{{ 1.000|floatformat(-3) }}') == '1'
        with self.assertRaises(ValueError):
            r('{{ "foo"|floatformat(3) }}')

        with self.assertRaises(ValueError):
            r('{{ 4.33|floatformat("foo") }}')

    def test_date_stuff(self):
        from django_cofingo import env
        assert r('a{{ d|date("Y") }}b', {'d': date(2007, 01, 01)}) == 'a2007b'
        assert r('a{{ d|time("H") }}b', {'d': datetime(2007, 01, 01, 12, 01, 01)}) == 'a12b'
        # TODO: timesince, timeuntil

        # Make sure the date filters can handle unset values gracefully.
        # While generally we'd like to be explicit instead of hiding errors,
        # this is a particular case where it makes sense.
        for f in ('date', 'time', 'timesince', 'timeuntil'):
            assert r('a{{ d|%s }}b' % f) == 'ab'
            assert r('a{{ d|%s }}b' % f, {'d': None}) == 'ab'

