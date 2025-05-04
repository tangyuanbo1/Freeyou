from paddleocr import PaddleOCR, draw_ocr
import time  # 新增导入

# Paddleocr supports Chinese, English, French, German, Korean and Japanese
# You can set the parameter `lang` as `ch`, `en`, `french`, `german`, `korean`, `japan`
# to switch the language model in order
ocr = PaddleOCR(use_angle_cls=True, lang='ch') # need to run only once to download and load model into memory
img_path = './logo.jpg'
# 记录开始时间
start_time = time.time()

result = ocr.ocr(img_path, cls=True)

# 计算并打印推理时间
elapsed_time = time.time() - start_time

for idx in range(len(result)):
    res = result[idx]
    for line in res:
        print(line)
print(f"推理用时: {elapsed_time:.2f} 秒")
# # draw result
from PIL import Image
result = result[0]
image = Image.open(img_path).convert('RGB')
boxes = [line[0] for line in result]
txts = [line[1][0] for line in result]
scores = [line[1][1] for line in result]
im_show = draw_ocr(image, boxes, txts, scores)
im_show = Image.fromarray(im_show)
im_show.save('result.jpg')