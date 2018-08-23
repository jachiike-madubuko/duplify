from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import render
import pandas  as pd
from tablib import Dataset
import csv
# Create your views here.

def index(request):
    print('scrape')
    return render(request, 'scraper/index.html')


def scrape(request):
    print('run scraper')
    print('get results from scraper')
    filename = 'filename="Scraper.csv"'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; ' + filename
    export = pd.DataFrame({i: [j for j in range(10)] for i in range(10)})
    dataset = Dataset()
    dataset.csv = export.to_csv(index=False)

    writer = csv.writer(response)
    for line in dataset:
        writer.writerow(line)

    return response
