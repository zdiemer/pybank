from . import views
from django.conf.urls import url
app_name = 'main'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^register/$', views.UserFormView.as_view(), name='register'),
    url(r'^transfer/$', views.TranferView.as_view(), name='transfer'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout', kwargs={'next_page': '/main'}),
]
