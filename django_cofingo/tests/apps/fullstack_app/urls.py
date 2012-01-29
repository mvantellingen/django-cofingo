from django.conf.urls.defaults import *

urlpatterns = patterns('apps.fullstack_app',
    url(r'^$', 'views.index', name='index'),
)
