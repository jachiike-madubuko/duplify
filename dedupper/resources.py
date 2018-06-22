from import_export import resources
from .models import Simple, RepContact, SFContact, DuplifyTime, DedupTime, UploadTime

class DuplifyTimeResource(resources.ModelResource):
    class Meta:
        model = DuplifyTime
        
class DedupTimeResource(resources.ModelResource):
    class Meta:
        model = DedupTime

class UploadTimeResource(resources.ModelResource):
    class Meta:
        model = UploadTime

class RepContactResource(resources.ModelResource):
    class Meta:
        model = RepContact


class SFContactResource(resources.ModelResource):
    class Meta:
        model = SFContact


