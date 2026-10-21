"""Рисуем передачу данных и изменение состояния в учебных примерах."""
import argparse
import math
import runpy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 480
HEIGHT = 650
INK = '#21384c'
MUTED = '#587083'
GREEN = '#147c70'
BLUE = '#315bb0'
PALE = '#e6f3ef'
FONTS = Path('C:/Windows/Fonts')


def font(size=17, bold=False):
    return ImageFont.truetype(str(FONTS / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size)


def paragraph(draw, text, position, width, size=17, color=INK, bold=False):
    """Переносим текст по словам; выход за отведённое место считаем ошибкой."""
    selected = font(size, bold)
    x, y = position
    for source_line in text.split('\n'):
        line = ''
        for word in source_line.split():
            assert draw.textlength(word, font=selected) <= width, word
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=selected) > width:
                draw.text((x, y), line, font=selected, fill=color)
                y += size + 6
                line = word
            else:
                line = candidate
        draw.text((x, y), line, font=selected, fill=color)
        y += size + 6
    return y


def panel(draw, box, heading, body, tint='white', size=17):
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=12, fill=tint, outline='#cbd8e1', width=1)
    y = paragraph(draw, heading, (left + 14, top + 9), right - left - 28, 16, MUTED, True)
    y = paragraph(draw, body, (left + 14, y + 5), right - left - 28, size)
    assert y <= bottom - 4, (heading, body, y, bottom)


def arrow(draw, points, color=GREEN, width=3):
    draw.line(points, fill=color, width=width, joint='curve')
    x, y = points[-1]
    previous = points[-2]
    angle = math.atan2(y - previous[1], x - previous[0])
    draw.polygon([(x, y), (x - 10 * math.cos(angle - .5), y - 10 * math.sin(angle - .5)),
                  (x - 10 * math.cos(angle + .5), y - 10 * math.sin(angle + .5))], fill=color)


def point_on_route(points, fraction):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    remaining = sum(lengths) * fraction
    for a, b, length in zip(points, points[1:], lengths):
        if remaining <= length:
            ratio = remaining / length if length else 0
            return a[0] + ratio * (b[0] - a[0]), a[1] + ratio * (b[1] - a[1])
        remaining -= length
    return points[-1]


def packet(draw, points, fraction, label):
    x, y = point_on_route(points, fraction)
    if fraction >= 1:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=GREEN)
        return
    selected = font(14, True)
    width = draw.textlength(label, font=selected) + 20
    left = max(6, min(WIDTH - width - 6, x - width / 2))
    draw.rounded_rectangle((left, y - 14, left + width, y + 15), 7, fill=BLUE)
    draw.text((left + 10, y - 11), label, font=selected, fill='white')


def base(title, subtitle):
    picture = Image.new('RGB', (WIDTH, HEIGHT), '#f3f7fa')
    draw = ImageDraw.Draw(picture)
    y = paragraph(draw, title, (20, 12), 440, 23, INK, True)
    assert y <= 77, title
    paragraph(draw, subtitle, (20, 80), 440, 14, MUTED)
    draw.line((20, 109, 460, 109), fill='#ccd8e1')
    return picture, draw


def draw_transfer(story, index, progress):
    scene = story['scenes'][index]
    picture, draw = base(story['title'], 'Учебный пример. Значения выбраны для объяснения.')
    paragraph(draw, f'{index + 1}/{len(story["scenes"])}. ' + scene['action'], (20, 120), 440, 19, INK, True)
    panel(draw, (20, 185, 460, 330), scene['source'], scene['before'])
    route = [(240, 331), (240, 395)]
    arrow(draw, route)
    packet(draw, route, progress, scene['packet'])
    arrived = progress >= 1
    panel(draw, (20, 397, 460, 552), scene['destination'],
          scene['after'] if arrived else scene.get('waiting', 'Данные ещё не переданы.'), PALE if arrived else 'white')
    y = paragraph(draw, scene['explanation'], (24, 568), 432, 16, MUTED)
    assert y <= 642, scene['explanation']
    return picture


def draw_summary(story):
    """Статичная версия показывает весь ход, а не последний кадр анимации."""
    picture, draw = base(story['title'], 'Краткая схема того же учебного примера.')
    scenes = story['scenes']
    top = 122
    row_height = min(116, 490 // len(scenes))
    for index, scene in enumerate(scenes):
        draw.ellipse((20, top + 5, 45, top + 30), fill=GREEN)
        draw.text((27, top + 6), str(index + 1), font=font(15, True), fill='white')
        y = paragraph(draw, scene['action'], (57, top), 400, 17, INK, True)
        y = paragraph(draw, scene.get('summary', scene['after']), (57, y + 1), 400, 16, MUTED)
        assert y <= top + row_height, (story['title'], scene['action'], 'summary overflow')
        top += row_height
    return picture


def save_animation(destination, frames, durations):
    destination.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(destination, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, disposal=2, optimize=True)


def render(story, vault, review_folder):
    destination = vault / story['path']
    frames, durations, keyframes = [], [], []
    count = len(story['scenes'])
    for index in range(count):
        for tick in range(10):
            progress = tick / 9
            frame = draw_transfer(story, index, progress)
            frames.append(frame)
            durations.append(3000 if tick == 9 else (600 if tick == 0 else 70))
        keyframes.append(frames[-1])
    save_animation(destination, frames, durations)
    draw_summary(story).save(destination.with_suffix('.png'))
    if review_folder:
        review_folder.mkdir(parents=True, exist_ok=True)
        sheet = Image.new('RGB', (WIDTH * 3, HEIGHT * math.ceil(count / 3)), 'white')
        for index, frame in enumerate(keyframes):
            sheet.paste(frame, ((index % 3) * WIDTH, (index // 3) * HEIGHT))
        sheet.save(review_folder / (destination.stem + '.png'))
    print(destination.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path, required=True)
    parser.add_argument('--only', help='Часть имени файла для одного рисунка')
    parser.add_argument('--review-folder', type=Path)
    args = parser.parse_args()
    stories = runpy.run_path(str(Path(__file__).with_name('course_flow_examples.py')))['STORIES']
    for story in stories:
        if not args.only or args.only in story['path']:
            render(story, args.vault, args.review_folder)


if __name__ == '__main__':
    main()
