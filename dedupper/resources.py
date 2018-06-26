from import_export import resources
from .models import simple, repContact, sfcontact, duplifyTime, dedupTime, uploadTime

class DuplifyTimeResource(resources.ModelResource):
    class Meta:
        model = duplifyTime
        
class DedupTimeResource(resources.ModelResource):
    class Meta:
        model = dedupTime

class UploadTimeResource(resources.ModelResource):
    class Meta:
        model = uploadTime

class RepContactResource(resources.ModelResource):
    class Meta:
        model = repContact


class SFContactResource(resources.ModelResource):
    class Meta:
        model = sfcontact


