from . import views
from django.conf.urls import url
app_name = 'main'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^register/$', views.UserFormView.as_view(), name='register'),
    url(r'^(?P<pk>[0-9]+)/transfer_process/(?P<id>[0-9]+)/$', views.TransferView.as_view(), name='transfer'),
    url(r'^(?P<pk>[0-9]+)/transfer_between/(?P<id>[0-9]+)/$', views.TransferBetweenView.as_view(), name='transfer_between'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout', kwargs={'next_page': '/main'}),
]
