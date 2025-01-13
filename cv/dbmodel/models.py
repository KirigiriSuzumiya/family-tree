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
    xing = models.CharField(max_length=100, blank=True, null=True)
    ming = models.CharField(max_length=100, blank=True, null=True)
    zi = models.CharField(max_length=100, blank=True, null=True)
    other_name = models.CharField(max_length=100, blank=True, null=True)


    mate = models.CharField(max_length=50, blank=True, null=True)
    father = models.CharField(max_length=50, blank=True, null=True)
    mother = models.CharField(max_length=50, blank=True, null=True)
    kids = models.JSONField(blank=True, null=True)
    info = models.CharField(max_length=50000, blank=True, null=True)
    family_name = models.CharField(max_length=100, blank=True, null=True)

    visited = models.IntegerField(default=0)
    visit_time = models.CharField(max_length=50000, blank=True, null=True)
    institute = models.CharField(max_length=50000, blank=True, null=True)
    edu = models.CharField(max_length=50000, blank=True, null=True)
    located_time = models.CharField(max_length=50000, blank=True, null=True)

    def __str__(self):
        return self.name

class Image(models.Model):
    path = models.CharField(max_length=1000)
    token_time = models.DateTimeField(blank=True, null=True)
    info = models.CharField(max_length=50000, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    count = models.IntegerField(blank=True, null=True)
    use_baidu = models.BooleanField(default=False)
    loc_x = models.CharField(max_length=50, blank=True, null=True)
    loc_y = models.CharField(max_length=50, blank=True, null=True)
    loc_info = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self):
        return self.path


class FaceImage(models.Model):
    path = models.CharField(max_length=50000, primary_key=True)
    upload_time = models.DateTimeField(default=timezone.now)
    name = models.ForeignKey(People, on_delete=models.CASCADE, null=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    token = models.CharField(max_length=50000, null=True, blank=True)
    logid = models.CharField(max_length=50000, null=True, blank=True)
    def __str__(self):
        return self.path


class Location(models.Model):
    belongs_to = models.ForeignKey(People, on_delete=models.CASCADE)
    loc_x = models.CharField(max_length=50, blank=True, null=True)
    loc_y = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    description = models.CharField(max_length=5000, blank=True, null=True)
