import os
import sys

from setuptools import setup, find_packages, Command

install_requires = [
    'Django>=1.3',
    'Jinja2>=2.5'
]


class RunTests(Command):
    """From django-celery"""
    description = "Run the tests"
    user_options = []
    extra_env = {}
    extra_args = ['django_cofingo']

    def run(self):
        for env_name, env_value in self.extra_env.items():
            os.environ[env_name] = str(env_value)

        sys.path.append(os.path.join(
            os.path.dirname(__file__), 'django_cofingo', 'tests'))

        from django.conf import settings
        from django.core.management import execute_manager

        if not settings.configured:
            settings.configure(
                DATABASE_ENGINE='sqlite3',
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'TEST_NAME': 'cofingo_tests.db',
                    },
                },
                INSTALLED_APPS=[
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                    'django.contrib.admin',
                    'django.contrib.sessions',
                    'django.contrib.sites',

                    'django_cofingo',
                    'apps.urls_app',
                    'apps.fullstack_app',
                ],
                TEMPLATE_LOADERS=[
                    'django_cofingo.Loader'
                ],
                ROOT_URLCONF='apps.urls',
                DEBUG=False,
                SITE_ID=1,
                TEMPLATE_DEBUG=True,
                TEMPLATE_DIRS=[],
                SETTINGS_MODULE='apps'
            )

        prev_argv = list(sys.argv)
        try:
            sys.argv = [__file__, "test"] + self.extra_args
            execute_manager(settings, argv=sys.argv)
        finally:
            sys.argv = prev_argv

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


readme = []
with open('README.rst', 'r') as fh:
    readme = fh.readlines()


setup(
    name='django-cofingo',
    version='0.2',
    license='BSD',
    url='http://github.com/mvantellingen/django-cofingo',
    author='Michael van Tellingen',
    author_email='michaelvantellingen@gmail.com',
    description='Jinja2 template renderer for Django',
    long_description=''.join(readme),
    install_requires=install_requires,
    zip_safe=False,
    cmdclass={"test": RunTests},
    packages=find_packages(exclude=('tests')),
    include_package_data=True,
)
