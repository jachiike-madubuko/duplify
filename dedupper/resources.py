from import_export import resources
from .models import Simple, Contact

class SimpleResource(resources.ModelResource):
    class Meta:
        model = Simple
        
class ContactResource(resources.ModelResource):
    class Meta:
        model = Contact