from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import render
import pandas  as pd
from tablib import Dataset
from collections import defaultdict
from scraper import finra_check_job
import csv
# Create your views here.

def index(request):
    print('scrape')
    return render(request, 'scraper/index.html')


def scrape(request):
    #apex callout sends json data with group, indi, and channel attrs if not filled then = 0
    sf = Salesforce(password='7924Trill!', username='jmadubuko@wealthvest.com', organizationId='00D36000001DkQo')

    export = finra_check_job(request.GET)


    print('run scraper')
    print('get results from scraper')
    filename = 'filename="Scraper.csv"'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; ' + filename
    dataset = Dataset()
    dataset.csv = export.to_csv(index=False)

    writer = csv.writer(response)
    for line in dataset:
        writer.writerow(line)

    return response
