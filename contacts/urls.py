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
from django.views import generic
from django.conf.urls import url, include
from django.contrib import admin
from contacts import models
from contacts import views
from django.conf import settings

admin.autodiscover()

urlpatterns = [
    path('', views.index, name='index'),
    path('contacts/', views.contacts, name='contacts'),
    path('table/', views.table, name='table'),
    path('plotly/', views.plotly, name='plotly'),
#     url(r'^keys', views.upload, name='keys'),
#     path('key-gen/', views.key_gen, name='key-gen'),
#     path('heroku/', generic.ListView.as_view(model=models.Contact), name='heroku'),
#     path('run/', views.run, name='run'),
#     path('sorted/<id>', views.merge, name='merge'),
#     path('sorted/export/<type>', views.download, name='export'),
#     path('sorted/report/<type>', views.download_times, name='report'),
]

