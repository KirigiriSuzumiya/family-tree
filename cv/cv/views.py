from django.http import HttpResponse
from django.shortcuts import render
import os
import time
from pathlib import Path
from .codes import FaceRecognition, FaceExtractor
from .settings import BASE_DIR
from dbmodel.models import FaceImage, People
import subprocess
import re


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
    try:
        face_num = FaceExtractor.extractor(img_path)
    except:
        return HttpResponse("您上传的文件不是合法的图片文件"+r'<br><a href="/faceupload">返回</a>')

    context = {}
    context["upload_states"] = "上传成功！共找到%d个人脸" % face_num
    context["total_path"] = os.path.join("temp_image", pic_path[0:pic_path.rfind('.')]+'-0'+pic_path[pic_path.rfind("."):])
    path_list = []
    for i in range(face_num):
        path_list.append(os.path.join("temp_image", pic_path[0:pic_path.rfind('.')]+'-'+str(i+1)+pic_path[pic_path.rfind("."):]))
    context["path_list"] = path_list
    return render(request, 'NameUpload.html', context)


def name_upload(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    namelist = ''
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
            namelist += name+' '
        if namelist == '':
            namelist += "没有人脸"
    return HttpResponse(namelist+"已上传"+r'<br><a href="/faceupload">返回</a>')


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
    context['last_name'] = name_obj.last_name
    context['mate'] = name_obj.mate
    context['father'] = name_obj.father
    context['mother'] = name_obj.mother
    context['kids'] = name_obj.kids
    context['family'] =[]
    face_obj_list = FaceImage.objects.filter(name=name_obj)
    count = 0
    for face_obj in face_obj_list:
        path = '/static/'+face_obj.path
        upload_time = face_obj.upload_time
        count = (count+1) % 4
        context['facelist'].append([upload_time, path, count])

    context["familytreepath"], family = familytree(request, name)["path"], familytree(request, name)["check"]
    for i in family:
        context["family"].append(i.name)
    return render(request, 'facelist.html', context)


def face_edit(request, re_name):
    people_obj = People.objects.get(name=re_name)
    people_obj.first_name = request.POST['first_name']
    people_obj.last_name = request.POST['last_name']
    people_obj.mate = request.POST['mate']
    people_obj.father = request.POST['father']
    people_obj.mother = request.POST['mother']
    people_obj.kids = request.POST['kids']
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
    fp = open(path, "w+")
    fp.close()
    check = set()
    # bfs遍历
    while peo_obj_list:
        print(check)
        peo_now = peo_obj_list[0]
        couple_obj = re_familytree(peo_now, path)
        for obj in couple_obj:
            check.add(obj)
        del peo_obj_list[0]
        # 将父亲加入队列
        try:
            People.objects.get(name=peo_now.father)
            if People.objects.get(name=peo_now.father) not in check:
                peo_obj_list.append(People.objects.get(name=peo_now.father))
        except:

            # 将母亲加入队列
            try:
                People.objects.get(name=peo_now.mother)
                if People.objects.get(name=peo_now.mother) not in check:
                    peo_obj_list.append(People.objects.get(name=peo_now.mother))
            except:
                pass
            finally:
                pass
        finally:
            pass

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
    shell = 'python ' + os.path.join(BASE_DIR, 'cv', 'codes', 'familytreemaker.py ')+path
    gra_path = path[:path.rfind('.')]
    fp = open(gra_path, 'w+')
    subprocess.run(shell, stdout=fp, shell=True)
    fp.close()
    os.remove(path)
    shell = "dot -Tpng " + gra_path+" -O"
    subprocess.run(shell,  shell=True)
    os.remove(gra_path)
    context={}
    context["name"] = name
    context["path"] = "temp_image/"+os.path.basename(gra_path)+".png"
    context["check"] = check
    return context


def re_familytree(people_obj, path):
    fp = open(path, 'a', encoding="utf-8")
    couple_obj = []
    # 为配偶写txt
    try:
        mate = People.objects.get(name=people_obj.mate)
        fp.write(mate.name + "(id=%d)" % mate.custom_id + "\n")
        couple_obj.append(mate)
    except:
        mate = people_obj.mate
        if not mate:
            fp.close()
            return [people_obj]
        fp.write(mate+"\n")

    # 为自己写txt
    name = people_obj.name
    fp.write(name+"(id=%d)" % people_obj.custom_id+"\n")
    couple_obj.append(people_obj)
    # 为后代写txt
    kids_list = people_obj.kids
    if kids_list:
        for kid in kids_list:
            try:
                People.objects.get(name=kid)
                fp.write("\t"+kid+"(id=%d)" % People.objects.get(name=kid).custom_id+"\n")
            except:
                fp.write("\t" + kid + "\n")
    fp.write("\n")
    fp.close()
    return couple_obj
