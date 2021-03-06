# Generated by Django 4.0.1 on 2022-02-22 15:11

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=1000)),
                ('token_time', models.DateTimeField(blank=True)),
                ('info', models.CharField(blank=True, max_length=1000)),
                ('title', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='People',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100)),
                ('display_name', models.CharField(blank=True, max_length=100)),
                ('first_name', models.CharField(blank=True, max_length=50)),
                ('middle_name', models.CharField(blank=True, max_length=50)),
                ('last_name', models.CharField(blank=True, max_length=50)),
                ('sex', models.CharField(blank=True, choices=[('female', 'Female')], max_length=20)),
                ('birth_date', models.DateTimeField(blank=True)),
                ('death_date', models.DateTimeField(blank=True)),
                ('mate', models.CharField(blank=True, max_length=50)),
                ('father', models.CharField(blank=True, max_length=50)),
                ('mother', models.CharField(blank=True, max_length=50)),
                ('kids', models.JSONField(blank=True)),
                ('info', models.CharField(blank=True, max_length=500)),
                ('loc1_x', models.CharField(blank=True, max_length=50)),
                ('loc1_y', models.CharField(blank=True, max_length=50)),
                ('loc1_info', models.CharField(blank=True, max_length=50)),
                ('loc2_x', models.CharField(blank=True, max_length=50)),
                ('loc2_y', models.CharField(blank=True, max_length=50)),
                ('loc2_info', models.CharField(blank=True, max_length=50)),
                ('loc3_x', models.CharField(blank=True, max_length=50)),
                ('loc3_y', models.CharField(blank=True, max_length=50)),
                ('loc3_info', models.CharField(blank=True, max_length=50)),
                ('xing', models.CharField(blank=True, max_length=100)),
                ('ming', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='FaceImage',
            fields=[
                ('path', models.CharField(max_length=1000, primary_key=True, serialize=False)),
                ('upload_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dbmodel.image')),
                ('name', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='dbmodel.people')),
            ],
        ),
    ]
