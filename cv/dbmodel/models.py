from django.db import models
from django.utils import timezone
# Create your models here.


class People(models.Model):
    name = models.CharField(max_length=100, default='')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    sex_choice = models.TextChoices('male', 'female')
    sex = models.CharField(blank=True, choices=sex_choice.choices, max_length=20, null=True)
    birth_date = models.DateTimeField(blank=True, null=True)
    death_date = models.DateTimeField(blank=True, null=True)


    mate = models.CharField(max_length=50, blank=True, null=True)
    father = models.CharField(max_length=50, blank=True, null=True)
    mother = models.CharField(max_length=50, blank=True, null=True)
    kids = models.JSONField(blank=True, null=True)
    info = models.CharField(max_length=500, blank=True, null=True)
    loc1_x = models.CharField(max_length=50, blank=True, null=True)
    loc1_y = models.CharField(max_length=50, blank=True, null=True)
    loc1_info = models.CharField(max_length=50, blank=True, null=True)
    loc2_x = models.CharField(max_length=50, blank=True, null=True)
    loc2_y = models.CharField(max_length=50, blank=True, null=True)
    loc2_info = models.CharField(max_length=50, blank=True, null=True)
    loc3_x = models.CharField(max_length=50, blank=True, null=True)
    loc3_y = models.CharField(max_length=50, blank=True, null=True)
    loc3_info = models.CharField(max_length=50, blank=True, null=True)
    xing = models.CharField(max_length=100, blank=True, null=True)
    ming = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class Image(models.Model):
    path = models.CharField(max_length=1000)
    token_time = models.DateTimeField(blank=True, null=True)
    info = models.CharField(max_length=1000, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.path


class FaceImage(models.Model):
    path = models.CharField(max_length=1000, primary_key=True)
    upload_time = models.DateTimeField(default=timezone.now)
    name = models.ForeignKey(People, on_delete=models.CASCADE, null=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)

    def __str__(self):
        return self.path


