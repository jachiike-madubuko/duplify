"""
Change your models (in models.py).
Run python django423/mysite/manage.py makemigrations to create migrations for those changes
Run python django423/mysite/manage.py migrate --run-syncdb to apply those changes to the database.
"""

from __future__ import unicode_literals

from django.db import models
import dedupper_app.settings as settings

def strip(string):
    if type(string) == int:
        return str(int)
    else:
        newstring = string.replace(" ","")
        return newstring


class Simple(models.Model):
    title = models.CharField(max_length=128)
    author = models.CharField(max_length=128)
    category = models.CharField(max_length=128)
    average = models.IntegerField(null=True, blank=True)
    TYPES_OF_RECORD = (  ('Undecided', 'Undecided'),
        ('Duplicate', 'Duplicate'),
        ('New Record', 'New Record')  )
    type = models.CharField(max_length=128, choices=TYPES_OF_RECORD, default='Undecided')

    closest1 = models.ForeignKey('Simple', on_delete=models.CASCADE, related_name='the_closest', null=True, blank=True)
    closest2 = models.ForeignKey('Simple', on_delete=models.CASCADE, related_name='second_closest', null=True, blank=True)
    closest3 = models.ForeignKey('Simple', on_delete=models.CASCADE, related_name='third_closest', null=True, blank=True)

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


class Contact(models.Model):
    CRD = models.IntegerField( unique=True, blank=True)
    firstName = models.CharField(max_length=128)
    lastName = models.CharField(max_length=128)
    suffix = models.CharField(max_length=128)
    canSellDate = models.DateField()
    levelGroup = models.CharField(max_length=128)
    mailingStreet = models.CharField(max_length=128)
    mailingCity = models.CharField(max_length=128)
    mailingStateProvince = models.CharField(max_length=128)
    mailingZipPostalCode = models.IntegerField(blank=True)
    territory = models.CharField(max_length=128)
    workPhone = models.CharField(max_length=128)
    homePhone = models.CharField(max_length=128)
    mobilePhone = models.CharField(max_length=128)
    workEmail = models.CharField(max_length=128)
    personalEmail = models.CharField(max_length=128)
    otherEmail = models.CharField(max_length=128)
    area = models.CharField(max_length=128)
    region = models.CharField(max_length=128)
    regionalLeader = models.CharField(max_length=128)
    levelLeader = models.CharField(max_length=128)
    fieldTrainerLeader = models.CharField(max_length=128)
    performanceLeader = models.CharField(max_length=128)
    boaName = models.CharField(max_length=128)

    def __str__(self):
        return '{}, {}'.format(self.lastName, self.firstName,)

    def key(self, key_parts):
        key = ''

        key_builder = {
            'CRD': strip(self.CRD),
            'firstName': strip(self.firstName),
            'lastName': strip(self.lastName),
            'suffix': strip(self.suffix),
            'canSellDate': strip(self.canSellDate),
            'levelGroup': strip(self.levelGroup),
            'mailingStreet': strip(self.mailingStreet),
            'mailingCity': strip(self.mailingCity),
            'mailingStateProvince': strip(self.mailingStateProvince),
            'mailingZipPostalCode': strip(self.mailingZipPostalCode),
            'territory': strip(self.territory),
            'ID': strip(self.ID),
            'workPhone': strip(self.workPhone),
            'homePhone': strip(self.homePhone),
            'mobilePhone': strip(self.mobilePhone),
            'workEmail': strip(self.workEmail),
            'personalEmail': strip(self.personalEmail),
            'otherEmail': strip(self.otherEmail),
            'area': strip(self.area),
            'region': strip(self.region),
            'regionalLeader': strip(self.regionalLeader),
            'levelLeader': strip(self.levelLeader),
            'fieldTrainerLeader': strip(self.fieldTrainerLeader),
            'performanceLeader': strip(self.performanceLeader),
            'boaName': strip(self.boaName),
        }

        for part in key_parts:
            key += key_builder[part]
        return key
    

class RepContact(Contact):
    average = models.IntegerField(null=True, blank=True)
    TYPES_OF_RECORD = (('Undecided', 'Undecided'),
                       ('Duplicate', 'Duplicate'),
                       ('New Record', 'New Record'))
    type = models.CharField(max_length=128, choices=TYPES_OF_RECORD, default='Undecided')

    closest1 = models.ForeignKey('SFContact', on_delete=models.CASCADE, related_name='the_closest', null=True,
                                 blank=True)
    closest2 = models.ForeignKey('SFContact', on_delete=models.CASCADE, related_name='second_closest', null=True,
                                 blank=True)
    closest3 = models.ForeignKey('SFContact', on_delete=models.CASCADE, related_name='third_closest', null=True,
                                 blank=True)
    dupFlag = models.BooleanField(blank=True, default=False)




class SFContact(Contact):
    closest_rep = models.ForeignKey('RepContact', on_delete=models.CASCADE, related_name='the_closest', null=True,
                                 blank=True)
    dupFlag = models.BooleanField(blank=True, default=False)


#TODO fix db for missing contact tbale