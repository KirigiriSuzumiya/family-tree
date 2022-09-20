import base64

import requests
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
import os
import time
from pathlib import Path
from .codes import FaceRecognition, FaceExtractor
from .settings import BASE_DIR
from dbmodel.models import FaceImage, People
from dbmodel.models import Image as image_db
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
import subprocess
from pypinyin import lazy_pinyin
from django.core.paginator import Paginator
import re


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
            info = FaceRecognition.dict_add(path, name)
            if info != 1:
                messages.error(request, info)
                return HttpResponseRedirect('/faceupload')
            namelist.append(name)
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
        names = image_db.objects.filter(title__icontains=request.POST["search"])
    else:
        names = image_db.objects.all()
    current_num = int(request.GET.get("page", 1))
    context = always()
    list_pic = []
    count = 1
    for i in names:
        name = i.path
        if i.title:
            name = i.title
        path =i.path
        number = i.count
        relate = len(FaceImage.objects.filter(image=i))
        if relate == 0:
            continue
        list_pic.append([name, path, number, count, relate])
        count = (count + 1) % 2
    paginator = Paginator(list_pic, 10)
    context['piclist'] = paginator.page(current_num)
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


def namelist(request):
    context = always()
    namelist = []
    if request.method == "POST":
        names = People.objects.filter(Q(name__icontains=request.POST["search"])|
                                      Q(first_name__icontains=request.POST["search"]) |
                                      Q(middle_name__icontains=request.POST["search"]) |
                                      Q(last_name__icontains=request.POST["search"])).distinct()
    else:
        names = People.objects.all()
    current_num = int(request.GET.get("page", 1))
    count = 1
    for i in names:
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
            path = ''
        namelist.append([name, upload_time, path, pic_obj, count, en_name, i.id])
        count = (count + 1) % 4
    namelist.sort(key=lambda char: lazy_pinyin(char[0])[0][0])
    count = 1
    for name in namelist:
        name[4] = count
        count = (count+1) % 4
    if request.method == "POST":
        paginator = Paginator(namelist, len(namelist))
    else:
        paginator = Paginator(namelist, 24)

    try:
        context['namelist'] = paginator.page(current_num)
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
    except:
        context['namelist'] = []
        context['page_range'] = [1]
        context['current_num'] = current_num
        context['end_page'] = 1

    return render(request, 'namelist.html', context)


def facelist(request, id):
    context = {}
    name_obj = People.objects.filter(id=id)[0]
    name = name_obj.name
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
    context['loc1_x'] = name_obj.loc1_x
    context['loc1_y'] = name_obj.loc1_y
    context['loc1_info'] = name_obj.loc1_info
    context['loc2_x'] = name_obj.loc2_x
    context['loc2_y'] = name_obj.loc2_y
    context['loc2_info'] = name_obj.loc2_info
    context['loc3_x'] = name_obj.loc3_x
    context['loc3_y'] = name_obj.loc3_y
    context['loc3_info'] = name_obj.loc3_info
    context['institute'] = name_obj.institute
    context['family'] = []
    face_obj_list = FaceImage.objects.filter(name=name_obj).order_by("-image__token_time")
    context['first_pic'] = '/static/' + face_obj_list[0].path
    count = 0
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
    return render(request, 'facelist.html', context)


def face_edit(request, re_name):
    people_obj = People.objects.get(name=re_name)
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
    people_obj.mate = request.POST['mate']
    people_obj.father = request.POST['father']
    people_obj.mother = request.POST['mother']
    try:
        people_obj.kids = [i for i in request.POST['kids'].split(' ') if i != '']
    except:
        people_obj.kids = []

    people_obj.info = request.POST['info']
    people_obj.loc1_x = request.POST['loc1_x']
    people_obj.loc1_y = request.POST['loc1_y']
    people_obj.loc1_info = request.POST['loc1_info']
    people_obj.loc2_x = request.POST['loc2_x']
    people_obj.loc2_y = request.POST['loc2_y']
    people_obj.loc2_info = request.POST['loc2_info']
    people_obj.loc3_x = request.POST['loc3_x']
    people_obj.loc3_y = request.POST['loc3_y']
    people_obj.loc3_info = request.POST['loc3_info']

    people_obj.xing = request.POST['xing']
    people_obj.ming = request.POST['ming']
    people_obj.family_name = request.POST['family_name']
    people_obj.institute = request.POST['institute']
    people_obj.zi = request.POST['zi']
    people_obj.other_name = request.POST['other_name']
    people_obj.located_time = request.POST['located_time']
    people_obj.save()

    if re_name != request.POST['name'].strip():
        peo_list = People.objects.filter(mate=re_name)
        for peo in peo_list:
            peo.mate = request.POST['name'].strip()
            peo.save()
        peo_list = People.objects.filter(mother=re_name)
        for peo in peo_list:
            peo.mother = request.POST['name'].strip()
            peo.save()
        peo_list = People.objects.filter(father=re_name)
        for peo in peo_list:
            peo.father = request.POST['name'].strip()
            peo.save()
        peo_list = People.objects.all()
        for peo in peo_list:
            if not peo.kids:
                continue
            if re_name in peo.kids:
                num = peo.kids.index(re_name)
                peo.kids[num] = request.POST['name'].strip()
                peo.save()
    messages.error(request, re_name + "已修改")
    return HttpResponseRedirect("/facelist/%s" % people_obj.name)


def face_edit_info(request):
    name = request.POST["name"]
    kids = []
    try:
        people_objs = People.objects.filter(father=name)
        for people in people_objs:
            kids.append(people.name)
    except:
        pass
    try:
        people_objs = People.objects.filter(mother=name)
        for people in people_objs:
            kids.append(people.name)
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
        mate = people_objs[0].name
    except:
        pass
    parents = []
    try:
        people_objs = People.objects.all()
        for people in people_objs:
            if not people.kids:
                continue
            if name in people.kids:
                parents.append(people.name)
    except:
        pass
    return HttpResponse("补齐建议—伴侣：%s，孩子：%s，父辈：%s" % (mate, res_kids, parents))


def edit_pic(request, path):
    # client_id 为官网获取的AK， client_secret 为官网获取的SK
    # 获取access_token
    api_key = "jkyuzoYl4Cly99sEmxNMZog3"
    secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
    response = requests.get(host)
    if response:
        access_token = response.json()["access_token"]
    else:
        return 0

    # 设置请求包体
    request_url = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/face/delete"
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/json'}
    path = os.path.basename(path)
    img_obj = FaceImage.objects.filter(path=path)[0]
    params = '{"log_id":%s,"group_id":"admin","user_id":"%d","face_token":"%s"}' % (img_obj.logid, img_obj.name.id, img_obj.token)
    response = requests.post(request_url, data=params, headers=headers)
    print(response.json())
    img_path = os.path.join(BASE_DIR, 'cv', 'model_image')
    img_obj.delete()
    os.remove(os.path.join(img_path, path))
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
        # try:
        #     print(People.objects.get(name=peo_now.mate))
        #     if People.objects.get(name=peo_now.mate) not in check:
        #         peo_obj_list.insert(peo_obj_list.index(peo_now)+1, People.objects.get(name=peo_now.mate))
        #         check.insert(check.index(peo_now)+1, People.objects.get(name=peo_now.mate))
        # except:
        #     pass
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
                peo_obj_list.insert(peo_obj_list.index(peo_now), People.objects.get(id=peo_now.mother))
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
    temp = temp.decode('cp936')

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
    count = 0
    time_range = set()
    for face in face_obj:
        name = face.name.name
        num = face.path[face.path.find('-') + 1:face.path.rfind('.')]
        context['namelist'].append([num, name])
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

    return render(request, "pic_info.html", context)


def pic_info_edit(request, path):
    image_obj = image_db.objects.get(path=path)
    image_obj.info = request.POST["info"]
    image_obj.title = request.POST["title"]
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
    api_key = "jkyuzoYl4Cly99sEmxNMZog3"
    secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
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
        info = FaceRecognition.dict_add(face_path, name)
        if info == 1:
            return HttpResponse(name+"补录成功")
        else:
            return HttpResponse(info)


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
