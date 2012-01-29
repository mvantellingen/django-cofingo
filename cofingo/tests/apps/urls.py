from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^url_test/', include('apps.urls_app.urls')),

    (r'^fullstack/', include('apps.fullstack_app.urls')),

    # These two are used to test that our url-tag implementation can
    # deal with application namespaces / the "current app".
    (r'^app/one/', include('apps.urls_app.urls',
                           app_name="testapp", namespace="testapp")),

    (r'^app/two/', include('apps.urls_app.urls',
                           app_name="testapp", namespace="two")),
)
