"""Окно утилиты: открыть журнал, разобрать записи моделью, сохранить результат в Excel."""
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from journal_ai import process_journal, write_summary
from journal_io import read_journal, save_results
from local_llm import load_chat

ROOT = Path(__file__).resolve().parent


class JournalApp:
    def __init__(self, window: tk.Tk, model):
        self.window = window
        self.model = model
        self.path = None
        self.entries, self.results, self.summary = [], [], ''
        # Модель работает в отдельном потоке и сообщает о ходе работы через очередь.
        self.events = queue.Queue()
        window.title('Журнал проделок кота')
        buttons = ttk.Frame(window, padding=8)
        buttons.pack(fill='x')
        self.open_button = ttk.Button(buttons, text='Открыть журнал', command=self.open_file)
        self.run_button = ttk.Button(buttons, text='Разобрать', command=self.start, state='disabled')
        self.save_button = ttk.Button(buttons, text='Сохранить в Excel', command=self.save, state='disabled')
        for button in (self.open_button, self.run_button, self.save_button):
            button.pack(side='left', padx=4)
        self.status = ttk.Label(buttons, text='Откройте файл журнала')
        self.status.pack(side='left', padx=12)
        self.table = ttk.Treeview(window, columns=('date', 'author', 'text', 'category', 'severity'),
                                  show='headings', height=12)
        for column, title, width in (('date', 'Дата', 90), ('author', 'Кто', 90), ('text', 'Что случилось', 420),
                                     ('category', 'Категория', 100), ('severity', 'Серьёзность', 90)):
            self.table.heading(column, text=title)
            self.table.column(column, width=width)
        self.table.pack(fill='both', expand=True, padx=8)
        self.text = tk.Text(window, height=7, wrap='word')
        self.text.pack(fill='x', padx=8, pady=8)

    def open_file(self):
        name = filedialog.askopenfilename(initialdir=ROOT / 'data', filetypes=[('Excel', '*.xlsx')])
        if not name:
            return
        self.path = Path(name)
        self.entries = read_journal(self.path)
        self.show(self.entries)
        self.status.config(text=f'Записей: {len(self.entries)}')
        self.run_button.config(state='normal')

    def show(self, rows):
        self.table.delete(*self.table.get_children())
        for row in rows:
            self.table.insert('', 'end', values=(row['date'], row['author'], row['text'],
                                                 row.get('category', ''), row.get('severity', '')))

    def start(self):
        for button in (self.open_button, self.run_button, self.save_button):
            button.config(state='disabled')
        self.status.config(text='Модель разбирает записи...')
        threading.Thread(target=self.work, daemon=True).start()
        self.window.after(100, self.poll)

    def work(self):
        try:
            results = process_journal(self.model, self.entries,
                                      lambda done, total: self.events.put(('progress', f'{done} из {total}')))
            self.events.put(('progress', 'сводка...'))
            self.events.put(('done', results, write_summary(self.model, results)))
        except Exception as error:  # Показываем любую ошибку в окне, а не только в консоли.
            self.events.put(('error', str(error)))

    def poll(self):
        # Окно меняем только здесь, в основном потоке tkinter.
        while not self.events.empty():
            kind, *data = self.events.get()
            if kind == 'progress':
                self.status.config(text='Разобрано: ' + data[0])
            elif kind == 'done':
                self.results, self.summary = data
                self.show(self.results)
                self.text.delete('1.0', 'end')
                self.text.insert('1.0', self.summary)
                self.status.config(text='Готово')
                self.open_button.config(state='normal')
                self.save_button.config(state='normal')
                return
            else:
                messagebox.showerror('Ошибка', data[0])
                self.open_button.config(state='normal')
                return
        self.window.after(100, self.poll)

    def save(self):
        save_results(self.path, self.results, self.summary)
        messagebox.showinfo('Сохранено', f'Лист "Разбор" записан в {self.path.name}')


def main():
    with load_chat() as model:
        window = tk.Tk()
        window.geometry('900x560')
        JournalApp(window, model)
        window.mainloop()


if __name__ == '__main__':
    main()
