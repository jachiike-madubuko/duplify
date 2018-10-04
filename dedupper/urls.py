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
from django.conf.urls import url
from django.contrib import admin
from django.urls import path

from . import views

admin.autodiscover()

urlpatterns = [
    path('v1/', views.index, name='v1'),
    url(r'^keys', views.upload, name='keys'),
    path('key-gen/', views.key_gen, name='key-gen'),
    # path('heroku/', generic.ListView.as_view(model=models.Contact), name='heroku'),
    path('run/', views.run, name='run'),
    path('map/', views.map, name='map'),
    path('login/', views.login, name='login'),
    path('', views.upload_page, name='upload_page'),
    path('progress/', views.progress, name='progress'),
    path('db_progress/', views.db_progress, name='db_progress'),
    path('closest/', views.closest, name='closest'),
    path('tables/', views.turn_table, name='tables'),
    path('search/', views.search, name='search'),
    path('flush_db/', views.flush_db, name='flush_db'),
    path('duplify/', views.duplify, name='duplify'), #figure out url reverse
    path('resort/', views.resort, name='resort'), #figure out url reverse
    path('contact_sort/', views.contact_sort, name='contact_sort'), #figure out url reverse
    path('v2/', views.display, name='v2'),
    path('sorted/<id>', views.merge, name='merge'),
    path('hatch/<id>', views.hatcher, name='hatcher'),
    path('sorted/export/<type>', views.download, name='export'),
    path('sorted/report/<type>', views.download_times, name='report'),
]

