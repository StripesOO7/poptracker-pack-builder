import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageDraw, ImageFont


def _gimp_png(save_path, name, length):
    font = ImageFont.truetype(r'C:\Windows\Fonts\micross.ttf', 40)
    multiline_count = name.count('\n')
    print(multiline_count)
    charsize = (length * 17, 46*(multiline_count+1))
    W, H = charsize
    color = '#fff'
    if multiline_count > 0:
        text = name.replace('\n', ' ')
    else:
        text = name
    path = fr'{save_path}\{text.replace(" ","_").lower()}.png'
    print(path)
    bg_img = Image.new('RGB', charsize, color)
    mask_img = Image.new('L', bg_img.size, 0)
    draw = ImageDraw.Draw(mask_img)
    _, _, w, h = draw.textbbox((0, 0), text, font=font)
    if multiline_count > 0:
        draw.multiline_text(((W - w) / 2, (H - h) / 2), text=text, font=font, fill='white', align='center')
    else:
        draw.text(xy=(0, 0), text=text, font=font, fill='white')
    bg_img.putalpha(mask_img)
    bg_img.save(path)


# def _gimp_png_multiline(save_path, name, length):
#     font = ImageFont.truetype(r'C:\Windows\Fonts\micross.ttf', 40)
#     # charsize = (length * 19, 92)
#     # W, H = charsize
#     color = '#fff'
#
#     multiline_count = name.count('\n')
#     charsize = (length * 17, 46*(multiline_count+1))
#     W, H = charsize
#     text = name.replace("\n", " ")
#     path = fr'{save_path}\{text.replace(" ", "_").lower()}.png'
#
#     print(path)
#     bg_img = Image.new('RGB', charsize, color)
#     mask_img = Image.new('L', bg_img.size, 0)
#     draw = ImageDraw.Draw(mask_img)
#     _, _, w, h = draw.textbbox((0, 0), text, font=font)
#     draw.multiline_text(((W - w) / 2, (H - h) / 2), text=text, font=font, fill='white', align='center')
#     bg_img.putalpha(mask_img)
#     bg_img.save(path)

if __name__ == '__main__':
    '''
    You are about to create images from a file containing a list of strings where each line is separated by a \\n (
    newline character)
    This List should be in on of the following formats:
    
    - a single item  such as: "Complete Mask Quest" 
    - a list of possible combinations such as: "Logic Rules", glitchless, glitched, no logic
    
    the option with a single item will be converted into an image with a single line
    
    the option in list form will be combines one by one with the first one resulting in 
    - "Logic Rules" glitchless
    - "Logic Rules" glitched
    - "Logic Rules" no logic
    and converted into a multiline image
    '''

    root = tk.Tk()
    root.withdraw()
    print('''
    You are about to create images from a file containing a list of strings where each line is separated by a \\n (
    newline character)
    This List should be in on of the following formats:
    
    - a single item  such as: "Complete Mask Quest" 
    - a list of possible combinations such as: "Logic Rules", glitchless, glitched, no logic
    
    the option with a single item will be converted into an image with a single line
    
    the option in list form will be combines one by one with the first one resulting in 
    - "Logic Rules" glitchless
    - "Logic Rules" glitched
    - "Logic Rules" no logic
    and converted into a multiline image
    ''')
    print("Select a file to open")
    text_to_image_filepath = filedialog.askopenfilename()
    print("Filename: ", text_to_image_filepath)
    print("Select a folder to save the created images into:")
    save_to_path = filedialog.askdirectory()
    print("Path to folder to save file to: ", save_to_path)
    with open(rf'{text_to_image_filepath}') as names:
        # max = 0
        line_split = []
        for line in names:
            if ", " in line:
                line_split.append(line.replace('\n', '').replace('"', '').split(', '))
            else:
                line_split.append(line.replace('\n', '').replace('"', ''))
        for index, lines in enumerate(line_split):
            # print(line)
            if len(lines) > 1 and isinstance(lines, list):
                for i, _ in enumerate(lines):
                    if i != 0:
                        # print('\n'.join((lines[0], lines[i])))
                        _gimp_png(save_to_path, '\n'.join((lines[0], lines[i])), 28)

            else:
                # pass
                # print(lines)
                _gimp_png(save_to_path, lines, 28)
                # if len(lines[0]) > max:
            #     max = len(lines[0])
            # gimp_png(line[0]+line[1], 33)