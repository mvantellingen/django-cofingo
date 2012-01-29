"""Adapter for using Jinja2 with Django."""
import imp
import logging

import jinja2
from django.conf import settings
from django.template.base import Origin, TemplateDoesNotExist
from django.template.context import get_standard_processors
from django.template.loader import BaseLoader
from django.utils.importlib import import_module

from django_cofingo.utils import django_filter_to_jinja2


VERSION = (0, 1)
__version__ = '.'.join(map(str, VERSION))

log = logging.getLogger('django_cofingo')


class Environment(jinja2.Environment):

    def __init__(self):
        self._libraries = []

        loader = jinja2.ChoiceLoader(self._get_loaders())
        options = self._get_options()

        super(Environment, self).__init__(
            extensions=options['extensions'],
            loader=loader,
            trim_blocks=True,
            autoescape=True,
            auto_reload=settings.DEBUG,
        )

        # Note: options already includes Jinja2's own builtins (with
        # the proper priority), so we want to assign to these attributes.
        self.filters = options['filters'].copy()
        self.globals = options['globals'].copy()
        self.tests = options['tests'].copy()
        for key, value in options['attrs'].items():
            setattr(self, key, value)

        # Set the environment in all libraries found.
        for library in self._libraries:
            library.set_env(self)

    def from_string(self, source, globals=None, template_class=None):
        return super(Environment, self).from_string(
            source, globals, template_class or Template)

    def _get_loaders(self):
        """Mimic Django's setup by loading templates from directories in
        TEMPLATE_DIRS and packages in INSTALLED_APPS.

        """
        x = ((jinja2.FileSystemLoader, settings.TEMPLATE_DIRS),
             (jinja2.PackageLoader, settings.INSTALLED_APPS))
        return [loader(p) for loader, places in x for p in places]

    def _get_options(self):
        """Generate a dictionary with the extensions, filters, globals, tests
        and attrs to be set on the Jinja2 environment.

        The options are added in the following order::

            * Django builtin filters
            * Jinja2 builtin filters, tests, and globals
            * Cofingo builtin filters, and extensions
            * Libraries from Django's INSTALLED_APPS (helpers.py)
            * Filters, extensions, tests and globals from DJANGO_SETTINGS

        """
        from django_cofingo import filters as cofingo_filters
        from django_cofingo import extensions as cofingo_extensions
        from django.conf import settings
        from django.template import builtins as django_builtins
        from django.core.urlresolvers import get_callable

        # Note that for extensions, the order in which we load the libraries
        # is not maintained: https://github.com/mitsuhiko/jinja2/issues#issue/3
        # Extensions support priorities, which should be used instead.
        options = {
            'extensions': [],
            'filters': {},
            'globals': {},
            'tests': {},
            'attrs': {}
        }

        def update_options(library):
            options['extensions'].extend(library.extensions)
            options['filters'].update(library.filters)
            options['globals'].update(library.globals)
            options['tests'].update(library.tests)
            options['attrs'].update(library.attrs)

        # Start with Django's builtins; this give's us all of Django's
        # filters courtasy of our interop layer.
        for lib in django_builtins:
            for name, func in lib.filters.iteritems():
                options['filters'][name] = django_filter_to_jinja2(func)

        # The stuff Jinja2 comes with by default should override Django.
        options['filters'].update(jinja2.defaults.DEFAULT_FILTERS)
        options['tests'].update(jinja2.defaults.DEFAULT_TESTS)
        options['globals'].update(jinja2.defaults.DEFAULT_NAMESPACE)

        # Our own set of builtins are next, overwriting Jinja2's.
        update_options(cofingo_filters.library)
        update_options(cofingo_extensions.library)

        # Optionally, include the i18n extension.
        if settings.USE_I18N:
            options['extensions'].append('jinja2.ext.i18n')

        # Next, add the globally defined extensions from the settings
        options['extensions'].extend(
            list(getattr(settings, 'JINJA2_EXTENSIONS', [])))

        # Finally, add extensions defined in application's templatetag
        # libraries
        for library in self._get_app_libraries():
            update_options(library)

        def from_setting(setting):
            retval = {}
            setting = getattr(settings, setting, {})
            if isinstance(setting, dict):
                for key, value in setting.iteritems():
                    retval[key] = callable(value) and value \
                        or get_callable(value)
            else:
                for value in setting:
                    value = callable(value) and value or get_callable(value)
                    retval[value.__name__] = value
            return retval
        options['filters'].update(from_setting('JINJA2_FILTERS'))
        options['globals'].update(from_setting('JINJA2_GLOBALS'))
        options['tests'].update(from_setting('JINJA2_TESTS'))

        for module_name in getattr(settings, 'COFINGO_HELPERS', []):
            module = import_module(module_name)
            update_options(module.library)
        return options

    def _get_app_libraries(self):
        for app in settings.INSTALLED_APPS:
            try:
                app_path = import_module(app).__path__
                imp.find_module('helpers', app_path)
            except (AttributeError, ImportError):
                continue

            module = import_module('%s.helpers' % app)
            if hasattr(module, 'library'):

                # Set the environment in the library
                self._libraries.append(module.library)
                yield module.library


def render_to_string(request, template, context=None):
    """
    Render a template into a string.
    """
    def get_context():
        c = {} if context is None else context.copy()
        for processor in get_standard_processors():
            c.update(processor(request))
        return c

    # If it's not a Template, it must be a path to be loaded.
    if not isinstance(template, jinja2.environment.Template):
        template = env.get_template(template)

    return template.render(get_context())

# Create the environment
env = Environment()


class Template(jinja2.Template):

    def render(self, context={}):
        """Render's a template, context can be a Django Context or a
        dictionary.
        """
        # flatten the Django Context into a single dictionary.
        context_dict = {}
        if hasattr(context, 'dicts'):
            for d in context.dicts:
                context_dict.update(d)
        else:
            context_dict = context

            # Django Debug Toolbar needs a RequestContext-like object in order
            # to inspect context.
            class FakeRequestContext:
                dicts = [context]
            context = FakeRequestContext()

        # Used by debug_toolbar.
        if settings.TEMPLATE_DEBUG:
            from django.test import signals
            self.origin = Origin(self.filename)
            signals.template_rendered.send(sender=self, template=self,
                                           context=context)

        # Jinja2 internally converts the context instance to a dictionary, thus
        # we need to store the current_app attribute as a key/value pair.
        context_dict['_current_app'] = getattr(context, 'current_app', None)

        return super(Template, self).render(context_dict)


class Loader(BaseLoader):
    is_usable = True
    env.template_class = Template

    def load_template(self, template_name, template_dirs=None):
        if hasattr(template_name, 'rsplit'):
            exclude_apps = getattr(settings, 'COFINGO_EXCLUDE_APPS', [
                'debug_toolbar',
                'admin'
            ])

            app = template_name.rsplit('/')[0]
            if app in exclude_apps:
                raise TemplateDoesNotExist(template_name)
        try:
            template = env.get_template(template_name)
            return template, template.filename
        except jinja2.TemplateNotFound:
            raise TemplateDoesNotExist(template_name)

