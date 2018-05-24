from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_tables2 import RequestConfig
from .models import Simple
from .tables import SimpleTable

def index(request):
    table = SimpleTable(Simple.objects.all(), order_by='author')
    RequestConfig(request).configure(table)
    return render(request, 'dedupper/dedupper.html', {'table': table})
