from jinja2 import environmentfilter, Markup, Undefined
from django.utils.safestring import EscapeData, SafeData


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
