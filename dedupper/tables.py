import django_tables2 as tables
from dedupper.models import Simple


class SimpleTable(tables.Table):
    class Meta:
        model = Simple
        template_name = 'django_tables2/bootstrap.html'