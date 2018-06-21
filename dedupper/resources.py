from import_export import resources
from .models import Simple, RepContact, SFContact

class SimpleResource(resources.ModelResource):
    class Meta:
        model = Simple
        
class RepContactResource(resources.ModelResource):
    class Meta:
        model = RepContact


class SFContactResource(resources.ModelResource):
    class Meta:
        model = SFContact


