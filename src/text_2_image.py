# Arquivo que insere as informações falsas nas imagens.

import itertools
import json
import os
import random
import secrets
import string
import time
from pathlib import Path

import cv2 as cv
from PIL import Image, ImageDraw, ImageFont

import background_generator
import class_pessoa
import paths

from logging_cfg import logging

entities = json.loads(Path('files/entities.json').read_text())


# TODO: estimate these heights from annotation
height_dict = {
    'nome': 4.6,
    'nomePai': 3.6, 'nomeMae': 3.6,
    'date': 3.1, 'city-est': 3.1,
    'serial?': 3.5, 'cod-sec': 2.9
}


# Gera o texto a ser colocado na mask.
def text_generator(tipo_texto, pessoa, tipo_doc, control_text):
    qtd_chars = control_text
    text = ''
    if tipo_texto in ('nome', 'nomePai', 'nomeMae'):
        text = pessoa.set_nome(qtd_chars)
    elif tipo_texto == 's_nome':
        text = pessoa.set_s_nome()
    elif tipo_texto == 'cpf':
        text = pessoa.set_cpf()
    elif tipo_texto == 'rg':
        text = pessoa.set_rg(tipo_doc)
    elif tipo_texto in ['org', 'inst']:
        text = pessoa.set_org()
    elif tipo_texto == 'est':
        text = pessoa.set_est()
    elif tipo_texto == 'city':
        text = pessoa.set_cid_est(qtd_chars)
    elif tipo_texto == 'city-est':
        text = pessoa.set_cid_est(qtd_chars)
    elif tipo_texto == 'rg_org_est':
        text = pessoa.set_rg_org_est()
    elif tipo_texto == 'date':
        text = pessoa.set_data()
    elif tipo_texto == 'tipo_h':
        text = pessoa.set_tipo_h()
    elif tipo_texto == 'n_9':
        text = pessoa.set_n_9(qtd_chars)
    elif tipo_texto == 'n_reg':
        text = pessoa.set_n_reg()
    elif tipo_texto == 'n_11':
        text = pessoa.set_n_11()
    elif tipo_texto == 'cod_11':
        text = pessoa.set_cod_11()
    elif tipo_texto == 'obs':
        text = pessoa.set_obs()
    elif tipo_texto == 'cargo':
        text = pessoa.set_cargo()
    elif tipo_texto == 'comarca':
        text = pessoa.set_d_orig()
    elif tipo_texto == 'doc':
        text = pessoa.set_folha()
    elif tipo_texto == 'aspa':
        text = pessoa.set_aspa()
    elif tipo_texto == 'via':
        text = pessoa.set_via()
    elif tipo_texto == 'pis':
        text = pessoa.set_pis(qtd_chars)
    elif tipo_texto == 'cod_4':
        text = pessoa.set_cod_4()
    elif tipo_texto == '5-code':
        text = pessoa.set_n_5()
    elif tipo_texto == 'cod_10':
        text = pessoa.set_cod_10()
    elif tipo_texto == 'cid':
        text = pessoa.set_cid(qtd_chars)
    elif tipo_texto == 'cod_8':
        text = pessoa.set_cod_8()
    elif tipo_texto == 'n_via':
        text = pessoa.set_n_via()
    elif tipo_texto == 'n_6':
        text = pessoa.set_n_6()
    elif tipo_texto == 'per':
        text = 'PERMISSÃO'
    elif tipo_texto == 'rga':
        text = 'RG ANTERIOR'
    elif tipo_texto == 'naci':
        text = 'BRASILEIRA'
    elif tipo_texto == 'serial?':
        text = f"{''.join(map(str, (random.randint(0, 8) for _ in range(4))))}-{random.randint(0, 8)}"

    elif tipo_texto == 'cod-sec':
        text = secrets.token_hex(4).upper()
    return text


def med_text_area(text_width, text_height):
    if text_height > text_width:
        return text_width
    a = text_width / (text_height * 0.6)
    return int(a)


def get_font_args(tipo_doc):
    return 'white'


def localize_text_area(temp_mask_path):
    """Attempts to shrink annotated ROI by detecting text
    """
    x, y, w, h = 0, 0, 0, 0
    temp_mask = cv.imread(temp_mask_path)
    gray = cv.cvtColor(temp_mask, cv.COLOR_BGR2GRAY)
    gray = cv.medianBlur(gray, 5)
    thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY_INV, 11, 2)

    thresh = cv.dilate(thresh, None, iterations=15)
    thresh = cv.erode(thresh, None, iterations=15)
    contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)
        if w >= 5 and h >= 5:
            return [x, y, w, h]
    return [x, y, w, h]


# Gera as demais masks.
def text_mask_generator(tipo_doc, json_arq, img_fname, angle):
    area_n_text = []
    bg_color = get_font_args(tipo_doc)
    p1 = class_pessoa.Person()


    img = Image.open(str(paths.path_entrada / img_fname))
    img_width, img_height = img.size

    bimg_width, bimg_height = Image.open(str(paths.path_back / img_fname)).size

    mask = Image.new('RGB', (img_width, img_height), color=bg_color)
    mask_name = 'mask_' + img_fname
    mask.save(os.path.join(paths.path_mask, mask_name))
    mask.close()

    temp_mask_path = Path(paths.path_mask) / ('temp_mask_' + img_fname)

    regions = json_arq

    # Checa se a imagem está no path
    if regions is not None:
        qtd_regions = len(regions)
        for aux in range(qtd_regions):
            mask_open = Image.open(paths.path_mask / mask_name)

            tag = regions[aux]['region_attributes']['tag']
            if regions[aux]['region_attributes']['info_type'] == 'p' and \
                    len(regions[aux]['region_attributes']) > 1:

                tipo_texto = regions[aux]['region_attributes']['text_type']

                font_color = (8, 8, 8)
                if tipo_texto in ('nome', 'serial?', 'date'):
                    font_type = (paths.path_static / 'fonts' / 'tahoma' / 'tahoma-bold.ttf').as_posix()
                else:
                    font_type = (paths.path_static / 'fonts' / 'tahoma' / 'tahoma-3.ttf').as_posix()

                if regions[aux]['region_shape_attributes']['name'] == 'rect':
                    # Região é um retângulo.
                    x_inicial = regions[aux]['region_shape_attributes']['x']
                    width = regions[aux]['region_shape_attributes']['width']
                    y_inicial = regions[aux]['region_shape_attributes']['y']
                    height = regions[aux]['region_shape_attributes']['height']

                    x_final = x_inicial + width
                    y_final = y_inicial + height

                    x_inicial, y_inicial, x_final, y_final = background_generator.rotate_points(
                        img_width,
                        img_height,
                        x_inicial, y_inicial,
                        x_final, y_final,
                        angle=angle)

                    width = x_final - x_inicial
                    height = y_final - y_inicial

                    min_x, max_x, min_y, max_y = tuple(map(int, (x_inicial, x_final, y_inicial, y_final)))

                else:
                    # Não é um retângulo.
                    all_points_x = regions[aux]['region_shape_attributes']['all_points_x']
                    all_points_y = regions[aux]['region_shape_attributes']['all_points_y']
                    qtd_points = len(all_points_x)

                    points_x = []
                    points_y = []

                    for i in range(qtd_points):
                        pts_x, pts_y = background_generator.rotate_poly(
                            img_width, img_height, all_points_x[i], all_points_y[i], angle=angle)

                        points_x.append(pts_x)
                        points_y.append(pts_y)

                    min_x, min_y, max_x, max_y = tuple(map(
                        int,
                        (min(points_x), min(points_y), max(points_x), max(points_y))))
                    width = max_x - min_x
                    height = max_y - min_y

                if tipo_texto in height_dict:
                    height = int(bimg_height * height_dict[tipo_texto] / 100)

                qtd_chars = med_text_area(width, height)
                font = ImageFont.truetype(font_type, height)
                text = text_generator(tipo_texto, p1, tipo_doc, control_text=qtd_chars)
                ImageDraw.Draw(mask_open).text(
                    (min_x, min_y), text, font_color, anchor='rs', font=font, align='left')

                if tipo_texto != 'x':
                    temp_mask = Image.new('RGB', (img_width, img_height), color=bg_color)
                    ImageDraw.Draw(temp_mask).text(
                        (min_x, min_y), text, font_color, anchor='rs', font=font, align='left')
                    temp_mask.save(temp_mask_path)
                    temp_mask.close()

                    area = localize_text_area(temp_mask_path.as_posix())
                    area.append(text)
                    area.append(tag)
                    area_n_text.append(area)
                    os.remove(temp_mask_path)

                mask_open.save(os.path.join(paths.path_mask, mask_name))
                mask_open.close()

            else:  # Texto default do documento
                transcription = regions[aux]['region_attributes']['transcription']

                # Região é um retângulo
                if regions[aux]['region_shape_attributes']['name'] == 'rect':
                    x_inicial = regions[aux]['region_shape_attributes']['x']
                    width = regions[aux]['region_shape_attributes']['width']
                    y_inicial = regions[aux]['region_shape_attributes']['y']
                    height = regions[aux]['region_shape_attributes']['height']

                    x_final = x_inicial + width
                    y_final = y_inicial + height

                    x_inicial, y_inicial, x_final, y_final = background_generator.rotate_points(img_width,
                                                                                                img_height,
                                                                                                x_inicial, y_inicial,
                                                                                                x_final, y_final,
                                                                                                angle=angle)

                    min_x, max_x, min_y, max_y = x_inicial, x_final, y_inicial, y_final

                    width = max_x - min_x
                    height = max_y - min_y

                    if transcription != 'X':
                        area = [min_x, min_y, width, height, transcription, tag]
                        area_n_text.append(area)

                else:
                    all_points_x = regions[aux]['region_shape_attributes']['all_points_x']
                    all_points_y = regions[aux]['region_shape_attributes']['all_points_y']
                    qtd_points = len(all_points_x)

                    points_x = []
                    points_y = []
                    width = -1
                    height = -1

                    for i in range(qtd_points):
                        pts_x, pts_y = background_generator.rotate_poly(img_width, img_height,
                                                                        all_points_x[i], all_points_y[i], angle=angle)
                        points_x.append(pts_x)
                        points_y.append(pts_y)

                    if transcription != 'X':
                        area = [points_x, points_y, width, height, transcription, tag]
                        area_n_text.append(area)

    return area_n_text


# Cria o txt baseado nas possíveis rotações que ocorreram com a imagem
def write_txt_file(txt_name, area_n_text, angle):
    txt_text = ''
    img = Image.open(str(paths.path_saida / (txt_name + '.jpg')))
    img_width, img_height = img.size
    im = Image.new('RGB', (img_width, img_height), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    for element in area_n_text:
        width = element[2]
        height = element[3]
        tag = element[5]
        if not entities[tag]['is_entity']:
            continue
        transcription = entities[tag].get('transcript', element[4])
        if width == -1 and height == -1:
            final_points_x = []
            final_points_y = []
            x_points = element[0]
            y_points = element[1]
            qtd_points = len(x_points)
            for i in range(qtd_points):
                pts_x, pts_y = background_generator.rotate_poly(
                    img_width, img_height, x_points[i], y_points[i], angle=angle)

                final_points_x.append(pts_x)
                final_points_y.append(pts_y)
            xy = [(final_points_x[a], final_points_y[a]) for a in range(len(final_points_x))]

            txt_text = txt_text + \
                '{}, {}, {}, {}, {}, {}\n'.format(final_points_x, final_points_y, width, height, transcription, tag)

            draw.polygon(xy, fill=(255, 255, 255))
        else:
            x_inicial = element[0]
            y_inicial = element[1]
            x_final = x_inicial + width
            y_final = y_inicial + height
            x_inicial, y_inicial, x_final, y_final = background_generator.rotate_points(
                img_width, img_height, x_inicial, y_inicial, x_final, y_final, angle=angle)

            width = x_final - x_inicial
            height = y_final - y_inicial
            txt_text = txt_text + \
                '{}, {}, {}, {}, {}, {}\n'.format(x_inicial, y_inicial, width, height, transcription, tag)

            draw.rectangle((x_inicial, y_inicial, x_final, y_final), fill=(255, 255, 255))
    im.save(str(paths.path_saida / f'{txt_name}_mask_GT.jpg'))
    with open(paths.path_saida / f'{txt_name}_GT.txt', 'w') as file:
        file.write('x, y, width, height, transcription, tag\n')
        file.write(txt_text)


# Joga pixels brancos na imagem para que pareça mais real.
def blur_mask(img_name, path_img, tipo_doc):
    mask_img = cv.imread(os.path.join(path_img, img_name))
    blue_mask, green_mask, red_mask = cv.split(mask_img)
    for j in range(mask_img.shape[0]):
        for i in range(mask_img.shape[1]):
            random.seed()
            ruido = random.randint(0, 100)
            if ruido > 95:
                if tipo_doc == 'CPF':
                    blue_mask[j][i] = 0
                    green_mask[j][i] = 0
                    red_mask[j][i] = 0
                else:
                    blue_mask[j][i] = 255
                    green_mask[j][i] = 255
                    red_mask[j][i] = 255
    dst = cv.merge((blue_mask, green_mask, red_mask))
    cv.imwrite(os.path.join(paths.path_mask, img_name), dst)


# Cria um nome aleatório para as imagens geradas.
def create_img_name(img_name):
    num = ''
    random.seed()
    let = ''.join(random.choice(string.ascii_letters) for _ in range(7))
    random.seed()
    for _ in range(7):
        num = num + str(random.randrange(10))
    return img_name + '_' + num + let


# Faz a multiplicação da mask com a imagem original.
def mult_img(mask_name, img_name, tipo_doc, area_n_text, param):
    new_img_name = create_img_name(img_name)
    back = cv.imread(os.path.join(paths.path_back, img_name))
    blue_back, green_back, red_back = cv.split(back)
    y = back.shape[0]
    x = back.shape[1]
    mask = cv.imread(os.path.join(paths.path_mask, mask_name))
    blue_mask, green_mask, red_mask = cv.split(mask)
    for j, i in itertools.product(range(y), range(x)):
        if tipo_doc == 'CPF':
            if blue_mask[j][i] > param and green_mask[j][i] > param and red_mask[j][i] > param:
                blue_back[j][i] = blue_mask[j][i]
                green_back[j][i] = green_mask[j][i]
                red_back[j][i] = red_mask[j][i]
        elif blue_mask[j][i] < param and green_mask[j][i] < param and red_mask[j][i] < param:
            blue_back[j][i] = blue_mask[j][i]
            green_back[j][i] = green_mask[j][i]
            red_back[j][i] = red_mask[j][i]
    final_img = cv.merge((blue_back, green_back, red_back))
    outfpath = str(paths.path_saida / (new_img_name + '.jpg'))
    cv.imwrite(outfpath, final_img)
    write_txt_file(new_img_name, area_n_text, angle=0)
    logging.info(f'Resultado da síntese salvo em {outfpath}.')
    return new_img_name


# Chama as funções de ruído e de multiplicação para cada imagem.
def noise_mask(tipo_doc, img_name, area_n_text):
    mask_name = 'mask_' + img_name
    blur_mask(mask_name, paths.path_mask, tipo_doc)
    mult_img(mask_name, img_name, tipo_doc, area_n_text, param=150)


# Faz a função de main() desse arquivo.
def control_mask_gen(tipo_doc, json_arq, img_id, angle):
    img_name = next(paths.path_entrada.glob(f'{img_id}.*')).name
    inicio = time.time()
    area_n_text = text_mask_generator(tipo_doc, json_arq, img_name, angle)
    noise_mask(tipo_doc, img_name, area_n_text)
    fim = time.time()
    tempo = fim - inicio
    logging.debug(f"Tempo de execução para geração da máscara: {str(tempo)}.")
