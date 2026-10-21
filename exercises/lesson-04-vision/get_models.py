"""Скачивает модели этого урока в общую папку моделей курса."""
import sys

from local_llm import download, models_dir

MODELS = ['vision', 'vision-proj']


def main():
    print('Папка моделей:', models_dir())
    # Run с параметром small скачает маленькую языковую модель вместо основной.
    small = 'small' in sys.argv[1:]
    download(*[('chat-small' if small and name == 'chat' else name) for name in MODELS])


if __name__ == '__main__':
    main()
