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
from django.urls import path
from django.conf.urls import url, include
from django.contrib import admin
from . import views
from django.conf import settings

admin.autodiscover()

urlpatterns = [
    path('', views.index, name='index'),
    url(r'^keys', views.upload, name='keys'),
    path('key-gen/', views.key_gen, name='key-gen'),
    path('run/', views.run, name='run'),
    path('progress/', views.progress, name='progress'),
    path('stats/', views.stats, name='stats'),
    path('duplify/', views.duplify, name='duplify'), #figure out url reverse
    path('loading/<keylist>', views.loading, name='loading'), #figure out url reverse
    path('sorted/', views.display, name='reps'),
    path('sorted/<CRD>', views.merge, name='merge'),
    path('sorted/export/<type>', views.download, name='export'),
    path('sorted/report/<type>', views.download_times, name='report'),
]
