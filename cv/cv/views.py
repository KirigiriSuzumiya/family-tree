from click import style
from django.http import HttpResponse
from django.shortcuts import render
import os
import time
from pathlib import Path
from .codes import FaceRecognition, FaceExtractor
from .settings import BASE_DIR
from dbmodel.models import FaceImage, People
from dbmodel.models import Image as image_db
import subprocess
import re
# -*- coding: CP936 -*-

def always():
    context = {
               "info": FaceRecognition.initialing(),
               "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
               "call": "请不要上传奇奇怪怪的东西！人在做，我在看，硬盘在存!"
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
    # try:
    face_num = FaceExtractor.extractor(img_path)
    # except:
    #     return HttpResponse("您上传的文件不是合法的图片文件"+r'<br><a href="/faceupload">返回</a>')

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
            name = request.POST['name'+str(i+1)]
            i += 1
            if name == '':
                continue
            FaceRecognition.dict_add(path, name)
            namelist.append(name)
    context = {"namelist" : namelist}
    return render(request, "info.html",context)


def recognition(request):
    context = always()
    return render(request, 'recognition.html', context)


def recognition_upload(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    submit_pic = request.FILES.get('pic')
    tolerance = eval(request.POST['tolerance'])/10
    pic_suffix = submit_pic.name.split(".")[-1]  # 获取后缀
    pic_path = os.path.join(str(time.time()) + "." + pic_suffix)  # 构造文件路径
    with open(os.path.join(BASE_DIR, "upload", pic_path), "wb") as f:
        for line in submit_pic:
            f.write(line)
    img_path = os.path.join(BASE_DIR, "upload", pic_path)
    try:
        return_dic = FaceRecognition.face_matchng(img_path, tolerance)
    except:
        return HttpResponse("您上传的文件不是合法的图片文件" + r'<br><a href="/recognition">返回</a>')
    context={}
    if return_dic == "no_face_error":
        return HttpResponse("无法识别出人脸，请上传清晰的人脸图片" + r'<br><a href="/recognition">返回</a>')
    context['path'] = return_dic['path']
    context['xls_path'] = return_dic['path'][:return_dic['path'].rfind('.')]+'.xls'
    context['result'] = return_dic['result']
    return render(request, 'recognition_result.html', context)


def index(request):
    context = always()
    return render(request, 'index.html', context)


def namelist(request):
    context = always()
    context['namelist'] = []
    names = People.objects.all()
    count = 1
    for i in names:
        name = i.name
        if FaceImage.objects.filter(name=i):
            pic_obj = FaceImage.objects.filter(name=i)[0]
            upload_time = pic_obj.upload_time
            path = '/static/' + pic_obj.path
        else:
            pic_obj = 'none'
            upload_time = 'none'
            path = ''
        context['namelist'].append([name, upload_time, path, pic_obj, count])
        count = (count+1) % 4
    return render(request, 'namelist.html', context)


def facelist(request, name):
    context = {}
    context['name'] = name
    context['facelist'] = []
    name_obj = People.objects.filter(name=name)[0]
    context['first_name'] = name_obj.first_name
    context['middle_name'] = name_obj.middle_name
    context['last_name'] = name_obj.last_name
    context['sex'] = name_obj.sex
    context['birth_date'] = str(name_obj.birth_date).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
    context['death_date'] = str(name_obj.death_date).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
    context['xing'] = name_obj.xing
    context['ming'] = name_obj.ming

    context['mate'] = name_obj.mate
    context['father'] = name_obj.father
    context['mother'] = name_obj.mother
    context['kids'] = name_obj.kids
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
    context['family'] =[]
    face_obj_list = FaceImage.objects.filter(name=name_obj)
    context['first_pic'] = '/static/'+face_obj_list[0].path
    count = 0
    for face_obj in face_obj_list:
        path = '/static/'+face_obj.path
        upload_time = face_obj.upload_time
        count = (count+1) % 4
        re_path = face_obj.image.path
        context['facelist'].append([upload_time, path, count,re_path])

    context["familytreepath"], family = familytree(request, name)["path"], familytree(request, name)["check"]
    for i in family:
        context["family"].append(i.name)
    return render(request, 'facelist.html', context)


def face_edit(request, re_name):
    people_obj = People.objects.get(name=re_name)
    people_obj.name = request.POST['name']
    people_obj.first_name = request.POST['first_name']
    people_obj.middle_name = request.POST['middle_name']
    people_obj.last_name = request.POST['last_name']
    # people_obj.sex = request.POST['sex']
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
        people_obj.kids = eval(request.POST['kids'])
    except:
        people_obj.kids = request.POST['kids']

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
    people_obj.save()
    return HttpResponse(re_name+"已修改"+r'<br><a href="/facelist/%s">返回</a>' % people_obj.name)


def edit_pic(request, path):
    npy_path = os.path.join(BASE_DIR, 'cv', 'model')
    img_path = os.path.join(BASE_DIR, 'cv', 'model_image')
    path = os.path.basename(path)
    img_obj = FaceImage.objects.filter(path=path)
    img_obj.delete()
    os.remove(os.path.join(npy_path, path[:path.rfind('.')]+'.npy'))
    os.remove(os.path.join(img_path, path))
    return HttpResponse(path+"已删除"+r'<br><a href="/namelist">返回</a>')


def familytree(request, name):
    people_obj = People.objects.get(name=name)
    peo_obj_list = [people_obj]
    path = os.path.join(BASE_DIR, 'statics', 'temp_image', str(time.time())+'.txt')
    fp = open(path, "w+", encoding="utf-8")
    fp.close()
    check = set()
    # bfs遍历
    while peo_obj_list:
        # print(check)
        peo_now = peo_obj_list[0]
        # 将孩子加入队列
        kids_list = peo_now.kids
        if not kids_list:
            continue
        for kid in kids_list:
            try:
                People.objects.get(name=kid)
                if People.objects.get(name=kid) not in check:
                    peo_obj_list.append(People.objects.get(name=kid))
            except:
                pass
            finally:
                pass

        # 将配偶加进队列
        try:
            People.objects.get(name=peo_now.mate)
            if People.objects.get(name=peo_now.mate) not in check:
                peo_obj_list.append(People.objects.get(name=peo_now.mate))
                re_peo_now = People.objects.get(name=peo_now.mate)
                try:
                    People.objects.get(name=re_peo_now.father)
                    if People.objects.get(name=re_peo_now.father) not in check:
                        peo_obj_list.append(People.objects.get(name=re_peo_now.father))
                        if peo_obj_list[-1] not in check:
                            couple_obj = re_familytree(peo_obj_list[-1], path)
                            for obj in couple_obj:
                                check.add(obj)
                except:
                    pass
                finally:
                    pass

                # 将母亲加入队列
                try:
                    People.objects.get(name=re_peo_now.mother)
                    if People.objects.get(name=re_peo_now.father) not in check:
                        peo_obj_list.append(People.objects.get(name=re_peo_now.mother))
                        if peo_obj_list[-1] not in check:
                            couple_obj = re_familytree(peo_obj_list[-1], path)
                            for obj in couple_obj:
                                check.add(obj)
                except:
                    pass
                finally:
                    pass
        except:
            pass
        finally:
            pass

        # 将父亲加入队列
        try:
            People.objects.get(name=peo_now.father)
            if People.objects.get(name=peo_now.father) not in check:
                peo_obj_list.append(People.objects.get(name=peo_now.father))
                if peo_obj_list[-1] not in check:
                    couple_obj = re_familytree(peo_obj_list[-1], path)
                    for obj in couple_obj:
                        check.add(obj)
        except:
            pass
        finally:
            pass

        # 将母亲加入队列
        try:
            People.objects.get(name=peo_now.mother)
            if People.objects.get(name=peo_now.father) not in check:
                peo_obj_list.append(People.objects.get(name=peo_now.mother))
                if peo_obj_list[-1] not in check:
                    couple_obj = re_familytree(peo_obj_list[-1], path)
                    for obj in couple_obj:
                        check.add(obj)
        except:
            pass
        finally:
            pass


        peo_now = peo_obj_list[-1]
        if peo_now not in check:
            couple_obj = re_familytree(peo_now, path)
            for obj in couple_obj:
                check.add(obj)
        del peo_obj_list[-1]

    shell = 'python ' + os.path.join(BASE_DIR, 'cv', 'codes', 'familytreemaker.py ')+path
    gra_path = path[:path.rfind('.')]
    fp = open(gra_path, 'w+', encoding="utf-8")
    p = subprocess.run(shell, stdout=subprocess.PIPE, shell=True)
    temp = p.stdout
    temp = temp.decode('cp936')
    fp.write(temp)
    fp.close()
    # os.remove(path)
    shell = "dot -Tpng " + gra_path+" -O"
    subprocess.run(shell,  shell=True)
    # os.remove(gra_path)
    context={}
    context["name"] = name
    context["path"] = "temp_image/"+os.path.basename(gra_path)+".png"
    context["check"] = check
    return context


def re_familytree(people_obj, path):
    # print(people_obj)
    fp = open(path, 'a', encoding="utf-8")
    couple_obj = []
    # 为配偶写txt
    try:
        mate = People.objects.get(name=people_obj.mate)
        fp.write(mate.name + "(id=%d)" % mate.id + "\n")
        couple_obj.append(mate)
    except:
        mate = people_obj.mate
        if not mate:
            fp.close()
            return [people_obj]
        fp.write(mate+"\n")

    # 为自己写txt
    name = people_obj.name
    fp.write(name + "(id=%d)" % people_obj.id+"\n")
    couple_obj.append(people_obj)
    # 为后代写txt
    kids_list = people_obj.kids
    if kids_list:
        for kid in kids_list:
            try:
                People.objects.get(name=kid)
                fp.write("\t"+kid+"(id=%d)" % People.objects.get(name=kid).id+"\n")
            except:
                fp.write("\t" + kid + "\n")
    fp.write("\n")
    fp.close()
    return couple_obj


def pic_info(request, path):
    context={}
    context["path"] = path
    image_obj = image_db.objects.get(path=path)
    face_obj = FaceImage.objects.filter(image=image_obj)
    context['namelist'] = []
    context['token_time'] = str(image_obj.token_time).replace('年', '-').replace('月', '-').replace('日', '-').replace(' ', 'T')
    context['info'] = image_obj.info
    context['title'] = image_obj.title
    for face in face_obj:
        name = face.name.name
        num = face.path[face.path.find('-')+1:face.path.rfind('.')]
        context['namelist'].append([num, name])
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
    return HttpResponse(path+"已修改"+r'<br><a href="/pic_info/%s">返回</a>' % path)
