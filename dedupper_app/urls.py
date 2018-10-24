"""dedupper_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.views.static import serve

urlpatterns = [
    path('dedupper/', include('dedupper.urls')),
    path('scraper/', include('scraper.urls')),
    path('contacts/', include('contacts.urls')),
    path('', include('dedupper.urls')),
    path(r'jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
    path(r'jet/', include('jet.urls', 'jet')),  # Django JET URLS
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path(r'media/<path>',
             serve, {
                 'document_root': settings.MEDIA_ROOT,
             }),
    ]
