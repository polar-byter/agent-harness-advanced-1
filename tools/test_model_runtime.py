"""Тесты общего модуля local_llm.py на подставных объектах: без библиотек моделей и без сети."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'model_runtime'))
import local_llm


class FakeModel:
    def __init__(self, content, finish='stop'):
        self.content, self.finish, self.calls = content, finish, []

    def create_chat_completion(self, **settings):
        self.calls.append(settings)
        return {'choices': [{'finish_reason': self.finish, 'message': {'content': self.content}}]}


class RuntimeTests(unittest.TestCase):
    def test_models_dir_from_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            os.environ['AGENT_MODELS_DIR'] = folder
            try:
                self.assertEqual(local_llm.models_dir(), Path(folder))
                with self.assertRaises(FileNotFoundError):
                    local_llm.require('embed')
                # Скачана только маленькая модель - берём её.
                local_llm.model_path('chat-small').write_bytes(b'')
                self.assertEqual(local_llm.chat_model_name(), 'chat-small')
            finally:
                del os.environ['AGENT_MODELS_DIR']

    def test_clean_answer(self):
        response = FakeModel('<think>\n\n</think>\n\nОтвет').create_chat_completion()
        self.assertEqual(local_llm.clean_answer(response), 'Ответ')
        with self.assertRaises(ValueError):
            local_llm.clean_answer(FakeModel('Обрыв', 'length').create_chat_completion())
        with self.assertRaises(ValueError):
            local_llm.clean_answer(FakeModel('<think>x</think>').create_chat_completion())

    def test_ask_text_and_schema(self):
        model = FakeModel('Текст')
        self.assertEqual(local_llm.ask(model, 'Правило', 'Данные'), 'Текст')
        settings = model.calls[0]
        self.assertEqual(settings['messages'], [{'role': 'system', 'content': 'Правило /no_think'},
                                                {'role': 'user', 'content': 'Данные'}])
        self.assertNotIn('response_format', settings)
        schema = {'type': 'object', 'properties': {'n': {'type': 'integer'}}}
        model = FakeModel('{"n": 3}')
        self.assertEqual(local_llm.ask(model, 'П', 'Д', schema=schema, max_tokens=8), {'n': 3})
        self.assertEqual(model.calls[0]['response_format'], {'type': 'json_object', 'schema': schema})
        self.assertEqual(model.calls[0]['max_tokens'], 8)

    def test_catalog(self):
        for name, (filename, url, size) in local_llm.MODELS.items():
            self.assertTrue(url.startswith('https://huggingface.co/') and url.endswith(filename), name)
            self.assertGreater(size, 0)


if __name__ == '__main__':
    unittest.main()
