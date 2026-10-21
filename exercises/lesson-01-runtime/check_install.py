import sys

from local_llm import models_dir, chat_model_name, model_path


def main():
    print('Python:', sys.version.split()[0])
    print('Интерпретатор:', sys.executable)
    try:
        import llama_cpp
    except (ImportError, OSError) as error:
        print('Библиотека пока не загрузилась:', error)
        return
    print('Библиотека загружена:', llama_cpp.__version__)
    print('Папка моделей:', models_dir())
    path = model_path(chat_model_name())
    print('Файл модели:', path.name, '- найден' if path.is_file() else '- пока не скачан')


if __name__ == '__main__':
    main()
