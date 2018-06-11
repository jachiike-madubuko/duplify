"""
Change your models (in models.py).
Run python django423/mysite/manage.py makemigrations to create migrations for those changes
Run python django423/mysite/manage.py migrate --run-syncdb to apply those changes to the database.
"""

from __future__ import unicode_literals

from django.db import models

def strip(string):
    newstring = string.replace(" ","")
    return  newstring


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
        return '{} by {} \n\t has Record type: {} with a match of {}%'.format(self.title, self.author, self.type, self.average)

    def key(self, key_parts):
        key=''

        key_builder = {
            'title': strip(self.title),
            'author': strip(self.author),
            'catergory': strip(self.category)
        }

        for part in key_parts:
            key += key_builder[part]
        return key

#model manager that returns object based on key code
#function to create its all key map


#create contact model
#create rep_contact and sf_contact that inherit from contact
#set up model for SF contact