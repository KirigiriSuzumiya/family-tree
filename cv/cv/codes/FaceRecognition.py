import time
import face_recognition
import numpy as np
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from ..settings import BASE_DIR
from dbmodel.models import FaceImage, People
from dbmodel.models import Image as image_db
info_dict = {}


def initialing():
    # 载入已保存的模型
    global info_dict
    info_dict = {}
    model_saving_path = os.path.join(BASE_DIR, 'cv', 'model')
    face_objs = FaceImage.objects.all()
    for face_obj in face_objs:
        path = face_obj.path
        name = path[:path.rfind('.')]
        path = os.path.join(model_saving_path, face_obj.path)
        info = np.load(path[:path.rfind('.')]+'.npy')
        info_dict[name] = info
    return_str = ""
    for i in info_dict.keys():
        return_str += i + ','
    return return_str

def face_matchng(path,tolerance=1):
    initialing()
    img = face_recognition.load_image_file(path)
    results = []
    names = []
    info = face_recognition.face_encodings(img)
    global info_dict
    for key, value in info_dict.items():
        result = face_recognition.face_distance(info, value)
        results.append(list(result))
        names.append(key)
    return face_matching_show(img, results, names, tolerance)


def face_matching_show(image, results, names, tolerance=1):
    # 数据清洗与整理
    return_dic = {}
    recognition_result = []
    time_now = time.time()
    df = pd.DataFrame(results)
    min_face_dis = []
    min_dict_dis = []
    try:
        for i in range(len(names)):
            min_dict_dis.append(min(df.loc[i, :]))
        for i in range(df.size//len(names)):
            min_face_dis.append(min(df.loc[:, i]))
    except:
        return "no_face_error"
    df_show = df.copy(deep=True)
    df_show["name"] = names
    df_show.set_index("name", inplace=True)
    df_show["min"] = min_dict_dis
    df_show.to_excel(os.path.join(BASE_DIR, 'statics', 'temp_image', '%f.xls' % time_now))
    # 图像画布初始化
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    font_size = pil_image.size[0]//50
    ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
    # draw.text((0, 0), "已加载人脸:\n"+"\n".join(names), "red", ft)
    # 图像人脸绘图
    face_list = face_recognition.face_locations(image)
    for i in range(len(face_list)):
        box = (face_list[i][3], face_list[i][0], face_list[i][1], face_list[i][2])
        draw.rectangle(box, None, 'yellow', width=font_size//8)
        draw.text((box[0:2]), str(i), "red", ft)
        recognition_result.append(None)
        for j in range(len(names)):
            if df.loc[j, i] == min_face_dis[i] and df.loc[j, i] == min_dict_dis[j] and df.loc[j, i] <= tolerance:
                name = FaceImage.objects.filter(path__startswith=names[j])[0].name.name
                draw.text((box[0], box[1]-font_size), name, "red", ft)
                recognition_result[i] = name


    img_path = os.path.join('temp_image', '%f.jpg' % time_now)
    pil_image.save(os.path.join(BASE_DIR, 'statics', img_path))
    return_dic['path'] = img_path
    return_dic['result'] = recognition_result
    return return_dic

def dict_add(path, name):
    face = face_recognition.load_image_file(path)
    name_path = os.path.split(path)[-1]
    img_path = name_path[:name_path.find("-")]+name_path[name_path.rfind("."):]
    image_obj = image_db.objects.filter(path=img_path)[0]
    try:
        info = face_recognition.face_encodings(face, num_jitters=100)[0]
        save_path = os.path.join(BASE_DIR, 'cv', 'model', name+"@"+name_path[:name_path.rfind('.')]+'.npy')
        np.save(save_path, info)
        pic_save_path = os.path.join(BASE_DIR, 'cv', 'model_image', name+'@'+name_path)
        fpw = open(pic_save_path, "wb")
        fpr = open(path, "rb")
        for line in fpr:
            fpw.write(line)
        print(name+'.npy'+" saved")
        #face_show(face)
        path = os.path.basename(pic_save_path)
        name = path[:path.find('@')]
        uploadtime = pic_save_path[pic_save_path.find('@') + 1:pic_save_path.rfind('-')]
        uploadtime = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(eval(uploadtime)))
        print(name, uploadtime, path, "\n")
        if People.objects.filter(name=name):
            people = People.objects.filter(name=name)[0]
        else:
            people = People(name=name)
            people.save()
        obj = FaceImage(name=people, path=path, upload_time=uploadtime, image=image_obj)
        obj.save()
    except IndexError:
        print("人脸过于模糊，请提供清晰的正面照")
        return 0
    return 1


def face_show(image):
    face_landmarks_list = face_recognition.face_landmarks(image)
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    for face_landmarks in face_landmarks_list:
        facial_features = [
            'chin',
            'left_eyebrow',
            'right_eyebrow',
            'nose_bridge',
            'nose_tip',
            'left_eye',
            'right_eye',
            'top_lip',
            'bottom_lip'
        ]
        for facial_feature in facial_features:
            draw.line(face_landmarks[facial_feature], width=2)
    pil_image.show()






# dict_add(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\裨益知 W. L. Beard\Young Willard L. Beard from 1894 letter.jpg","W.L.Beard")
# dict_add(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\face\Young Ellen Lucy Kinney (Mrs. Beard) from 1894 letter-1.jpg","E.L.Kinney")
# dict_add(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\face\model\1891-1894 W. L. Beard 04254v-1.jpg", "W.L.Beard-y")
# dict_add(r"C:\Users\boyif\Desktop\paddle\re_pic\Dr. and Mrs. Baldwin missionaries 1847-1895 (Caleb C. and Harriet F. Baldwin) (from Jill Elmer Jackson - 1894 letter)-1.jpg","Mrs.Baldwin")
# face_matchng(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\裨益知 W. L. Beard\1900 - Willard L. Beard and Ellen are in the middle.jpg")
# face_matchng(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\裨益知 W. L. Beard\1900 - Willard L. Beard sits in the middle seated next to Ellen and Ding Ming Uong next to Ellen (from 1900 letter).jpg")
