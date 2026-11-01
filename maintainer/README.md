# Сопровождение курса

Тексты уроков пишутся в Obsidian (папка `Agent Harness Workshop/Расширенный курс 1` хранилища DEVPOINTVAULT). Код каркасов и эталонные решения лежат здесь, в `maintainer`. Схемы рисуются скриптом из `tools`.

```text
maintainer/starters/<урок>    исходники каркаса без общих файлов
maintainer/solutions/<урок>   эталонные решения, читателю не выдаются
maintainer/make_data.py       пересборка журналов Excel
tools/model_runtime/local_llm.py   общий модуль, копируется в каркасы
tools/course-map.json         уроки, модели, зависимости, ожидаемый вывод
```

## Обновить курс

В корне репозитория, в окружении с установленными зависимостями курса:

```powershell
python tools/draw_course_flows.py --vault 'путь-к-DEVPOINTVAULT'
python tools/build_starters.py --vault 'путь-к-DEVPOINTVAULT'
python tools/export_obsidian.py --vault 'путь-к-DEVPOINTVAULT'
python tools/check_course.py
python tools/check_solutions.py
```

`draw_course_flows.py` рисует GIF и статичные PNG шириной 480 пикселей в папку `Уроки/Материалы`. `build_starters.py` собирает каждый каркас: исходники, `local_llm.py`, `get_models.py`, `requirements.txt`, `.gitignore` и `TASK.md`, который составляется из разделов урока ("Где мы", "Напишите сами", "Подключите", "Угадайте до запуска", "Запустим", "Попробуйте сломать"). ZIP с фиксированной датой файлов записывается рядом с уроками в Obsidian. `export_obsidian.py` выгружает страницы, схемы и архивы и распаковывает каркасы в `exercises`. Файл, изменённый в репозитории вручную, экспорт не перезапишет: перенесите правку в источник.

## Что проверяется

Отдельное дополнение по дообучению использует независимый пример `maintainer/fine_tuning_demo`. Подготовить его архив и выгрузить только эту страницу можно без перезаписывания остальных уроков:

```powershell
python tools/build_fine_tuning_supplement.py --vault 'путь-к-хранилищу'
python tools/export_obsidian.py --vault 'путь-к-хранилищу' --only course/fine-tuning-dialogues.md
python tools/check_fine_tuning_supplement.py
```

Параметр `--only` сохраняет прежние записи манифеста экспорта и по-прежнему запрещает перезапись вручную измененного файла. Само обучение дополнения этими командами не запускается.

`check_course.py` проверяет пунктуацию и ссылки в Markdown, синтаксис Python, совпадение каждого ZIP с папкой `exercises`, состав `requirements.txt`, совпадение `local_llm.py` с общим модулем и то, что незавершённые `demo_check.py` и `demo.py` выводят подсказку `Допишите`. Модели и сеть не используются.

`check_solutions.py` во временных копиях подставляет эталонные решения, запускает `tests/test_lesson.py` и `demo_check.py` и сверяет вывод с полем `expected` из карты курса. Это проверка каркасов и тестов, а не качества моделей.

Проверка на настоящих моделях выполняется вручную: скачайте модели в папку вне репозитория, задайте `AGENT_MODELS_DIR` и запустите `demo.py` в копиях с решениями. Числа в уроках взяты из таких запусков.
