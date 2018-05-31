from import_export import resources
from .models import Simple

class SimpleResource(resources.ModelResource):
    class Meta:
        model = Simple