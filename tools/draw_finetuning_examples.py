"""Рисуем числовые примеры для дополнительного урока; модель не запускается."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SCALE = 2
BG, INK, MUTED = '#f5f7fb', '#18334b', '#526579'
BLUE, GREEN, ORANGE = '#dfeaff', '#d9f1e5', '#fff0d5'
FONTS = Path('C:/Windows/Fonts')


def canvas(height, title, subtitle):
    image = Image.new('RGB', (960, height * SCALE), BG)
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=15, bold=False, fill=INK):
        font = ImageFont.truetype(str(FONTS / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size * SCALE)
        box = draw.textbbox((x*SCALE, y*SCALE), value, font=font)
        assert box[2] <= 950 and box[3] <= height*SCALE, (title, value, box)
        draw.text((x*SCALE, y*SCALE), value, font=font, fill=fill)

    def card(x, y, w, h, color):
        draw.rounded_rectangle((x*SCALE, y*SCALE, (x+w)*SCALE, (y+h)*SCALE), radius=12*SCALE,
                               fill=color, outline='#c7d3df', width=SCALE)

    def matrix(x, y, rows, color=BLUE, cell=40):
        for i, row in enumerate(rows):
            for j, number in enumerate(row):
                card(x+j*cell, y+i*cell, cell-3, cell-3, color)
                text(x+j*cell+10, y+i*cell+5, str(number), 18, True)

    text(20, 14, title, 21, True)
    text(20, 45, subtitle, 13, fill=MUTED)
    return image, text, card, matrix


def draw_all(output):
    output.mkdir(parents=True, exist_ok=True)
    image, t, c, m = canvas(380, 'Как слой считает по матрице', 'Вымышленные числа: один слой, два входа.')
    t(30, 83, 'Веса W', 16, True)
    t(175, 83, 'Вход x', 16, True)
    t(315, 83, 'Выход y', 16, True)
    m(30, 114, [[1, 2], [3, 4]])
    t(126, 132, '*', 24)
    m(180, 114, [[2], [1]], ORANGE)
    t(250, 132, '=', 24)
    m(320, 114, [[4], [10]], GREEN, 48)
    c(20, 228, 440, 104, '#ffffff')
    t(33, 240, 'Строка 1:  1 * 2 + 2 * 1 = 4', 17, True)
    t(33, 280, 'Строка 2:  3 * 2 + 4 * 1 = 10', 17, True)
    t(20, 347, 'Это внутренние числа, не готовые категории.', 14, fill=MUTED)
    image.save(output/'finetuning-matrix.png')

    image, t, c, m = canvas(530, 'Из двух матриц - поправка LoRA', 'Для счета на бумаге: r = 1, alpha = 1.')
    t(25, 80, 'B: 2 x 1', 16, True)
    t(162, 80, 'A: 1 x 2', 16, True)
    t(324, 80, 'BA: 2 x 2', 16, True)
    m(27, 112, [[2], [1]], GREEN)
    t(100, 126, '*', 24)
    m(161, 112, [[1, -1]], GREEN, 46)
    t(280, 126, '=', 24)
    m(325, 112, [[2, -2], [1, -1]], ORANGE, 46)
    c(20, 222, 440, 70, '#ffffff')
    t(32, 231, 'Первая строка:  2 * [1, -1] = [2, -2]', 15)
    t(32, 260, 'Вторая строка:  1 * [1, -1] = [1, -1]', 15)
    t(25, 315, 'База W', 16, True)
    t(170, 315, '+ поправка', 16, True)
    t(338, 315, '= W_new', 16, True)
    m(25, 347, [[1, 2], [3, 4]])
    t(127, 366, '+', 24)
    m(177, 347, [[2, -2], [1, -1]], ORANGE)
    t(286, 366, '=', 24)
    m(345, 347, [[3, 0], [4, 3]], GREEN)
    t(20, 455, 'Тот же вход [2, 1]:', 16, True)
    t(20, 483, 'база дает [4, 10], с поправкой - [6, 11].', 16)
    image.save(output/'finetuning-lora.png')

    image, t, c, m = canvas(470, 'У каждого файла своя работа', 'Одно правило проверяем на разных формулировках.')
    for y, name, phrase, color, action in (
        (83, 'train.jsonl', 'Еще на неделю', GREEN, 'Ответ используется для изменения A и B.'),
        (201, 'dev.jsonl', 'Недели сверху хватит', BLUE, 'По ошибкам выбираем настройки опыта.'),
        (319, 'exam.jsonl', 'Срок увеличьте на неделю', ORANGE, 'Проверяем уже выбранный вариант.')):
        c(20, y, 440, 103, color)
        t(32, y+8, name, 17, True)
        t(32, y+37, '"'+phrase+'"', 17)
        t(32, y+71, action, 14)
    t(20, 437, 'В каждом файле: с книгой renew, без нее clarify.', 14, fill=MUTED)
    image.save(output/'finetuning-files.png')

    image, t, c, m = canvas(420, 'Что читаем и где считаем ошибку', 'Условные номера токенов, не словарь Qwen.')
    t(20, 83, 'Инструкция и вход', 16, True)
    t(282, 83, 'Правильный ответ', 16, True)
    t(20, 118, 'input_tokens', 15, True)
    for j, value in enumerate((11, 12, 13, 21, 22)):
        c(20+j*89, 149, 80, 49, BLUE if j<3 else GREEN)
        t(44+j*89, 158, str(value), 20, True)
    t(20, 218, 'labels', 15, True)
    for j, value in enumerate((-100, -100, -100, 21, 22)):
        c(20+j*89, 249, 80, 49, '#e4e8ee' if j<3 else GREEN)
        t(31+j*89, 258, str(value), 19, True)
    t(20, 323, '-100: позицию пропускаем в функции ошибки.', 15)
    t(20, 354, 'Вход модель учитывает при предсказании ответа.', 15)
    t(20, 385, 'Сдвиг на следующий токен делает библиотека.', 14, fill=MUTED)
    image.save(output/'finetuning-mask.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    draw_all(parser.parse_args().output)
