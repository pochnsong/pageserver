import uuid
import os
def resize(path, max_size=(100, 100), save_format=None):
    try:
        from PIL import Image
    except:
        exit()

    img = Image.open(path)
    if not save_format:
        save_format = img.format
    save_format = save_format.upper()
    max_width, max_height = max_size
    width, height = img.size
    save = False
    if max_width and width > max_width:
        height = max_width/width*height
        width = max_width
        save = True

    if max_height and height > max_height:
        width = max_height/height*width
        height = max_height
        save = True

    if save:
        if save_format == 'JPEG':
            print(img.format)
            img = img.convert('RGB')

        img = img.resize((int(width), int(height)))
        img.save(path, save_format)


if __name__ == "__main__":
    resize("/home/song/code/college/media/master/zj (3).png", (500, None), 'jpeg')
