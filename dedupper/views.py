from django.shortcuts import render
from django.views.generic import TemplateView, ListView
import django_tables2
import dedupper.models
import dedupper.filters
import dedupper.tables
from tablib import Dataset
from dedupper.resources import SimpleResource
import pandas as pd
import csv




class FilteredSingleTableView(django_tables2.SingleTableView):
    filter_class = None

    def get_table_data(self):
        data = super(FilteredSingleTableView, self).get_table_data()
        self.filter = self.filter_class(self.request.GET, queryset=data)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(FilteredSingleTableView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        return context


class SimpleFilteredSingleTableView(FilteredSingleTableView):
    model = dedupper.models.Simple
    table_class = dedupper.tables.SimpleTable
    filter_class = dedupper.filters.SimpleFilter


class SimpleSingleTableView(django_tables2.SingleTableView):
    model = dedupper.models.Simple
    table_class = dedupper.tables.SimpleTable


class FilteredTableView(ListView):
    model = dedupper.models.Simple

    def get_context_data(self, **kwargs):
        context = super(FilteredTableView, self).get_context_data(**kwargs)
        filter = dedupper.filters.SimpleFilter(self.request.GET, queryset=self.object_list)

        table = dedupper.tables.SimpleTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table
        return context


class FilterExListView(ListView):
    model = dedupper.models.Simple

    def get_context_data(self, **kwargs):
        context = super(FilterExListView, self).get_context_data(**kwargs)
        filter = dedupper.filters.SimpleFilterEx(self.request.GET, queryset=self.object_list)

        table = dedupper.tables.SimpleTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table

        return context


    #TODO Add view for csv upload
    #TODO set up postgresql
    #TODO heroku connect

def index(request):
    if(request.method == 'GET'):
        return render(request, 'dedupper/rep_list_upload.html')
    else:
        simple_resource = SimpleResource()
        dataset = Dataset()
        #TODO format uploadeded file before using django-import-export
        #find out how to convert from bytes to csv
        #https://docs.djangoproject.com/en/2.0/ref/files/uploads/
        #https://docs.djangoproject.com/en/2.0/ref/files/
        print('uploading file')
        uploadedfile = request.FILES['myfile']
        new_simples= uploadedfile.read()

        newCSV = pd.read_csv(new_simples)
        imported_data = dataset.load(newCSV)
        result = simple_resource.import_data(imported_data, dry_run=True)  # Test the data import

        if not result.has_errors():
            print('importing data')
            simple_resource.import_data(imported_data, dry_run=False)  # Actually import now

        return render(request, 'dedupper/simple_list.html')

