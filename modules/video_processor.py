from PIL import Image
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip
import math
from wand.image import Image as wand_Image
from wand.drawing import Drawing, TEXT_DECORATION_TYPES
from wand.color import Color
import cv2




def hex_to_rgb(hex_color):
    # переводим цвет из 16-тиричного представления в RGB-кортеж
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def title_splitter(string, video, text_clip, header_font_size, title_font_path, header_text_color):
    video_width = video.size[0] # ширина видео
    text_width = text_clip.w # ширина текста
    text_height = text_clip.h # высота текста
    if (rows:=math.ceil(text_width/video_width)) > 2:
        print("Текст не вмещается в 2 строки, уменьшаем...")
        while (rows:=math.ceil(text_width/video_width)) > 2:
            # уменьшаем шрифт
            header_font_size -= 1
            text_clip = TextClip(string, fontsize=header_font_size, font=title_font_path, color=header_text_color)
            text_width = text_clip.w # ширина текста
            text_height = text_clip.h # высота текста

    if (rows:=math.ceil(text_width/video_width)) > 1:
        print(f"Разбиваем на {rows} строки")
        while True:
            # вычисляем среднюю ширину одного символа
            char_width = text_width / len(string)
            # вычисляем количество символов, которые могут поместиться в одну строку
            chars_per_line = video_width / char_width
            # разбиваем текст на строки, сохраняя целостность слов
            lines = []
            current_line = ""
            for word in string.split():
                if len(current_line) + len(word) + 1 <= chars_per_line:
                    current_line += word + " "
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())
            string = "\n".join(lines)
            # если строк больше чем 2
            if len(lines) != 2:
                header_font_size -= 1
                text_clip = TextClip(string, fontsize=header_font_size, font=title_font_path, color=header_text_color)
                text_width = text_clip.w
            else:
                break


    text_clip = TextClip(string, fontsize=header_font_size, font=title_font_path, color=header_text_color)
    # вычисляем координату Y нижней границы текста
    bottom_edge_y = video.size[1]//32 + text_clip.h
    print(f"Нижняя граница текста на видео: {bottom_edge_y}")
    

    return text_clip, header_font_size, bottom_edge_y


# обрезаем текст (отрезаем прозрачные части)
def crop_to_non_transparent(image_path):
    # загружаем картинку
    image = Image.open(image_path)
    # берём прозрачность
    alpha = image.split()[-1]
    # ищём прямоугольник, по которому будем резать
    bbox = alpha.getbbox()
    # режем
    cropped_image = image.crop(bbox)
    # сохраняем
    cropped_image.save(image_path)

def draw_text(draw, text, width, x, img, main_text_color, main_font_path, main_bold_text_color, main_bold_font_path):
    global logo_data
    words = text.replace("\n", "<n> ")
    words = words.split(" ")

        
    logo_data = {} # флаг, будет ли тут логотип
    # Вычисляем ширину буквы А (для примерного представления, какая средняя ширина символов)
    line = ''
    letter_width = int(draw.get_font_metrics(img, 'Ш').text_width)
    letter_height = int(draw.get_font_metrics(img, 'Ш').text_height)
    y = letter_height
    for i, word in enumerate(words):
        word_width = int(draw.get_font_metrics(img, word.replace("<n>", "")).text_width)
        flag_logo = False
        flag_newline = False

        if "<l>" in word:
            word = word.replace("<l>", "  ")
            logo_data["x"] = x + word_width + letter_width
            logo_data["y"] = y
            logo_data["size"] = letter_width*2
            flag_logo = True


        if "<n>" in word:
            word = word.replace("<n>", "")
            flag_newline = True


        if word == '':
            word = " "


        if "<b>" in word or "<u>" in word or "<c>" in word:

            if "<b>" in word:
                # Remove the "<b>" tag from the word
                word = word.replace("<b>", "")
                # жирный шрифт
                draw.font = main_bold_font_path

            if "<u>" in word:
                word = word.replace("<u>", "")
                # делаем текст подчёркнутым
                draw.text_decoration = TEXT_DECORATION_TYPES [2]

            if "<c>" in word:
                word = word.replace("<c>", "")
                # цвет для текста
                draw.fill_color = Color(main_bold_text_color)



            word_width = int(draw.get_font_metrics(img, word).text_width)
            
            # если не вмещается в эту строку
            if x + word_width + letter_width > width:
                # смещаем y вниз
                y += letter_height
                x = 0
            
            draw.text(x, y, word)  
            if flag_newline:
                y += letter_height
             
            
            # смещаем координату х
            if flag_newline == False:
                x += word_width+letter_width
            else:
                x = 0
            

        else:
            # устанавливаем цвет для текста
            draw.fill_color = Color(main_text_color)
            # проверяем, вмещается-ли в эту строку, и если нет, то
            if x + word_width + letter_width > width:
                # переносим на следующую строку
                y += letter_height
                x = 0
            # отрисовываем
            draw.text(x, y, word)
            if flag_newline:
                y += letter_height

            
                
            # обновляем координату x для следущего слова
            if flag_newline == False:
                x += word_width+letter_width
                # if flag_logo:
                #     x += letter_width
            else:
                x = 0



        # восстанавливаем оформление шрифта
        # обычный шрифт
        draw.font = main_font_path
        # возвращаем обычный стиль для текста
        draw.text_decoration = TEXT_DECORATION_TYPES [1]
        # возвращаем обычный цвет текста
        draw.fill_color = Color(main_text_color)

    return y





def process(video_path, header_text, header_font_size, fill_color, header_text_color, main_text, \
main_text_color, main_bold_text_color, main_fill_color, main_alpha, main_font_size, preview=True, video_id=0):
    global logo_data
    # Путь к вашему шрифту
    title_font_path = "for_videos/title_font.otf"
    # основной шрифт обычный
    main_font_path = "for_videos/main_font.otf"
    # жирный шрифт
    main_bold_font_path = "for_videos/main_font_bold.otf"
    # словарь данных для отображения логотипа
    logo_data = {} 

    # если был выбран режим предпросмотра
    if not preview:
        # Загрузка видео
        video = VideoFileClip(video_path)

    else:
        # Открываем видео
        cap = cv2.VideoCapture(video_path)

        # Читаем первый кадр
        ret, frame = cap.read()

        # Закрываем видео
        cap.release()

        # Если кадр успешно прочитан, преобразуем его в ImageClip
        if ret:
            # OpenCV использует BGR, поэтому мы конвертируем его в RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Создаем ImageClip
            video = ImageClip(frame_rgb)
        else:
            print(f"Ошибка при работе с файлом {video_path}")
            return None




    # Создание текстового клипа для заголовка



    # получаем новый клип, новый размер шрифта заголовка, координату Y для нижней границы заголовка на видео
    title_text, header_font_size, bottom_edge_y = title_splitter(string=header_text, header_text_color=header_text_color, title_font_path=title_font_path, video=video, header_font_size=header_font_size, text_clip=TextClip(header_text, fontsize=header_font_size, font=title_font_path, color=header_text_color))



    # Создание фона для текста заголовка
    background = ColorClip(size=(int(title_text.w*1.2), int(title_text.h)), color=hex_to_rgb(fill_color))#.set_opacity(0.5)
    # фон для текста и поверх него текст
    vid_with_background = CompositeVideoClip([video, background.set_position(('center', video.size[1]//32)).set_duration(video.duration), title_text.set_position(('center', video.size[1]//32)).set_duration(video.duration)])

    # если есть знаки переноса строки в конце текста, то убираем их
    main_text = main_text.rstrip("\n")

    font_size_normal = False
    # создаём картинку с текстом
    while not font_size_normal:
        with Drawing() as draw:
            with wand_Image(width=video.size[0], height=video.size[1], background=Color('rgba(0, 0, 0, 0)')) as img:
                draw.font = main_font_path
            
                draw.font_size = main_font_size
                y = draw_text(draw, main_text, img.width, 0, img, main_text_color, main_font_path, main_bold_text_color, main_bold_font_path)
                # если текст перекрывается заголовком, то уменьшаем шрифт
                if video.size[1]-y == 0:
                    main_font_size -= 1
                    continue
                if (video.size[1]//2 - (y//2+main_font_size*2)) < bottom_edge_y*1.1:
                    print(f"Верхняя граница основного текста: {video.size[1]//2 - y//2}")
                    print("Основной текст перекрывает заголовок. Уменьшаем шрифт...")
                    main_font_size -= 1
                    continue
                else:
                    font_size_normal = True

                draw(img)
                img.save(filename=f"previews/preview_{video_id}.png")

    # обрезаем прозрачность
    crop_to_non_transparent(f"previews/preview_{video_id}.png")

    # конвертируем в RGN
    formatter = {"PNG": "RGBA", "JPEG": "RGB"}
    img = Image.open(f"previews/preview_{video_id}.png")
    rgbimg = Image.new(formatter.get(img.format, 'RGB'), img.size)
    rgbimg.paste(img)
    rgbimg.save(f"previews/preview_{video_id}.png", format=img.format)

    img_width, img_height = img.size


    main_text = (ImageClip(f"previews/preview_{video_id}.png").set_duration(video.duration).margin(opacity=0).set_pos((main_font_size, video.size[1]//2-img_height//2)))

    # фон основного текста
    background_color = hex_to_rgb(main_fill_color)
    img_width = video.size[0]
    background_image = ColorClip(size=(img_width, img_height+main_font_size*2), color=background_color)
    background_image = background_image.set_duration(video.duration)
    background_image = background_image.set_opacity(main_alpha)

    # тут задаём позицию, в которой будем выводить картинку с текстом (можно привязать в title)
    background_image = background_image.set_pos((0, video.size[1] // 2 - img_height // 2 - main_font_size))

    if logo_data != {}:
        # наложение гиф-анимации на видео
        watermark = (VideoFileClip(r"for_videos/logo.gif", has_mask=True)
                             .loop()  # loop gif
                             .set_duration(video.duration)  # Продолжительность водяного знака
                             .resize((logo_data["size"], logo_data["size"]))  # Высота водяного знака будет пропорционально масштабирована.
                             .margin(left=0, top=0, opacity=0))  # Поля водяных знаков и прозрачность

        watermark = watermark.set_pos((logo_data["x"]-watermark.w//2-logo_data["size"]//3, video.size[1]//2-img_height//2+logo_data["y"]-logo_data["size"]))  # Расположение водяного знака

        final = CompositeVideoClip([vid_with_background, background_image, main_text, watermark])
    else:
        final = CompositeVideoClip([vid_with_background, background_image, main_text])


    if preview:
        # для сохранения превью
        final.save_frame(f"previews/preview_{video_id}.png", t=0)
    else:
        # для сохранения видео
        final.write_videofile(f"output/output_{video_id}.mp4")


    return header_font_size, main_font_size


'''
2) определяем y нижнего края рамки (основной текст начинать выводить от...)
'''