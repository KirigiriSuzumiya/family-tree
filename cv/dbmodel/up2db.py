# import os
# import time
from dbmodel.models import FaceImage,People
# files = os.listdir('D:\image_recognition\cv\cv\model_image')
# print(files)
# for file in files:
#     name = file[:file.find('@')]
#     uploadtime = file[file.find('@')+1:file.rfind('-')]
#     uploadtime = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(eval(uploadtime)))
#     path = file
#     print(name, uploadtime, path, "\n")
#     if People.objects.filter(name=name):
#         people = People.objects.filter(name=name)[0]
#     else:
#         people = People(name=name)
#         people.save()
#     obj = FaceImage(name=people, path=path, upload_time=uploadtime)
#     obj.save()

peoples = People.objects.all()
