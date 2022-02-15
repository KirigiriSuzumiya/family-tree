# # ————————————图像的读取、显示和保存———————————— #
# # 导入cv模块
# import cv2 as cv
# # 读取图像，支持bmp、jpg、png、tiff等
# img = cv.imread('../files/m16a1.jpg')
# # 创建窗口并显示图像
# cv.namedWindow("Image")
# cv.imshow("Image", img)
# # 输出图像，等待键盘接收命令
# cv.waitKey(0)
# # ————————————图像通道处理———————————— #
# b, g, r = cv.split(img)  # 拆分图像通道为b、g、r三个通道
# cv.imshow("b", b)  # 显示b通道的图像信息
# cv.waitKey(0)
# cv.imshow("g", g)  # 显示g通道的图像信息
# cv.waitKey(0)
# cv.imshow("r", r)  # 显示r通道的图像信息
# cv.waitKey(0)
# # —————————————图像属性获取——————————— #
# # 输出图像的大小属性
# print("image.shape", img.shape)
# # 输出图像的像素数目属性
# print("image.size", img.size)
# # 输出图像的类型属性
# print("image.dtype", img.dtype)
# # —————————————numpy创建图——————————— #
# import numpy as np
# img1 = np.random.randint(0, 256, size=[1080, 1954, 3], dtype="uint8")
# cv.imshow("img1", img1)
# cv.waitKey(0)
# # —————————————色彩空间转换——————————— #
# img2 = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
# cv.imshow("img2", img2)
# cv.waitKey(0)
# # —————————————图像基本运算——————————— #
# img3 = cv.add(img, img1)
# cv.imshow("img3", img3)
# cv.waitKey(0)
# img4 = cv.divide(img3, img)
# cv.imshow("img4", img4)
# cv.waitKey(0)
# cv.destroyAllWindows()
import django

print(django.get_version())
