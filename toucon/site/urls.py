from django.conf.urls import include
from django.contrib.flatpages.views import flatpage
from django.urls import path, re_path
from django.views.generic import TemplateView

from toucon.site import views


conference_patterns = ([
    path('<slug:code>/', include([
        path('', views.ConferenceView.as_view(), name='app'),
        path('-/badges.pdf', views.ConferenceBadgesView.as_view(), name='badges'),
    ])),
], 'conference_patterns')

registration_patterns = ([
    path('<uuid:uuid>/', include([
        path('', views.RegistrationView.as_view(), name='app'),
    ])),
    path('<slug:code>/', views.RegistrationRedirectView.as_view(), name='redirect'),
], 'registration_patterns')

urlpatterns = [
    path('c/', include(conference_patterns, namespace='conference')),
    path('r/', include(registration_patterns, namespace='registration')),
    path('u/', include('allauth.urls')),
    path('u/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('disclaimer/', flatpage, {'url': '/disclaimer/'}, name='disclaimer'),
    path('privacy/', flatpage, {'url': '/privacy/'}, name='privacy'),
    path('terms/', flatpage, {'url': '/terms/'}, name='terms'),
    path('', TemplateView.as_view(template_name='pages/homepage.html'), name='homepage'),
]

# Flatpages “catchall” pattern
urlpatterns += [
    re_path(r'^(?P<url>.*/)$', flatpage),
]
