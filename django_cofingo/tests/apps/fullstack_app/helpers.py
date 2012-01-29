from django_cofingo.library import Library

library = Library()


@library.filter
def my_filter(value):
    return 'my-foo-filter'
