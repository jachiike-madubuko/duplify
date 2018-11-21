"""
Change your models (in models.py).
Run python django423/mysite/manage.py makemigrations dedupper to create migrations for those changes
Run python manage.py migrate dedupper to apply those changes to the database.
"""

from __future__ import unicode_literals

from django.db import models


# from heroku_connect.db import models as hc_models

def strip(string):
    if string == '':
        return 'NULL'
    newstring = string.replace(" ", "").lower().strip()
    return  newstring

class simple(models.Model):
    title = models.CharField(max_length=256)
    author = models.CharField(max_length=256)
    category = models.CharField(max_length=256)
    average = models.IntegerField(null=True, blank=True)
    TYPES_OF_RECORD = (
        ('Undecided', 'Undecided'),
        ('Duplicate', 'Duplicate'),
        ('New Record', 'New Record')  )
    type = models.CharField(max_length=256, choices=TYPES_OF_RECORD, default='Undecided')

    closest1 = models.ForeignKey('simple', on_delete=models.CASCADE, related_name='the_closest', null=True, blank=True)
    closest2 = models.ForeignKey('simple', on_delete=models.CASCADE, related_name='second_closest', null=True, blank=True)
    closest3 = models.ForeignKey('simple', on_delete=models.CASCADE, related_name='third_closest', null=True, blank=True)

    def __str__(self):
        return '{} by {} \n\t has Record type: {}'.format(self.title, self.author, self.type, self.average)

    def key(self, key_parts):
        key=''

        key_builder = {
            'title': strip(self.title),
            'author': strip(self.author),
            'category': strip(self.category)
        }

        for part in key_parts:
            key += key_builder[part]
        return key

# class Contact(hc_models.HerokuConnectModel):
#     sf_object_name= 'Contact'
#
#     CRD = hc_models.Text( sf_field_name='CRD__c', max_length=80)
#
#     name = hc_models.Text( sf_field_name='Name', max_length=80)
#     firstName = hc_models.Text( sf_field_name='FirstName', max_length=80)
#     middleName = hc_models.Text( sf_field_name='MiddleName', max_length=80)
#     lastName = hc_models.Text( sf_field_name='LastName', max_length=80)
#     suffix = hc_models.Text( sf_field_name='Suffix', max_length=80)
#
#     mailingStreet = hc_models.Text( sf_field_name='MailingStreet', max_length=80)
#     mailingCity = hc_models.Text( sf_field_name='MailingCity', max_length=80)
#     mailingState = hc_models.Text( sf_field_name='MailingState', max_length=80)
#     mailingPostalCode = hc_models.Text( sf_field_name='MailingPostalCode', max_length=80)
#
#     Phone = hc_models.Phone( sf_field_name='Phone', max_length=80)
#     mobilePhone = hc_models.Phone( sf_field_name='MobilePhone', max_length=80)
#     homePhone = hc_models.Phone( sf_field_name='HomePhone', max_length=80)
#     otherPhone = hc_models.Phone( sf_field_name='OtherPhone', max_length=80)
#
#     email = hc_models.Email(sf_field_name='Email')
#     otherEmail = hc_models.Email(sf_field_name='Other_Email__c')
#     personalEmail = hc_models.Email(sf_field_name='Personal_Email__c')
#
#     def __str__(self):
#         return self.name
#
#     def key(self, key_parts):
#         key = ''
#
#         key_builder = {
#             'CRD': strip(self.CRD),
#             'firstName': strip(self.firstName),
#             'lastName': strip(self.lastName),
#             'suffix': strip(self.suffix),
#             'canSellDate': strip(self.canSellDate),
#             'levelGroup': strip(self.levelGroup),
#             'mailingStreet': strip(self.mailingStreet),
#             'mailingCity': strip(self.mailingCity),
#             'mailingStateProvince': strip(self.mailingStateProvince),
#             'mailingZipPostalCode': strip(self.mailingZipPostalCode),
#             'territory': strip(self.territory),
#             'ID': strip(self.ID),
#             'workPhone': strip(self.workPhone),
#             'homePhone': strip(self.homePhone),
#             'mobilePhone': strip(self.mobilePhone),
#             'workEmail': strip(self.workEmail),
#             'personalEmail': strip(self.personalEmail),
#             'otherEmail': strip(self.otherEmail),
#             'area': strip(self.area),
#             'region': strip(self.region),
#             'regionalLeader': strip(self.regionalLeader),
#             'levelLeader': strip(self.levelLeader),
#             'fieldTrainerLeader': strip(self.fieldTrainerLeader),
#             'performanceLeader': strip(self.performanceLeader),
#             'boaName': strip(self.boaName),
#         }
#
#         for part in key_parts:
#             key += key_builder[part]
#         return key

'''
repContact.objects.update(type='Undecided', keySortedBy='',closest1='', closest2='', closest3='', closest1_contactID='', closest2_contactID='', closest3_contactID='', average=None)
'''
class repContact(models.Model):
    CRD = models.CharField(max_length=256, db_column="CRD")
    firstName = models.CharField(max_length=256, blank=True)
    middleName = models.CharField(max_length=256, blank=True)
    lastName = models.CharField(max_length=256, blank=True)
    suffix = models.CharField(max_length=256, blank=True)
    mailingStreet = models.CharField(max_length=256, blank=True)
    mailingCity = models.CharField(max_length=256, blank=True)
    mailingStateProvince = models.CharField(max_length=256, blank=True)
    mailingZipPostalCode = models.CharField(max_length=256, blank=True)
    Phone = models.CharField(max_length=256, blank=True)
    homePhone = models.CharField(max_length=256, blank=True)
    mobilePhone = models.CharField(max_length=256, blank=True)
    otherPhone = models.CharField(max_length=256, blank=True)
    workEmail = models.CharField(max_length=256, blank=True)
    personalEmail = models.CharField(max_length=256, blank=True)
    otherEmail = models.CharField(max_length=256, blank=True)
    average = models.IntegerField(null=True, blank=True)
    TYPES_OF_RECORD = (('Undecided', 'Undecided'),
                       ('Duplicate', 'Duplicate'),
                       ('Manual Check', 'Manual Check'),
                       ('New Record', 'New Record'))
    type = models.CharField(max_length=256, choices=TYPES_OF_RECORD, default='Undecided')

    closest1_contactID = models.CharField(max_length=256, blank=True)
    closest1 = models.ForeignKey('sfcontact', on_delete=models.CASCADE, related_name="first_%(app_label)s_%("
                                                                                     "class)s_related",
                                 related_query_name="%(app_label)s_%(class)s", null=True, blank=True)

    closest2_contactID = models.CharField(max_length=256, blank=True)
    closest2 = models.ForeignKey('sfcontact', on_delete=models.CASCADE, related_name="second_%(app_label)s_%("
                                                                                     "class)s_related",
                                 related_query_name="%(app_label)s_%(class)ss", null=True, blank=True)

    closest3_contactID = models.CharField(max_length=256, blank=True)
    closest3 = models.ForeignKey('sfcontact', on_delete=models.CASCADE, related_name="third_%(app_label)s_%("
                                                                                     "class)s_related",
                                 related_query_name="%(app_label)s_%(class)sss", null=True, blank=True)

    dupFlag = models.BooleanField(blank=True, default=False)
    keySortedBy = models.CharField(max_length=256, blank=True)
    misc = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return '{} {}'.format(self.firstName, self.lastName,)

    def full_name(self):
        return '{} {}'.format(self.firstName, self.lastName)

    def email(self):
        if self.workEmail != '':
            email = self.workEmail
        elif self.otherEmail != '':
            email = self.otherEmail
        elif self.personalEmail != '':
            email = self.personalEmail
        else:
            email = ''
        return '{}'.format(email)

    def phone(self):
        if self.Phone != '':
            email = self.Phone
        elif self.otherPhone != '':
            email = self.otherPhone
        elif self.mobilePhone != '':
            email = self.mobilePhone
        elif self.homePhone != '':
            email = self.homePhone
        else:
            email = ''
        return '{}'.format(email)

    def locale(self):
        return '{}, {} {}'.format(self.mailingCity, self.mailingStateProvince, self.mailingZipPostalCode)

    def key(self, key_parts):
        key = ''

        key_builder = {
            'CRD': strip(self.CRD),
            'firstName': strip(self.firstName),
            'lastName': strip(self.lastName),
            'suffix': strip(self.suffix),
            'mailingStreet': strip(self.mailingStreet),
            'mailingCity': strip(self.mailingCity),
            'mailingStateProvince': strip(self.mailingStateProvince),
            'mailingZipPostalCode': strip(self.mailingZipPostalCode),
            'Phone': strip(self.Phone),
            'homePhone': strip(self.homePhone),
            'mobilePhone': strip(self.mobilePhone),
            'otherPhone': strip(self.otherPhone),
            'workEmail': strip(self.workEmail),
            'personalEmail': strip(self.personalEmail),
            'otherEmail': strip(self.otherEmail),
        }

        for part in key_parts:
            key += key_builder[part]
        return key

    #create functions that generate semantically exploitable strings for matching

class sfcontact(models.Model):
    CRD = models.CharField(max_length=256, db_column="CRD")
    ContactID = models.CharField(max_length=256, blank=True)
    firstName = models.CharField(max_length=256, blank=True)
    middleName = models.CharField(max_length=256, blank=True)
    lastName = models.CharField(max_length=256, blank=True)
    suffix = models.CharField(max_length=256, blank=True)
    mailingStreet = models.CharField(max_length=256, blank=True)
    mailingCity = models.CharField(max_length=256, blank=True)
    mailingStateProvince = models.CharField(max_length=256, blank=True)
    mailingZipPostalCode = models.CharField(max_length=256, blank=True)
    Phone = models.CharField(max_length=256, blank=True)
    homePhone = models.CharField(max_length=256, blank=True)
    mobilePhone = models.CharField(max_length=256, blank=True)
    otherPhone = models.CharField(max_length=256, blank=True)
    workEmail = models.CharField(max_length=256, blank=True)
    personalEmail = models.CharField(max_length=256, blank=True)
    otherEmail = models.CharField(max_length=256, blank=True)
    closest_rep = models.ForeignKey('repContact', on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(class)s", null=True,
                                 blank=True)
    dupFlag = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return '{} {}'.format(self.firstName, self.lastName,)

    def full_name(self):
        return '{} {}'.format(self.firstName, self.lastName)

    def email(self):
        if self.workEmail != '':
            email = self.workEmail
        elif self.otherEmail != '':
            email = self.otherEmail
        elif self.personalEmail != '':
            email = self.personalEmail
        else:
            email = ''
        return '{}'.format(email)

    def phone(self):
        if self.Phone != '':
            email = self.Phone
        elif self.otherPhone != '':
            email = self.otherPhone
        elif self.mobilePhone != '':
            email = self.mobilePhone
        elif self.homePhone != '':
            email = self.homePhone
        else:
            email = ''
        return '{}'.format(email)

    def locale(self):
        return '{}, {} {}'.format(self.mailingCity, self.mailingStateProvince, self.mailingZipPostalCode)

    def key(self, key_parts):
        key = ''
        key_builder = {
            'CRD': strip(self.CRD),
            'ContactID': strip(self.ContactID),
            'firstName': strip(self.firstName),
            'lastName': strip(self.lastName),
            'suffix': strip(self.suffix),
            'mailingStreet': strip(self.mailingStreet),
            'mailingCity': strip(self.mailingCity),
            'mailingStateProvince': strip(self.mailingStateProvince),
            'mailingZipPostalCode': strip(self.mailingZipPostalCode),
            'Phone': strip(self.Phone),
            'homePhone': strip(self.homePhone),
            'mobilePhone': strip(self.mobilePhone),
            'otherPhone': strip(self.otherPhone),
            'workEmail': strip(self.workEmail),
            'personalEmail': strip(self.personalEmail),
            'otherEmail': strip(self.otherEmail),
        }

        for part in key_parts:
            key += key_builder[part]
        return key

class progress(models.Model):
    label = models.CharField(max_length=256, blank=True)
    total = models.IntegerField(null=True, blank=True)
    total_keys = models.IntegerField(null=True, blank=True)
    completed = models.IntegerField(null=True, blank=True, default=0)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta():
        get_latest_by = "created_on"

    def complete(self):
        print('\a')
        self.completed += 1
        self.save()

class dedupTime(models.Model):
    id = models.BigAutoField(primary_key=True)
    num_threads = models.IntegerField(null=True, blank=True)
    num_SF = models.IntegerField(null=True, blank=True)
    num_dup = models.IntegerField(null=True, blank=True)
    num_new = models.IntegerField(null=True, blank=True)
    num_undie= models.IntegerField(null=True, blank=True)
    seconds = models.FloatField( null=True, blank=True)
    avg = models.FloatField( null=True, blank=True)
    current_key = models.CharField(max_length=256, blank=True, null=True)
    created_on = models. DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
       return "At {} -- {} dups and {} new".format(self.created_on, self.num_dup, self.num_new)

    class Meta():
        get_latest_by = "created_on"


class duplifyTime(models.Model):
    num_threads = models.IntegerField(null=True, blank=True)
    num_SF = models.IntegerField(null=True, blank=True)
    num_rep = models.IntegerField(null=True, blank=True)
    seconds = models.FloatField( null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return "{} reps <=> {} SF records in {} seconds".format(self.num_rep, self.num_SF, self.seconds)

class uploadTime(models.Model):
    num_threads = models.IntegerField(default=1, null=True, blank=True)
    num_records = models.IntegerField(null=True, blank=True)
    batch_size = models.IntegerField(null=True, blank=True)
    seconds = models.FloatField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} records uploaded in {} seconds".format(self.num_records, self.seconds)