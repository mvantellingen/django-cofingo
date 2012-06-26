import datetime

import pytz
from django.conf import settings
from django.utils.safestring import EscapeData, SafeData
from jinja2 import environmentfilter, Markup, Undefined

if settings.TIME_ZONE:
    local_tzinfo = pytz.timezone(settings.TIME_ZONE)
else:
    local_tzinfo = pytz.utc


def localtime(value):
    return value.astimezone(local_tzinfo)


def is_naive(value):
    """
    Determines if a given datetime.datetime is naive.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is None or value.tzinfo.utcoffset(value) is None


def template_localtime(value, use_tz=None):
    """
    Checks if value is a datetime and converts it to local time if necessary.

    If use_tz is provided and is not None, that will force the value to
    be converted (or not), overriding the value of settings.USE_TZ.

    This function is designed for use by the template engine.
    """
    should_convert = (isinstance(value, datetime.datetime)
        and (settings.USE_TZ if use_tz is None else use_tz)
        and not is_naive(value)
        and getattr(value, 'convert_to_local_time', True))
    return localtime(value) if should_convert else value


def django_filter_to_jinja2(filter_func):
    """
    Note: Due to the way this function is used by
    ``coffin.template.Library``, it needs to be able to handle native
    Jinja2 filters and pass them through unmodified. This necessity
    stems from the fact that it is not always possible to determine
    the type of a filter.

    TODO: Django's "func.is_safe" is not yet handled
    """
    def _convert_out(v):
        if isinstance(v, SafeData):
            return Markup(v)
        if isinstance(v, EscapeData):
            return Markup.escape(v)  # not 100% equivalent, see mod docs
        return v

    def _convert_in(v):
        if isinstance(v, Undefined):
            # Essentially the TEMPLATE_STRING_IF_INVALID default
            # setting. If a non-default is set, Django wouldn't apply
            # filters. This is something that we neither can nor want to
            # simulate in Jinja.
            return ''
        return v

    def conversion_wrapper(value, *args, **kwargs):
        result = filter_func(_convert_in(value), *args, **kwargs)
        return _convert_out(result)
    # Jinja2 supports a similar machanism to Django's
    # ``needs_autoescape`` filters: environment filters. We can
    # thus support Django filters that use it in Jinja2 with just
    # a little bit of argument rewriting.
    if hasattr(filter_func, 'needs_autoescape'):
        @environmentfilter
        def autoescape_wrapper(environment, *args, **kwargs):
            kwargs['autoescape'] = environment.autoescape
            return conversion_wrapper(*args, **kwargs)
        return autoescape_wrapper
    else:
        return conversion_wrapper
