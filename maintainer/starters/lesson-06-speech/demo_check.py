from pathlib import Path
from types import SimpleNamespace

from speech import read_wav, transcribe

ROOT = Path(__file__).resolve().parent


class ExampleWhisper:
    """Подставной объект вместо Whisper. Время в сегментах - в сотых долях секунды, как у pywhispercpp."""

    def __init__(self):
        self.calls = []

    def transcribe(self, audio, **settings):
        self.calls.append(settings)
        return [SimpleNamespace(t0=0, t1=200, text=' Здравствуйте.'),
                SimpleNamespace(t0=744, t1=1164, text=' Две недели назад я купила у вас электрический чайник,')]


def check_exercise():
    model = ExampleWhisper()
    lines = transcribe(model, [0.0] * 16000)
    assert model.calls[0].get('language') == 'ru', 'Укажите язык речи: language=ru'
    assert lines[0] == '[00:00] Здравствуйте.', lines[0]
    assert lines[1].startswith('[00:07] Две недели'), 'Переведите сотые доли секунды в минуты и секунды'
    assert len(read_wav(ROOT / 'data' / 'call.wav')) > 16000 * 20, 'Запись длится больше 20 секунд'
    return lines[1]


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
