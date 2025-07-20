import base64

import numpy as np
import pandas as pd
import requests
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render
import os
import time
from pathlib import Path
from .codes import FaceRecognition, FaceExtractor
from .settings import BASE_DIR
from dbmodel.models import FaceImage, People, Location
from dbmodel.models import Image as image_db
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import subprocess
from pypinyin import lazy_pinyin
from django.core.paginator import Paginator
import re
import json
import shutil
import cv2
import subprocess
from io import BytesIO

# -*- coding: CP936 -*-
config_path = os.path.join(os.path.dirname(__file__),"..","..","config.json")
auth_config = json.load(open(config_path,"r"))
api_key = auth_config["face_api_key"]
secret_key = auth_config["face_secret_key"]

def always():
    context = {
        "info": FaceRecognition.initialing(),
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "people_num": People.objects.all().count,
        "pic_num": image_db.objects.all().count,
        "face_num": FaceImage.objects.all().count,
    }
    return context


def about(request):
    return render(request, 'about.html')


def face_upload(request):
    context = always()
    return render(request, 'faceupload.html', context)


def pic_change(request, path):
    BASE_DIR = Path(__file__).resolve().parent.parent
    submit_pic = request.FILES.get('pic')
    with open(os.path.join(BASE_DIR, "upload", path), "wb") as f:
        for line in submit_pic:
            f.write(line)
    return HttpResponseRedirect("/pic_info/"+path)


def pic_upload(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    submit_pic = request.FILES.get('pic')
    pic_suffix = submit_pic.name.split(".")[-1]  # 获取后缀
    pic_path = os.path.join(str(time.time()) + "." + pic_suffix)  # 构造文件路径
    with open(os.path.join(BASE_DIR, "upload", pic_path), "wb") as f:
        for line in submit_pic:
            f.write(line)
    img_path = os.path.join(BASE_DIR, "upload", pic_path)
    try:
        face_num = FaceExtractor.extractor(img_path)
    except:
        messages.error(request, '您上传的文件不是合法的图片文件')
        return HttpResponseRedirect('/faceupload')

    context = {}
    context["upload_states"] = "上传成功！共找到%d个人脸" % face_num
    context["total_path"] = os.path.join(pic_path)
    path_list = []
    for i in range(face_num):
        path_list.append(os.path.join("temp_image", pic_path[0:pic_path.rfind('.')]+'-'+str(i+1)+pic_path[pic_path.rfind("."):]))
    context["path_list"] = path_list
    return render(request, 'NameUpload.html', context)


def baidu_extract(request, img_path):

    try:
        face_num = FaceExtractor.baidu_extractor(img_path)
    except:
        messages.error(request, '您上传的文件不是合法的图片文件')
        return HttpResponseRedirect('/faceupload')
    pic_path = os.path.basename(img_path)
    context = {}
    context["upload_states"] = "上传成功！共找到%d个人脸" % face_num
    context["total_path"] = os.path.join(pic_path)
    path_list = []
    for i in range(face_num):
        path_list.append(os.path.join("temp_image", pic_path[0:pic_path.rfind('.')]+'-'+str(i+1)+pic_path[pic_path.rfind("."):]))
    context["path_list"] = path_list
    return render(request, 'NameUpload.html', context)


def pic_compress(pic_path, target_size=5000, quality=90, step=5, pic_type='.jpg'):
    # 读取图片bytes
    with open(pic_path, 'rb') as f:
        pic_byte = f.read()

    img_np = np.frombuffer(pic_byte, np.uint8)
    img_cv = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)

    current_size = len(pic_byte) / 1024
    print("图片压缩前的大小为(KB)：", current_size)
    while current_size > target_size:
        pic_byte = cv2.imencode(pic_type, img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), quality])[1]
        if quality - step < 0:
            break
        quality -= step
        current_size = len(pic_byte) / 1024

    # 保存图片
    out_path = pic_path[:pic_path.rfind(".")]+".jpg"
    with open(out_path, 'wb') as f:
        f.write(BytesIO(pic_byte).getvalue())

    return out_path


def up_sample_extract(request, img_path):
    img_path_abs = os.path.join(BASE_DIR, "upload", img_path)
    time_now = str(time.time())
    # Final2x_config = {
    #     "gpuid": -1,
    #     "inputpath": [img_path_abs],
    #     "model": "RealCUGAN-pro",
    #     "modelscale": 2,
    #     "modelnoise": -1,
    #     "outputpath": os.path.join(BASE_DIR, "statics", "up_sample"),
    #     "targetscale": 2.0,
    #     "tta": False}
    # json_path = os.path.join(BASE_DIR,"temp",time_now+".json")
    # json.dump(Final2x_config, open(json_path,"w"))
    # subprocess.call(f"/usr/local/bin/Final2x-core -y {json_path}", shell=True)
    url = "http://110.42.255.139:33082/upsampler?url=http://nenva.com/static/upload/"+img_path
    payload = {}
    headers = {
    'Access-Control-Allow-Origin': '*'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    up_img_path = os.path.join(BASE_DIR, "statics", "up_sample", time_now+img_path[img_path.rfind("."):])
    with open(up_img_path, "wb") as fp:
        fp.write(response.content)
    try:
        cv2.imread(up_img_path)
        with open(up_img_path, 'rb') as fp:
            if len(fp.read())/1024 >= 5125:
                up_img_path = pic_compress(up_img_path)
    except:
        messages.error(request, "上采样失败")
        os.remove(up_img_path)
        return HttpResponseRedirect("/faceupload")
    new_img_path = time_now + img_path[img_path.rfind("."):]
    shutil.copyfile(up_img_path,
                    os.path.join(BASE_DIR,"upload",new_img_path))
    os.remove(up_img_path)
    shutil.copyfile(os.path.join(BASE_DIR,"upload",img_path),
                    os.path.join(BASE_DIR,"statics","up_sample",new_img_path))
    try:
        image = image_db(path=new_img_path)
        image.save()
        face_num = FaceExtractor.baidu_extractor(new_img_path)
    except:
        messages.error(request, '您上传的文件不是合法的图片文件(可能是图片超出大小了)')
        return HttpResponseRedirect(f'/static/upload/{new_img_path}')
    pic_path = os.path.basename(new_img_path)
    context = {}
    context["upload_states"] = "上传成功！共找到%d个人脸" % face_num
    context["total_path"] = os.path.join(pic_path)
    path_list = []
    for i in range(face_num):
        path_list.append(os.path.join("temp_image", pic_path[0:pic_path.rfind('.')]+'-'+str(i+1)+pic_path[pic_path.rfind("."):]))
    context["path_list"] = path_list
    return render(request, 'NameUpload.html', context)
    

def name_upload(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    namelist = []
    if request.POST:
        path_list = eval(request.POST["path_list"])
        for i in range(len(path_list)):
            path = path_list[i]
            path = os.path.join(BASE_DIR, "statics/", path)
            path = os.path.normpath(path)
            name = request.POST['name' + str(i + 1)]
            i += 1
            if name == '':
                continue
            info, id = FaceRecognition.dict_add(path, name)
            if info != 1:
                messages.error(request, info)
                return HttpResponseRedirect('/faceupload')
            namelist.append([name, id])
    context = {"namelist": namelist}
    return render(request, "info.html", context)


num = 0


def recognition(request):
    if request.method == 'POST':
        global num
        num = (num + 1) % 3
        return HttpResponse(FaceRecognition.info + "…" * num)
    context = always()
    return render(request, 'recognition.html', context)


def recognition_upload(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    submit_pic = request.FILES.get('pic')
    tolerance = eval(request.POST['tolerance']) / 10
    pic_suffix = submit_pic.name.split(".")[-1]  # 获取后缀
    pic_path = os.path.join(str(time.time()) + "." + pic_suffix)  # 构造文件路径
    with open(os.path.join(BASE_DIR, "upload", pic_path), "wb") as f:
        for line in submit_pic:
            f.write(line)
    img_path = os.path.join(BASE_DIR, "upload", pic_path)
    try:
        return_dic = FaceRecognition.face_matchng(img_path, request, tolerance)
    except:
        messages.error(request, '您上传的文件不是合法的图片文件或者图片中没有可分辨的人脸！')
        return HttpResponseRedirect('/recognition')
    context = {}
    if return_dic == "no_face_error":
        messages.error(request, '无法识别出人脸，请上传清晰的人脸图片')
        return HttpResponseRedirect('/recognition')
    context['path'] = return_dic['path']
    context['xls_path'] = return_dic['path'][:return_dic['path'].rfind('.')] + '.xls'
    context['result'] = return_dic['result']
    return render(request, 'recognition_result.html', context)


def index(request):
    context = always()
    return render(request, 'index.html', context)


def piclist(request):
    if request.method == "POST":
        names = image_db.objects.filter(title__icontains=request.POST["search"]).only("id")
        paginator = Paginator(names, len(names))
    else:
        names = image_db.objects.all().only("id")
        paginator = Paginator(names, 10)
    current_num = int(request.GET.get("page", 1))
    name_in_page = paginator.page(current_num)
    # name_in_page = image_db.objects.filter(id__in=[j.id for j in name_in_page])
    context = always()
    filter_list = []
    count = 1
    for i, img_id in enumerate(name_in_page):
            img_obj = image_db.objects.get(id=img_id.id)
            name = img_obj.path
            if img_obj.title:
                name = img_obj.title
            path =img_obj.path
            number = img_obj.count
            relate = len(FaceImage.objects.filter(image=img_obj))
            if relate == 0:
                continue
            filter_list.append([name, path, number, count, relate])
            count = (count + 1) % 2
    context['piclist'] = filter_list
    # 大于11页时
    if paginator.num_pages > 11:
        # 当前页码的后5页数超过最大页码时，显示最后10项
        if current_num + 5 > paginator.num_pages:
            page_range = range(paginator.num_pages - 10, paginator.num_pages + 1)
        # 当前页码的前5页数为负数时，显示开始的10项
        elif current_num - 5 < 1:
            page_range = range(1, 12)
        else:
            # 显示左5页到右5页的页码
            page_range = range(current_num - 5, current_num + 5 + 1)
    # 小于11页时显示所有页码
    else:
        page_range = paginator.page_range
    context['page_range'] = page_range
    context['current_num'] = current_num
    context['end_page'] = paginator.num_pages
    return render(request, 'piclist.html', context)


def pic_clean(request):
    names = image_db.objects.filter(faceimage__isnull=True).only("id")
    paginator = Paginator(names, 10)
    current_num = int(request.GET.get("page", 1))
    name_in_page = paginator.page(current_num)
    # name_in_page = image_db.objects.filter(id__in=[j.id for j in name_in_page])
    context = always()
    filter_list = []
    count = 1
    for i, img_id in enumerate(name_in_page):
            img_obj = image_db.objects.get(id=img_id.id)
            name = img_obj.path
            if img_obj.title:
                name = img_obj.title
            path =img_obj.path
            number = img_obj.count
            relate = len(FaceImage.objects.filter(image=img_obj))
            filter_list.append([name, path, number, count, relate])
            count = (count + 1) % 2
    context['piclist'] = filter_list
    # 大于11页时
    if paginator.num_pages > 11:
        # 当前页码的后5页数超过最大页码时，显示最后10项
        if current_num + 5 > paginator.num_pages:
            page_range = range(paginator.num_pages - 10, paginator.num_pages + 1)
        # 当前页码的前5页数为负数时，显示开始的10项
        elif current_num - 5 < 1:
            page_range = range(1, 12)
        else:
            # 显示左5页到右5页的页码
            page_range = range(current_num - 5, current_num + 5 + 1)
    # 小于11页时显示所有页码
    else:
        page_range = paginator.page_range
    context['page_range'] = page_range
    context['current_num'] = current_num
    context['end_page'] = paginator.num_pages
    return render(request, 'pic_clean.html', context)


def pic_del(request, path):
    image_obj = image_db.objects.get(path=path)
    image_obj.delete()
    messages.error(request, path + "已删除")
    return HttpResponse("")


def namelist(request):
    context = always()
    namelist = []
    search = ""
    target = ""
    if request.GET.get("search"):
        search = request.GET["search"]
        target = request.GET["target"]
        if target == "name":
            names = People.objects.filter(Q(name__icontains=search)|
                                        Q(first_name__icontains=search) |
                                        Q(middle_name__icontains=search) |
                                        Q(last_name__icontains=search))\
                                            .distinct().order_by('name').only("id")
        elif target == "institute":
            names = People.objects.filter(Q(institute__icontains=search))\
                                            .distinct().order_by('name').only("id")
        elif target == "edu":
            names = People.objects.filter(Q(edu__icontains=search))\
                                            .distinct().order_by('name').only("id")
        paginator = Paginator(names, 24)
    else:
        names = People.objects.all().order_by('name').only("id")
        paginator = Paginator(names, 24)
    current_num = int(request.GET.get("page", 1))
    count = 1
    names = paginator.page(current_num)
    for i in names:
        i = People.objects.get(id=i.id)
        name = i.name
        en_name = ""
        if i.first_name:
            en_name = i.first_name+" "
        if i.middle_name:
            en_name = en_name + i.middle_name+" "
        if i.last_name:
            en_name = en_name + i.last_name
        if FaceImage.objects.filter(name=i):
            pic_obj = FaceImage.objects.filter(name=i)[0]
            upload_time = pic_obj.upload_time
            path = '/static/' + pic_obj.path
        else:
            pic_obj = 'none'
            upload_time = 'none'
            path = '/static/unknown.jpeg'
        namelist.append([name, upload_time, path, pic_obj, count, en_name, i.id])
        count = (count + 1) % 4
    # namelist.sort(key=lambda char: lazy_pinyin(char[0])[0][0])
    context['namelist'] = namelist
    # 大于11页时
    if paginator.num_pages > 11:
        # 当前页码的后5页数超过最大页码时，显示最后10项
        if current_num + 5 > paginator.num_pages:
            page_range = range(paginator.num_pages - 10, paginator.num_pages + 1)
        # 当前页码的前5页数为负数时，显示开始的10项
        elif current_num - 5 < 1:
            page_range = range(1, 12)
        else:
            # 显示左5页到右5页的页码
            page_range = range(current_num - 5, current_num + 5 + 1)
    # 小于11页时显示所有页码
    else:
        page_range = paginator.page_range
    context['page_range'] = page_range
    context['current_num'] = current_num
    context['end_page'] = paginator.num_pages
    context['search'] = search
    context['target'] = target
    return render(request, 'namelist.html', context)


def facelist(request, id):
    context = {}
    name_obj = People.objects.filter(id=id)[0]
    name = name_obj.name
    context['id'] = id
    context['name'] = name
    context['facelist'] = []
    context['first_name'] = name_obj.first_name
    context['middle_name'] = name_obj.middle_name
    context['last_name'] = name_obj.last_name
    context['sex'] = name_obj.sex
    context['birth_date'] = str(name_obj.birth_date).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
    context['death_date'] = str(name_obj.death_date).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
    context['xing'] = name_obj.xing
    context['ming'] = name_obj.ming
    context['family_name'] = name_obj.family_name
    context['zi'] = name_obj.zi
    context['other_name'] = name_obj.other_name
    context['located_time'] = name_obj.located_time

    context['mate'] = name_obj.mate
    context['father'] = name_obj.father
    context['mother'] = name_obj.mother
    if name_obj.kids:
        context['kids'] = str(name_obj.kids)
    else:
        context['kids'] = ''
    context['info'] = name_obj.info
    context['institute'] = name_obj.institute
    context['edu'] = name_obj.edu
    context['family'] = []
    # get face images
    face_obj_list = FaceImage.objects.filter(name=name_obj).order_by("-image__token_time")
    try:
        context['first_pic'] = '/static/' + face_obj_list[0].path
    except:
        context['first_pic'] = '/static/unknown.jpeg'
    count = 0
    context['locations'] = []
    for face_obj in face_obj_list:
        path = '/static/' + face_obj.path
        upload_time = face_obj.upload_time
        count = (count + 1) % 4
        re_path = face_obj.image.path
        token_time = face_obj.image.token_time
        try:
            token_age = face_obj.image.token_time.year - face_obj.name.birth_date.year
        except:
            token_age = None
        context['facelist'].append([upload_time, path, count, re_path, token_time, token_age])
        if face_obj.image.loc_x:
            context['locations'].append({
                "id": f"image_{face_obj.image.id}",
                "loc_x": face_obj.image.loc_x,
                "loc_y": face_obj.image.loc_y,
                "info": face_obj.image.loc_info,
                "path": face_obj.image.path,
                "date": str(face_obj.image.token_time).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
            })
    # get locations
    location_obj_list = Location.objects.filter(belongs_to=id).order_by("-date")
    for location in location_obj_list:
        print(location)
        context['locations'].append({
            "id": str(location.id),
            "loc_x": location.loc_x,
            "loc_y": location.loc_y,
            "info": location.description,
            "date": str(location.date).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
        })
    # family tree visualization
    if request.GET.get("detail"):
        tree_function_re = familytree(request, id)
        context["familytreepath"], family = tree_function_re["path"], tree_function_re["check"]
        
        for i in family:
            context["family"].append([i.id, i.name])
        context["known"]=[]
        FaceImage.objects.filter(name=People.objects.get(id=id))
        for group_photo in FaceImage.objects.filter(name=People.objects.get(id=id)):
            group_photo = group_photo.image
            faces = FaceImage.objects.filter(image=group_photo)
            for face in faces:
                if [face.name.id, face.name.name] in context["known"]:
                    continue
                else:
                    context["known"].append([face.name.id, face.name.name])
        context["new_graph"] = json.dumps(familytree_info(id), ensure_ascii=False)
    else:
        context["familytreepath"], family= None,[]
        context["family"] = []
        context["known"] = []
        context["new_graph"] = ""
    return render(request, 'facelist.html', context)


def face_edit(request, re_name):
    people_obj = People.objects.get(id=re_name)
    people_obj.name = request.POST['name'].strip()
    people_obj.first_name = request.POST['first_name'].strip()
    people_obj.middle_name = request.POST['middle_name'].strip()
    people_obj.last_name = request.POST['last_name'].strip()
    try:
        people_obj.sex = request.POST['sex']
    except:
        pass
    if request.POST['birth_date']:
        people_obj.birth_date = request.POST['birth_date']
    else:
        people_obj.birth_date = None
    if request.POST['death_date']:
        people_obj.death_date = request.POST['death_date']
    else:
        people_obj.death_date = None

    try:
        if request.POST['mate']:
            tmp = int(request.POST['mate'])
            people_obj.mate = request.POST['mate']
    except:
        messages.error(request, "mate不是合法的id形式！")
        return HttpResponseRedirect("/facelist/%s" % people_obj.id)
    
    try:
        if request.POST['father']:
            tmp = int(request.POST['father'])
            people_obj.father = request.POST['father']
    except:
        messages.error(request, "father不是合法的id形式！")
        return HttpResponseRedirect("/facelist/%s" % people_obj.id)
    
    try:
        if request.POST['mother']:
            tmp = int(request.POST['mother'])
            people_obj.mother = str(request.POST['mother'])
    except:
        messages.error(request, "mother不是合法的id形式！")
        return HttpResponseRedirect("/facelist/%s" % people_obj.id)
    
    try:
        people_obj.kids = eval(request.POST['kids'])
    except:
        messages.error(request, "子辈输入格式有误，修改失败")
        return HttpResponseRedirect("/facelist/%s" % people_obj.id)

    people_obj.info = request.POST['info']

    people_obj.xing = request.POST['xing']
    people_obj.ming = request.POST['ming']
    people_obj.family_name = request.POST['family_name']
    people_obj.institute = request.POST['institute']
    people_obj.edu = request.POST['edu']
    people_obj.zi = request.POST['zi']
    people_obj.other_name = request.POST['other_name']
    people_obj.located_time = request.POST['located_time']
    people_obj.save()
    messages.error(request, people_obj.name + "已修改")
    key: str
    location_set = set()
    for key in list(request.POST.keys()):
        if not key.startswith("loc_"):
            continue
        loc_id = key.split("_")[-1]
        if loc_id in location_set:
            continue
        else:
            location_set.add(loc_id)
        if loc_id == "new":
            if not request.POST["loc_x_new"]:
                continue
            loc_obj = Location(
                belongs_to=people_obj,
                loc_x=request.POST["loc_x_new"],
                loc_y=request.POST["loc_y_new"],
                date=request.POST["loc_date_new"] if request.POST["loc_date_new"] else None,
                description=request.POST["loc_info_new"]
            )
        else:
            loc_obj = Location.objects.get(id=int(loc_id))
            if not request.POST["loc_x_"+loc_id]:
                loc_obj.delete()
                continue
            loc_obj.loc_x=request.POST["loc_x_"+loc_id]
            loc_obj.loc_y=request.POST["loc_y_"+loc_id]
            loc_obj.date=request.POST["loc_date_"+loc_id] if request.POST["loc_date_"+loc_id] else None
            loc_obj.description=request.POST["loc_info_"+loc_id]

        loc_obj.save()

    return HttpResponseRedirect("/facelist/%s" % people_obj.id)


def face_edit_info(request):
    name = request.POST["name"]
    kids = []
    try:
        people_objs = People.objects.filter(father=name)
        for people in people_objs:
            kids.append(people.id)
    except:
        pass
    try:
        people_objs = People.objects.filter(mother=name)
        for people in people_objs:
            kids.append(people.id)
    except:
        pass
    try:
        people_objs = People.objects.filter(mate=name)
        kids.extend(people_objs[0].kids)
    except:
        pass
    try:
        res_kids = []
        [res_kids.append(i) for i in kids if i not in res_kids]
        res_kids = ';'.join(res_kids)
    except:
        res_kids = 'None'

    mate = None
    try:
        people_objs = People.objects.filter(mate=name)
        mate = people_objs[0].id
    except:
        pass
    parents = []
    try:
        people_objs = People.objects.all()
        for people in people_objs:
            if not people.kids:
                continue
            if name in people.kids:
                parents.append(people.id)
    except:
        pass
    return HttpResponse("补齐建议—伴侣：%s，孩子：%s，父辈：%s" % (mate, res_kids, parents))


def face_edit_check(request, id):
    out_message = ""
    people_obj = People.objects.get(id=int(id))

    # father
    try:
        father_obj = People.objects.get(id=int(people_obj.father))
        if not father_obj.kids or int(id) not in father_obj.kids:
            if father_obj.kids:
                father_obj.kids.append(int(id))
            else:
                father_obj.kids = [int(id)]
            father_obj.save()
            out_message += f"已为父亲对象({father_obj.name})更新kids字段！\n"
    except:
        out_message += "为父亲对象更新kids字段时出错！\n"
    # mother
    try:
        mother_obj = People.objects.get(id=int(people_obj.mother))
        if not mother_obj.kids or int(id) not in mother_obj.kids:
            if mother_obj.kids:
                mother_obj.kids.append(int(id))
            else:
                mother_obj.kids = [int(id)]
            mother_obj.save()
            out_message += f"已为母亲对象({mother_obj.name})更新kids字段！\n"
    except:
        out_message += "为母亲对象更新kids字段时出错！\n"
    # kids
    try:
        if not people_obj.sex:
            out_message += "要更新kids对象需要填写性别！！\n"
        else:
            kids = people_obj.kids
            for kid in kids:
                try:
                    kid_obj = People.objects.get(id=kid)
                    if people_obj.sex == "male":
                        if kid_obj.father and kid_obj.father != str(id):
                            out_message += f"更新kids对象(id={kid})的父亲字段时发生冲突，请手动检查错误！\n"
                        elif kid_obj.father == str(id):
                            pass
                        else:
                            kid_obj.father = str(id)
                            kid_obj.save()
                            out_message += f"已为kids对象({kid_obj.name})更新父亲字段！\n"
                    if people_obj.sex == "female":
                        if kid_obj.mother and kid_obj.mother != str(id):
                            out_message += f"更新kids对象(id={kid})的母亲字段时发生冲突，请手动检查错误！\n"
                        elif kid_obj.mother == str(id):
                            pass
                        else:
                            kid_obj.mother = str(id)
                            kid_obj.save()
                            out_message += f"已为kids对象({kid_obj.name})更新母亲字段！\n"
                except:
                    out_message += f"更新kids对象(id={kid})时发生错误！可能是对象不存在！\n"
    except:
        out_message += "尝试遍历kids列表时出错！\n"
    # mate
    try:
        mate_obj = People.objects.get(id=int(people_obj.mate))
        if mate_obj.mate and mate_obj.mate != str(id):
            out_message += f"更新mate对象(id={people_obj.mate})的mate字段时发生冲突，请手动检查错误！\n"
        elif mate_obj.mate == str(id):
            pass
        else:
            mate_obj.mate = str(id)
            mate_obj.save()
            out_message += f"已为mate对象({mate_obj.name})更新mate字段！\n"
    except:
        out_message += "更新mate对象时出错！"
    if len(out_message) == 0:
        messages.error(request, "没有需要关联更新的内容！")
    else:
        for message in out_message.split("\n"):
            messages.error(request, message)
    return HttpResponseRedirect("/facelist/%s" % id)
    # return HttpResponse(out_message)


def edit_pic(request, path):
    path = os.path.basename(path)
    img_obj = FaceImage.objects.filter(path=path)[0]
    img_obj.delete()
    messages.error(request, path + "已删除")
    return HttpResponseRedirect("/namelist")


def familytree(request, id):
    people_obj = People.objects.get(id=id)
    peo_obj_list = [people_obj]
    path = os.path.join(BASE_DIR, 'statics', 'temp_image', str(time.time()) + '.txt')
    fp = open(path, "w+", encoding="utf-8")
    fp.close()
    check = [people_obj]
    written = set()
    # bfs遍历
    while peo_obj_list:
        peo_now = peo_obj_list[0]
        print(peo_now)
        # 将孩子加入队列
        kids_list = peo_now.kids
        if kids_list:
            for kid in kids_list:
                try:
                    People.objects.get(id=kid)
                    if People.objects.get(id=kid) not in check:
                        peo_obj_list.insert(peo_obj_list.index(peo_now)+1, People.objects.get(id=kid))
                        check.insert(check.index(peo_now)+1, People.objects.get(id=kid))
                except:
                    pass
                finally:
                    pass

        # 将配偶加进队列
        try:
            print(People.objects.get(name=peo_now.mate))
            if People.objects.get(name=peo_now.mate) not in check:
                # peo_obj_list.insert(peo_obj_list.index(peo_now)+1, People.objects.get(name=peo_now.mate))
                check.insert(check.index(peo_now)+1, People.objects.get(name=peo_now.mate))
        except:
            pass
        # 将父亲加入队列
        try:
            People.objects.get(id=peo_now.father)
            if People.objects.get(id=peo_now.father) not in check:
                peo_obj_list.insert(peo_obj_list.index(peo_now), People.objects.get(id=peo_now.father))
                check.insert(check.index(peo_now), People.objects.get(id=peo_now.father))
        except:
            pass
        finally:
            pass
        # 将母亲加入队列
        try:
            People.objects.get(id=peo_now.mother)
            if People.objects.get(id=peo_now.mother) not in check:
                # peo_obj_list.insert(peo_obj_list.index(peo_now), People.objects.get(id=peo_now.mother))
                check.insert(check.index(peo_now), People.objects.get(id=peo_now.mother))
        except:
            pass
        finally:
            pass



        print(check, "\n")
        print(peo_obj_list, "\n")
        peo_obj_list.remove(peo_now)

    for peo_now in check:
        if peo_now not in written:
            couple_obj = re_familytree(peo_now, path)
            for obj in couple_obj:
                written.add(obj)
    shell = 'python ' + os.path.join(BASE_DIR, 'cv', 'codes', 'familytreemaker.py ') + path
    gra_path = path[:path.rfind('.')]
    fp = open(gra_path, 'w+', encoding="utf-8")
    p = subprocess.run(shell, stdout=subprocess.PIPE, shell=True)
    temp = p.stdout
    temp = temp.decode()

    fp.write(temp)
    fp.close()
    # os.remove(path)
    shell = "dot -Tpng " + gra_path + " -O"
    subprocess.run(shell, shell=True)
    os.remove(gra_path)
    context = {}
    context["name"] = people_obj.name
    context["path"] = "temp_image/" + os.path.basename(gra_path) + ".png"
    context["check"] = list(written)
    return context


def re_familytree(people_obj, path):
    # print(people_obj)
    fp = open(path, 'a', encoding="utf-8")
    couple_obj = []
    # 为无对象父母写txt
    # flag = 0
    # try:
    #     father = People.objects.get(id=people_obj.father.mate)
    # except:
    #     flag = flag+1
    # try:
    #     mother = People.objects.get(id=people_obj.mother.mate)
    # except:
    #     flag = flag+1
    # if flag == 2 and people_obj.father and people_obj.mother:
    #     fp.write(People.objects.get(id=people_obj.mother).name + "(F,id=%s)\n" % str(people_obj.mother))
    #     fp.write(People.objects.get(id=people_obj.father).name + "(M,id=%s)\n" % str(people_obj.father))
    #     fp.write("\t"+people_obj.name+"(id=%d)\n\n" % people_obj.id)
    #     couple_obj.append(People.objects.get(id=people_obj.mother))
    #     couple_obj.append(People.objects.get(id=people_obj.father))
    # 为配偶写txt
    try:
        mate = People.objects.get(id=people_obj.mate)
        fp.write(mate.name + "(id=%d," % mate.id)
        if mate.sex == "female":
            fp.write("F,")
        if mate.sex == "male":
            fp.write("M,")
        if mate.birth_date:
            fp.write("birthday=%s," % str(mate.birth_date)[:-9])
        if mate.death_date:
            fp.write("deathday=%s" % str(mate.death_date)[:-9])
        fp.write(")\n")
        couple_obj.append(mate)
    except:
        mate = people_obj.mate
        if not mate:
            fp.close()
            return [people_obj]
        fp.write(mate +"(id=%s)" % "".join(lazy_pinyin(people_obj.mate)).replace(' ', '').replace(".", '') + "\n")

    # 为自己写txt
    name = people_obj.name
    fp.write(name + "(id=%d," % people_obj.id)
    if people_obj.sex == "female":
        fp.write("F,")
    if people_obj.sex == "male":
        fp.write("M,")
    if people_obj.birth_date:
        fp.write("birthday=%s," % str(people_obj.birth_date)[:-9])
    if people_obj.death_date:
        fp.write("deathday=%s" % str(people_obj.death_date)[:-9])
    fp.write(")\n")
    couple_obj.append(people_obj)

    # 为后代写txt
    kids_list = set()
    try:
        for i in People.objects.get(id=people_obj.mate).kids:
            kids_list.add(i)
    except:
        pass
    try:
        for i in people_obj.kids:
            kids_list.add(i)
    except:
        pass
    try:
        mate_list = []
        for obj in People.objects.filter(mate=people_obj.id):
            mate_list.append(obj)
        for obj in People.objects.filter(mate=mate.id):
            mate_list.append(obj)
        for obj in mate_list:
            if obj.id != mate.id and obj.id != people_obj.id:
                try:
                    for i in obj.kids:
                        if i in kids_list:
                            kids_list.remove(i)
                except:
                    pass
    except:
        pass
    kids_list = list(kids_list)
    if kids_list:
        for i in range(len(kids_list)):
            kid = kids_list[i]
            date = ""
            try:
                kid_obj = People.objects.get(id=kid)
                date = str(kid_obj.birth_date)
            except:
                pass
            kids_list[i] = (kid_obj.name, date, kid)
    kids_list.sort(key=lambda x:x[1])
    if kids_list:
        for kid_tuple in kids_list:
            kid = kid_tuple[2]
            if not kid:
                continue
            try:
                People.objects.get(id=kid)
                fp.write("\t" + kid_tuple[0] + "(id=%d," % People.objects.get(id=kid).id)
                if People.objects.get(id=kid).sex == "female":
                    fp.write("F,")
                if People.objects.get(id=kid).sex == "male":
                    fp.write("M,")
                if People.objects.get(id=kid).birth_date:
                    fp.write("birthday=%s," % str(People.objects.get(id=kid).birth_date)[:-9])
                if People.objects.get(id=kid).death_date:
                    fp.write("deathday=%s" % str(People.objects.get(id=kid).death_date)[:-9])
                fp.write(")\n")
            except:
                fp.write("\t" + kid_tuple[0] + "(id=%s)" % "".join(lazy_pinyin(kid)).replace(' ', '').replace(".", '') + "\n")
    fp.write("\n")
    fp.close()
    return couple_obj


def familytree_info(id):
    people_obj = People.objects.get(id=id)
    peo_obj_list = [people_obj]
    check = [str(people_obj.id)]
    out_data = []
    back_check = dict()
    while peo_obj_list:
        peo_now = peo_obj_list[0]
        peo_obj_list.remove(peo_now)
        check.insert(0, str(peo_now.id))
        if FaceImage.objects.filter(name=peo_now.id):
            pic_obj = FaceImage.objects.filter(name=peo_now.id)[0]
            avatar_path = '/static/' + pic_obj.path
        else:
            avatar_path = '/static/unknown.jpeg'
        if peo_now.sex == "male":
            sex = "M"
        elif peo_now.sex == "female":
            sex = "F"
        else:
            sex = None
        full_name = (peo_now.first_name+" " if peo_now.first_name else "") + \
                    (peo_now.middle_name+" " if peo_now.middle_name else "") + \
                        (peo_now.last_name+" "  if peo_now.last_name else "")
        peo_info = {
            "id": str(peo_now.id),
            "data":{
                "gender": sex,
                "name": peo_now.name,
                "first_name": peo_now.first_name,
                "middle_name": peo_now.middle_name,
                "last_name": peo_now.last_name,
                "birthday": f"{str(peo_now.birth_date)[:-9]}-{str(peo_now.death_date)[:-9]}",
                "avatar": avatar_path
            },
            "rels":{
                "spouses": [],
                "children": [],
            }
        }
        # mates
        if peo_now.mate and str(peo_now.mate) not in peo_info["rels"]["spouses"]:
            peo_info["rels"]["spouses"].append(str(peo_now.mate))
        try:
            mates = People.objects.filter(mate=str(peo_now.id))
            for mate in mates:
                if str(mate.id) not in peo_info["rels"]["spouses"]:
                    peo_info["rels"]["spouses"].append(str(mate.id))
        except:
            pass
        for i in peo_info["rels"]["spouses"]:
            if i not in check:
                peo_obj_list.append(People.objects.get(id=int(i)))

        # children
        if peo_now.kids:
            for kid in peo_now.kids:
                if str(kid) not in peo_info["rels"]["children"]:
                    peo_info["rels"]["children"].append(str(kid))
        try:
            kids = People.objects.filter(father=str(peo_now.id))
            for kid in kids:
                if str(kid.id) not in peo_info["rels"]["children"]:
                    peo_info["rels"]["children"].append(str(kid.id))
        except:
            pass
        try:
            kids = People.objects.filter(mother=str(peo_now.id))
            for kid in kids:
                if str(kid.id) not in peo_info["rels"]["children"]:
                    peo_info["rels"]["children"].append(str(kid.id))
        except:
            pass
        for children in peo_info["rels"]["children"]:
            if children not in check:
                peo_obj_list.append(People.objects.get(id=int(children)))
            if back_check.get(children):
                back_check[children].append(peo_now.id)
            else:
                back_check[children]=[peo_now.id]
        # father & mother
        if peo_now.father:
            peo_info["rels"]["father"]=str(peo_now.father)
        if peo_now.mother:
            peo_info["rels"]["mother"]=str(peo_now.mother)
        if (not peo_now.father) and back_check.get(str(peo_now.id)):
            for i in back_check[str(peo_now.id)]:
                if not peo_info["rels"].get("mother"):
                    peo_info["rels"]["father"]=str(i)
                    break
                elif str(i)!=peo_info["rels"]["mother"]:
                    peo_info["rels"]["father"]=str(i)
                    break
        if (not peo_now.mother) and back_check.get(str(peo_now.id)):
            for i in back_check[str(peo_now.id)]:
                if (not peo_info["rels"].get("father")):
                    peo_info["rels"]["mother"]=str(i)
                    break
                elif str(i)!=peo_info["rels"]["father"]:
                    peo_info["rels"]["mother"]=str(i)
                    break
        if peo_info["rels"].get("mother") and peo_info["rels"]["mother"] not in check:
                peo_obj_list.append(People.objects.get(id=int(peo_info["rels"]["mother"])))
        if peo_info["rels"].get("father") and peo_info["rels"]["father"] not in check:
                peo_obj_list.append(People.objects.get(id=int(peo_info["rels"]["father"])))
        out_data.append(peo_info)
        root = out_data[0]
        out_data.remove(root)
        out_data.sort(key= lambda x: x["data"]["birthday"])
        out_data.insert(0, root)
    return out_data


def pic_info(request, path):
    context = {}
    context["path"] = path
    image_obj = image_db.objects.get(path=path)
    face_obj = FaceImage.objects.filter(image=image_obj)
    context['namelist'] = []
    context['token_time'] = str(image_obj.token_time).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
    context['info'] = image_obj.info
    context['title'] = image_obj.title
    context["use_baidu"] = image_obj.use_baidu
    context["loc_x"] = image_obj.loc_x
    context["loc_y"] = image_obj.loc_y
    context["loc_info"] = image_obj.loc_info
    if os.path.exists(os.path.join(BASE_DIR,"statics","up_sample",path)):
        context['origin'] = "up_sample/"+path
    else:
        context['origin'] = ""
    count = 0
    time_range = set()
    for face in face_obj:
        name = face.name.name
        num = face.path[face.path.find('-') + 1:face.path.rfind('.')]
        id = face.name.id
        context['namelist'].append([num, name, id])
        located_time = face.name.located_time
        if located_time:
            located_time = located_time.split(' ')
            temp = set()
            if count == 0:
                for i in located_time:
                    count = 1
                    if not i:
                        continue
                    start_time, end_time = i.split('-')
                    for k in range(eval(start_time), eval(end_time)):
                        time_range.add(k)
            else:
                for i in located_time:
                    if not i:
                        continue
                    start_time, end_time = i.split('-')
                    for k in range(eval(start_time), eval(end_time)):
                        temp.add(k)
                time_range = temp & time_range
        else:
            birth = str(face.name.birth_date)[:-9].replace('-', '')
            death = str(face.name.death_date)[:-9].replace('-', '')
            temp = set()
            if birth and death:
                if count == 0:
                    count = 1
                    for k in range(eval(birth), eval(death)):
                        time_range.add(k)
                else:
                    for k in range(eval(birth), eval(death)):
                        temp.add(k)
                    time_range = temp & time_range


    time_range = list(time_range)
    time_range.sort()
    time_out = []
    start = 0
    try:
        for i in range(len(time_range)):
            if start == 0:
                start = time_range[i]
            elif i == len(time_range) - 1 or time_range[i + 1] != time_range[i] + 1:
                time_out.append([start, time_range[i]+1])
                start = 0
            elif time_range[i + 1] == time_range[i] + 1:
                continue
    except:
        pass
    context['time_range'] = time_out
    context['random'] = time.time()

    return render(request, "pic_info.html", context)


def pic_info_edit(request, path):
    image_obj = image_db.objects.get(path=path)
    image_obj.info = request.POST["info"]
    image_obj.title = request.POST["title"]
    image_obj.loc_info = request.POST["loc_info"]
    image_obj.loc_x = request.POST["loc_x"]
    image_obj.loc_y= request.POST["loc_y"]
    if request.POST['token_time']:
        image_obj.token_time = request.POST["token_time"]
    else:
        image_obj.token_time = None
    image_obj.save()
    messages.error(request, path + "已修改")
    return HttpResponseRedirect("/pic_info/%s" % path)


def user_view(request):
    try:
        context = {'info': request.GET['message']}
    except:
        context = {'info': "请先登录!"}
    return render(request, "user.html", context)


def user_oper(request):
    username = request.POST['username']
    password = request.POST['password']
    operat = request.POST['operat']
    if operat == "login":
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            # Redirect to a success page.
            messages.error(request, "登陆成功！")
            return HttpResponseRedirect('index')
        else:
            # Return an 'invalid login' error message.
            messages.error(request, "用户名或密码错误！")
            return HttpResponseRedirect('user?message=用户名或密码错误！')
    elif operat == "register":
        try:
            user = User.objects.create_user(username=username, password=password)
        except:
            messages.error(request, "用户名已存在！")
            return HttpResponseRedirect('user?message=用户名已存在！')
        return HttpResponseRedirect('user?message=注册成功，请登陆！')


def logout_view(request):
    auth.logout(request)
    messages.error(request, "用户已登出！")
    return HttpResponseRedirect('index')


def demo(request):
    return render(request, 'demo.html')


def baidu_upload(request):
    faces = FaceImage.objects.all()
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (
    api_key, secret_key)
    response = requests.get(host)
    if response:
        access_token = response.json()["access_token"]
    else:
        return 0
    for face in faces:
        pic_path = face.path
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add"
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        png = open(os.path.join(BASE_DIR, "cv", "model_image", face.path), 'rb')
        res = png.read()
        png.close()
        image = base64.b64encode(res).decode("ascii")
        params = '{"image":"%s","image_type":"BASE64","group_id":"admin","user_id":"%d"}' % (image, face.name.id)
        headers = {'content-type': 'application/json'}
        response = requests.post(request_url, data=params, headers=headers)
        print(response.json())

        time.sleep(1)
        if response.json()["error_msg"] != "SUCCESS":
            print(response.json()["error_msg"])
        else:
            face.token = response.json()["result"]["face_token"]
            face.logid = response.json()["log_id"]
            face.save()
    return render(request, 'index.html')


def recog_again(request, path):
    try:
        try:
            return_dic = FaceRecognition.face_matchng(os.path.join(BASE_DIR, "upload", path), request, 0.4)
        except:
            return_dic = FaceRecognition.face_matchng(os.path.join(BASE_DIR, "cv", "model_image", path), request, 0.4)
    except:
        messages.error(request, '您上传的文件不是合法的图片文件或者图片中没有可分辨的人脸！')
        return HttpResponseRedirect('/recognition')
    context = {}
    if return_dic == "no_face_error":
        messages.error(request, '无法识别出人脸，请上传清晰的人脸图片')
        return HttpResponseRedirect('/recognition')
    context['path'] = return_dic['path']
    shutil.copy(os.path.join(BASE_DIR, "statics", "temp_image", path), os.path.join(BASE_DIR, "cv", "model_image", path))
    context['xls_path'] = return_dic['path'][:return_dic['path'].rfind('.')] + '.xls'
    context['result'] = return_dic['result']
    return render(request, 'recognition_again.html', context)


def upload_again(request):
    if request.method == 'POST':
        name = request.POST["name"]
        if name == "":
            return HttpResponse("补录取消")
        if name == "random":
            name = "无名氏"+str(time.time()).replace('.', '-')
        num = request.POST["num"]
        path = request.POST["path"]
        path = path[path.rfind("/")+1:]
        face_path = os.path.join(BASE_DIR, "statics", "temp_image",
                                 path[0:path.rfind('.')] + '-' + str(num) + path[path.rfind("."):])
        # return HttpResponseRedirect('/index')
        try:
            info = FaceRecognition.dict_add_id(face_path, name)
        except:
            info, id = FaceRecognition.dict_add(face_path, name)
        if info == 1:
            return HttpResponse(name+"补录成功")
        else:
            return HttpResponse(info)


@method_decorator(csrf_exempt)
def name2id_researcher(request):
    result_list = ""
    name = request.POST["name"]
    peo_objs = People.objects.filter(Q(name__icontains=name) |
                                    Q(first_name__icontains=name) |
                                    Q(middle_name__icontains=name) |
                                    Q(last_name__icontains=name)).distinct()
    for peo in peo_objs:
        result_list += r'<li role="presentation"><a role="menuitem" tabindex="-1" href="/facelist/%d">%d：%s</a></li>' \
                       % (peo.id, peo.id, peo.name)
    return JsonResponse(result_list, safe=False)


@method_decorator(csrf_exempt)
def peo_obj_ini(request):
    name = request.POST["name"]
    peo_obj = People(name=name)
    peo_obj.save()
    return JsonResponse(peo_obj.id, safe=False)


@method_decorator(csrf_exempt)
def id2name_researcher(request):
    id = request.POST["id"]
    peo_objs = People.objects.get(id=id)
    return JsonResponse({"id":id, "name":peo_objs.name})


@method_decorator(csrf_exempt)
def image_obj_ini(request):
    file_name = request.POST["file_name"]
    face_count = request.POST["face_count"]
    img_objs = image_db(path=file_name,count=face_count,use_baidu=True)
    img_objs.save()
    return JsonResponse({"file_name":file_name, "id":img_objs.id})


@method_decorator(csrf_exempt)
def face_obj_ini(request):
    image_id = request.POST["image_id"]
    name_id = request.POST["name_id"]
    path = request.POST["path"]
    token = request.POST["token"]
    uploadtime = path[path.find('@') + 1:path.rfind('-')]
    uploadtime = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(eval(uploadtime)))
    face_objs = FaceImage(path=path,upload_time=uploadtime,token=token,
                          image_id=image_id, name_id=name_id)
    face_objs.save()
    return JsonResponse({"file_name":path})


from random import randrange
from pyecharts.charts import Graph
from pyecharts import options as opts
import json


def social_graph(request, name):
    context = {"name": name}
    return render(request, 'social_graph.html', context)


def social_info(request, person):
    nodes = []
    links = []
    name = []
    if person:
        return social_info_person(request, person)
    else:
        group_photos = image_db.objects.all()
    for group_photo in group_photos:
        faces = FaceImage.objects.filter(image=group_photo)
        for face in faces:
            if face.name.name in name:
                nodes[name.index(face.name.name)]["symbolSize"] += 5
            else:
                name.append(face.name.name)
                en_name = ""
                if face.name.first_name:
                    en_name = face.name.first_name + " "
                if face.name.middle_name:
                    en_name = en_name + face.name.middle_name + " "
                if face.name.last_name:
                    en_name = en_name + face.name.last_name
                nodes.append({"name": face.name.name, "symbolSize": 5})
        for face_i in faces:
            for face_j in faces:
                links.append({"source": face_i.name.name, "target": face_j.name.name, "value": group_photo.path})
    data = (
        Graph()
            .add("", nodes, links, repulsion=8000, is_draggable=True)
            .set_global_opts(title_opts=opts.TitleOpts(title="人员关系图", subtitle="合照社交关系可视化"),
                             toolbox_opts=opts.ToolboxOpts(is_show=True))
            .dump_options_with_quotes()
    )
    data = json.loads(data)
    data = {
        "code": 200,
        "msg": "success",
        "data": data,
    }
    return JsonResponse(data)


def social_info_person(request, person):
    nodes = []
    links = []
    name = []
    for group_photo in FaceImage.objects.filter(name=People.objects.get(name=person)):
        group_photo = group_photo.image
        faces = FaceImage.objects.filter(image=group_photo)
        for face in faces:
            if face.name.name in name:
                continue
            else:
                name.append(face.name.name)
                en_name = ""
                if face.name.first_name:
                    en_name = face.name.first_name + " "
                if face.name.middle_name:
                    en_name = en_name + face.name.middle_name + " "
                if face.name.last_name:
                    en_name = en_name + face.name.last_name
                nodes.append({"name": face.name.name, "symbolSize": 20})
        for face_i in faces:
            for face_j in faces:
                links.append({"source": face_i.name.name, "target": face_j.name.name, "value": group_photo.path})
    data = (
        Graph()
            .add("", nodes, links, repulsion=8000, is_draggable=True)
            .set_global_opts(toolbox_opts=opts.ToolboxOpts(is_show=True))
            .dump_options_with_quotes()
    )
    data = json.loads(data)
    data = {
        "code": 200,
        "msg": "success",
        "data": data,
    }
    return JsonResponse(data)


def data_transfer(request):
    for i in People.objects.all():
        if i.mate:
            try:
                mate = People.objects.filter(name=i.mate)[0]
                i.mate = mate.id
                i.save()
            except:
                try:
                    int(i.mate)
                except:
                    new_obj = People(name=i.mate)
                    new_obj.save()
                    i.mate = new_obj.id
                    i.save()

        if i.father:
            try:
                father = People.objects.filter(name=i.father)[0]
                i.father = father.id
                i.save()
            except:
                try:
                    int(i.father)
                except:
                    new_obj = People(name=i.father)
                    new_obj.save()
                    i.father = new_obj.id
                    i.save()
        if i.mother:
            try:
                mother = People.objects.filter(name=i.mother)[0]
                i.mother = mother.id
                i.save()
            except:
                try:
                    int(i.mother)
                except:
                    new_obj = People(name=i.mother)
                    new_obj.save()
                    i.mother = new_obj.id
                    i.save()
        if i.kids:
            temp_list = []
            for kid in i.kids:
                try:
                    temp = People.objects.filter(name=kid)[0]
                    temp_list.append(temp.id)
                except:
                    try:
                        int(kid)
                        temp_list.append(int(kid))
                    except:
                        new_obj = People(name=kid)
                        new_obj.save()
                        temp_list.append(new_obj.id)
            i.kids = temp_list
            i.save()
    return HttpResponse("数据转换完成")


def person_check(peo_obj):
    if len(Location.objects.filter(belongs_to=peo_obj.id)):
        return True
    else:
        return False

def info2excel(request):
    index_dict = ["起点","起点id","终点","终点id","边权","角色","备注"]
    data = []
    error = set()
    for peo_obj in People.objects.all():
        if not person_check(peo_obj):
            continue
        # 亲缘关系
        print(peo_obj.id,peo_obj)
        done = set()
        list_5 = set()
        if peo_obj.mother:
            try:
                int(peo_obj.mother)
                list_5.add(peo_obj.mother)
            except:
                error.add(peo_obj.id)
        if peo_obj.father:
            try:
                int(peo_obj.father)
                list_5.add(peo_obj.father)
            except:
                error.add(peo_obj.id)
        if peo_obj.mate:
            try:
                int(peo_obj.mate)
                list_5.add(peo_obj.mate)
            except:
                error.add(peo_obj.id)
        for i in People.objects.filter(mother=peo_obj.id):
            list_5.add(i.id)
        for i in People.objects.filter(father=peo_obj.id):
            list_5.add(i.id)
        for i in People.objects.filter(mate=peo_obj.id):
            list_5.add(i.id)
        if peo_obj.kids:
            for i in peo_obj.kids:
                list_5.add(i)
        # 普通亲戚
        list_4 = set()
        peo_obj_list = [peo_obj]
        path = os.path.join(BASE_DIR, 'statics', 'temp_image', str(time.time()) + '.txt')
        fp = open(path, "w+", encoding="utf-8")
        fp.close()
        check = [peo_obj]
        written = set()
        # bfs遍历
        while peo_obj_list:
            peo_now = peo_obj_list[0]
            # print(peo_now)
            # 将孩子加入队列
            kids_list = peo_now.kids
            if kids_list:
                for kid in kids_list:
                    try:
                        People.objects.get(id=kid)
                        if People.objects.get(id=kid) not in check:
                            peo_obj_list.insert(peo_obj_list.index(peo_now) + 1, People.objects.get(id=kid))
                            check.insert(check.index(peo_now) + 1, People.objects.get(id=kid))
                    except:
                        pass
                    finally:
                        pass

            # 将配偶加进队列
            try:
                # print(People.objects.get(name=peo_now.mate))
                if People.objects.get(name=peo_now.mate) not in check:
                    # peo_obj_list.insert(peo_obj_list.index(peo_now)+1, People.objects.get(name=peo_now.mate))
                    check.insert(check.index(peo_now) + 1, People.objects.get(name=peo_now.mate))
            except:
                pass
            # 将父亲加入队列
            try:
                People.objects.get(id=peo_now.father)
                if People.objects.get(id=peo_now.father) not in check:
                    peo_obj_list.insert(peo_obj_list.index(peo_now), People.objects.get(id=peo_now.father))
                    check.insert(check.index(peo_now), People.objects.get(id=peo_now.father))
            except:
                pass
            finally:
                pass
            # 将母亲加入队列
            try:
                People.objects.get(id=peo_now.mother)
                if People.objects.get(id=peo_now.mother) not in check:
                    # peo_obj_list.insert(peo_obj_list.index(peo_now), People.objects.get(id=peo_now.mother))
                    check.insert(check.index(peo_now), People.objects.get(id=peo_now.mother))
            except:
                pass
            finally:
                pass
            peo_obj_list.remove(peo_now)
        for i in check:
            list_4.add(i.id)
        # 密切伙伴
        list_3 = set()
        list_3_from = dict()
        if peo_obj.edu:
            for edu in peo_obj.institute.split(";"):
                if edu == "":
                    continue
                for i in People.objects.filter(edu__contains=edu):
                    list_3.add(i.id)
                    if list_3_from.get(str(i.id)):
                        list_3_from[str(i.id)].append(edu)
                    else:
                        list_3_from[str(i.id)] = [edu]
        if peo_obj.institute:
            for institute in peo_obj.institute.split(";"):
                if institute == "":
                    continue
                for i in People.objects.filter(institute__contains=institute):
                    list_3.add(i.id)
                    if list_3_from.get(str(i.id)):
                        list_3_from[str(i.id)].append(institute)
                    else:
                        list_3_from[str(i.id)] = [institute]
        # 轻度社交
        list_2 = set()
        list_2_from = dict()
        for group_photo in FaceImage.objects.filter(name=People.objects.get(id=peo_obj.id)):
            group_photo = group_photo.image
            faces = FaceImage.objects.filter(image=group_photo)
            for face in faces:
                list_2.add(face.name.id)
                if list_2_from.get(str(face.name.id)):
                    list_2_from[str(face.name.id)].append(face.image.path)
                else:
                    list_2_from[str(face.name.id)] = [face.image.path]
        for i in list_5:
            peo_info = People.objects.get(id=i)
            if not person_check(peo_info):
                continue
            data.append([peo_obj.name,peo_obj.id,peo_info.name, i, 5, "亲缘关系", "近代直系亲属"])
            done.add(i)
        for i in list_4:
            peo_info = People.objects.get(id=i)
            if i in done or i==peo_obj.id or not person_check(peo_info):
                continue
            data.append([peo_obj.name, peo_obj.id, peo_info.name, i, 4, "普通亲戚", "普通亲属"])
            done.add(i)
        for i in list_3:
            peo_info = People.objects.get(id=i)
            if i in done or i==peo_obj.id or not person_check(peo_info):
                continue
            data.append([peo_obj.name, peo_obj.id, peo_info.name, i, 3, "密切伙伴", str(list_3_from[str(i)])])
            done.add(i)
        for i in list_2:
            peo_info = People.objects.get(id=i)
            if i in done or i==peo_obj.id or not person_check(peo_info):
                continue
            data.append([peo_obj.name, peo_obj.id, peo_info.name, i, 2, "轻度社交", str(list_2_from[str(i)])])
            done.add(i)
    data.append([str(error)])
    df = pd.DataFrame(data,columns=index_dict)
    excel_path = os.path.join(BASE_DIR,"statics", "temp_image", str(time.time())+".xlsx")
    df.to_excel(excel_path)
    np_arr = np.array(df)
    np_arr = np.insert(np_arr,0,1,axis=1)
    id_set = set()
    link_dict = set()
    nodes = []
    links = []
    for i in np_arr:
        if i[1] not in id_set:
            nodes.append({"name": i[1], "value": i[2], "symbolSize": 20,"category":0})
            id_set.add(i[1])
        if i[3] not in id_set:
            nodes.append({"name": i[3], "value": i[4], "symbolSize": 20, "category":0})
            id_set.add(i[3])
        if i[5] == 3:
            i[7] = eval(i[7])
            if i[7][0] not in id_set:
                nodes.append({"name": i[7][0], "symbolSize": 20, "category":1})
                id_set.add(i[7][0])
            if (i[1], i[7][0]) not in link_dict:
                link_dict.add((i[1], i[7][0]))
                links.append({"source": i[1], "target": i[7][0], "value": i[5] * i[5]})
                count = 0
                for j in nodes:
                    if j["name"] == i[1] or j["name"] == i[7][0]:
                        j["symbolSize"] += 0.2
                        count += 1
                    if count >= 2:
                        break
        elif (i[1], i[3]) not in link_dict:
            link_dict.add((i[1], i[3]))
            links.append({"source": i[1], "target": i[3], "value": i[5] * i[5]})
            count = 0
            for j in nodes:
                if j["name"] == i[1] or j["name"] == i[3]:
                    j["symbolSize"] += 0.2
                    count += 1
                if count >= 2:
                    break
    obj = (
        Graph()
        .add("鼓岭房主", nodes, links, repulsion=8000, is_draggable=True,categories=[{"name":"person"},{"name":"institute"}])
        .set_global_opts(title_opts=opts.TitleOpts(title="人员关系图", subtitle="社交关系可视化"),
                         toolbox_opts=opts.ToolboxOpts(is_show=True))
    )
    html_path = os.path.join(BASE_DIR,"statics", "temp_image", str(time.time())+".html")
    obj.render(html_path)
    print(len(id_set))
    print(len(link_dict) / 2)
    return HttpResponse('<a href="/static/temp_image/%s">excel数据</a><br><a href="/static/temp_image/%s">图表</a>'
                        % (os.path.basename(excel_path), os.path.basename(html_path)))