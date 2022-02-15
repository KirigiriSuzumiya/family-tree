import face_recognition
from PIL import Image,ImageDraw,ImageFont
import glob
import os
from pathlib import Path


def extractor(img_path):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    image = face_recognition.load_image_file(img_path)
    origin = Image.open(img_path)
    locations = face_recognition.face_locations(image)
    # 保存合照人头画框
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    font_size = pil_image.size[0] // 30
    ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
    face_list = locations
    for i in range(len(face_list)):
        box = (face_list[i][3], face_list[i][0], face_list[i][1], face_list[i][2])
        draw.rectangle(box, None, 'yellow')
        draw.text((box[0:2]), str(i+1), "red", ft)
    img_path = os.path.join(BASE_DIR, 'statics', 'temp_image', os.path.split(img_path)[-1])
    pil_image.save(img_path[0:img_path.rfind('.')]+'-0'+img_path[img_path.rfind("."):])
    # 保存各个人头大头贴
    count = 1
    for location in locations:
        box = (location[3], location[0], location[1], location[2])
        face = origin.crop(box)
        save_path = img_path[0:img_path.rfind('.')]+'-'+str(count)+img_path[img_path.rfind("."):]
        face.save(save_path)
        #print(save_path+" saved!")
        count += 1
    return count-1
