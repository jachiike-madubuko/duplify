from import_export import resources
from .models import simple, repContact, sfcontact, duplifyTime, dedupTime, uploadTime
from import_export.fields import Field


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
    sales_force_link = Field()

    class Meta:
        model = repContact
        fields = ('id', 'CRD', 'firstName', 'lastName', 'mailingStreet', 'mailingCity', 'mailingStateProvince', 'mailingZipPostalCode', 'Phone', 'homePhone', 'mobilePhone', 'otherPhone', 'workEmail', 'personalEmail', 'otherEmail', 'keySortedBy', 'average')
        # exclude = ('closest1','closest2','closest3','average','type','dupFlag')

    def dehydrate_sales_force_link(self, repcontact):
        return 'https://na30.salesforce.com/{} '.format(repcontact.closest1_contactID)


class SFContactResource(resources.ModelResource):
    class Meta:
        model = sfcontact


