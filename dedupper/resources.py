from import_export import resources
from .models import Simple, Contact, RepContact, SFContact

class SimpleResource(resources.ModelResource):
    class Meta:
        model = Simple

class ContactResource(resources.ModelResource):
    class Meta:
        model = Contact

class RepContactResource(resources.ModelResource):
    class Meta:
        model = RepContact

class SFContactResource(resources.ModelResource):
    class Meta:
        model = SFContact


