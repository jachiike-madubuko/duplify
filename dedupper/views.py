from django.shortcuts import render
from django.views.generic import TemplateView, ListView
import django_tables2
import dedupper.models
import dedupper.filters
import dedupper.tables
from tablib import Dataset
from dedupper.resources import SimpleResource



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

    def simple_upload(request):
        if request.method == 'POST':
            simple_resource = SimpleResource()
            dataset = Dataset()
            print('uploading file')
            new_simples = request.FILES['myfile']
            imported_data = dataset.load(new_simples.read())
            result = simple_resource.import_data(imported_data, dry_run=True)  # Test the data import

            if not result.has_errors():
                print('importing data')
                simple_resource.import_data(imported_data, dry_run=False)  # Actually import now

        return render(request, 'dedupper/simple_list.html')

def index(request):

    return render(request, 'dedupper/rep_list_upload.html')
