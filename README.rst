Cofingo is a combination of Coffin (http://github.com/coffin/coffin) and Jingo (http://github.com/jbalogh/jingo). It allows the usage of Jinja2 templates while keeping the tags and filters from Django (e.g. the URL tag)

Like Jingo the way to add custom filters, tags (extensions), and tests is by creating a helpers.py file in your app. 

Getting started
===============

The easiest way to install Cofingo is by using **pip**::

    pip install django-cofingo

The development version can be found at::

    http://github.com/mvantellingen/django-cofingo


Configuration
=============

Add `django_cofingo.Loader` to your settings::

    TEMPLATE_LOADERS = (
        'django_cofingo.Loader',
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

Templates are then rendered by Jinja2 whichever method is used (It works for class based views, TemplateResponse etc).

If you want to prevent that the templates of a specific app are rendered with Jinja2 then you can excluded them in your settings file::

    COFINGO_EXCLUDED_APPS = ['admin', 'debug_toolbar']

(Note that these two apps are added by default)


Creating custom filters and extensions
======================================

Create a `helpers` module in your django app and add the following::

    from django_cofingo.library import Library

    library = Library()


If you want to add a filter add the following::

    @library.filter
    def my_custom_filter(value):
        return value + '-filtered'

Adding an extension can be done as follow::

    from django_cofingo.library import Library
    from django_assets.env import get_env
    from webassets.ext.jinja2 import AssetsExtension

    library = Library()
    library.attr('assets_environment', get_env())
    library.extension(AssetsExtension)

You can also add other modules with a library to Cofingo by specifying them in
your settings.py file::

    COFINGO_HELPERS = [
        'myproject.helpers'
    ]

