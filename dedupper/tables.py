import django_tables2 as tables
from dedupper.models import Simple
from django_tables2.utils import AttributeDict
from django.utils.safestring import mark_safe


class SimpleTable(tables.Table):

    merge = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary', 'href':"#" }, text="Merge")

    def render_merge(self, record):
        href = record.title
        return mark_safe('<a id="yo" class="btn btn-outline-primary" onclick="merge()" href="'+str(href)+'" Merge>Merge</a>')

    class Meta:
        model = Simple
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark' }
