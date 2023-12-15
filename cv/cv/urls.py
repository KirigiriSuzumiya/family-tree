"""cv URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth.decorators import login_required
from . import views
from . import views_ar
urlpatterns = [
    path(r'', views.index),
    path(r'index', views.index),
    path('about', views.about),
    path(r'admin/', admin.site.urls),
    path(r'faceupload', login_required(views.face_upload)),
    path(r'pic_upload', login_required(views.pic_upload)),
    path(r'name_upload', login_required(views.name_upload)),
    path(r'recognition', login_required(views.recognition)),
    path(r'recognition_upload', login_required(views.recognition_upload)),
    path(r'namelist', login_required(views.namelist)),
    path(r'piclist', login_required(views.piclist)),
    path(r'user', views.user_view),
    path(r'user_oper', views.user_oper),
    path(r'logout', views.logout_view),
    re_path(r'pic_change/(.*)$', login_required(views.pic_change)),
    re_path(r'facelist/(.*)$', login_required(views.facelist)),
    re_path(r'face_edit/(.*)$', login_required(views.face_edit)),
    re_path(r'face_edit_info', login_required(views.face_edit_info)),
    re_path(r'face_edit_check/(.*)$', login_required(views.face_edit_check)),
    re_path(r'edit_pic/(.*)$', login_required(views.edit_pic)),
    re_path(r'pic_info/(.*)$', login_required(views.pic_info)),
    re_path(r'pic_info_edit/(.*)$', login_required(views.pic_info_edit)),
    re_path(r'recog_again/(.*)$', login_required(views.recog_again)),
    path(r'demo', views.demo),
    # path(r'baidu', login_required(views.baidu_upload)),
    path("upload_again", login_required(views.upload_again)),
    re_path("baidu_extract/(.*)$", login_required(views.baidu_extract)),
    re_path("social_graph/(.*)$", views.social_graph),
    re_path("social_info/(.*)$", views.social_info),
    re_path("social_info_person/(.*)$", views.social_info_person),
    path("ar", views_ar.ar),
    # path("data_transfer", views.data_transfer),
    path("name2id", views.name2id_researcher),
    path("peo_obj_ini", views.peo_obj_ini),
    path("info2excel", views.info2excel),
    path("id2name", views.id2name_researcher),
    path("image_obj_ini", views.image_obj_ini),
    path("face_obj_ini",views.face_obj_ini)
]




