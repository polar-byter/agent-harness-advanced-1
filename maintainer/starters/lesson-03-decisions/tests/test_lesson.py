import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from decisions import ask_choice, decide, read_json, route
from demo_check import ExampleModel
from frida_client import ask_frida
from jev_client import ask_jev, openrouter_key

# Ответ в виде примера из документации OpenRouter Decisions API, сокращён до двух вопросов.
JEV_RESPONSE = {'id': 'gen-dec-1', 'model': 'typesafe/jev-1.14', 'provider': 'TypeSafe', 'answers': {
    'queue': {'type': 'choice', 'choice': 'доставка', 'confidence': 1.0,
              'probabilities': {'доставка': 1.0, 'оплата': 0.0}},
    'damaged': {'type': 'noul', 'noul': 0.02}}, 'usage': {'input_tokens': 428, 'output_tokens': 73}}


class FakeJev(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        FakeJev.received.append((self.path, self.headers['Authorization'], json.loads(body)))
        data = json.dumps(JEV_RESPONSE, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class FakeJudge:
    """Подставная FRIDA: запоминает запрос и отвечает в её формате."""

    def __init__(self):
        self.requests = []

    def judge(self, request):
        self.requests.append(request)
        return {'answers': {'queue': {'type': 'choice', 'choice': 'доставка', 'confidence': 0.9,
                                      'probabilities': {'доставка': 0.97, 'оплата': 0.03}}}}


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.model = ExampleModel()
        self.questions = read_json(ROOT / 'data' / 'questions.json')

    def test_choice_answer(self):
        answer = ask_choice(self.model, 'Курьер опоздал на три часа', self.questions['queue'])
        self.assertEqual(answer['type'], 'choice')
        self.assertEqual(answer['choice'], 'доставка')
        self.assertEqual(answer['confidence'], answer['probabilities']['доставка'])
        self.assertAlmostEqual(sum(answer['probabilities'].values()), 1.0)

    def test_decide_and_route(self):
        questions = dict(self.questions, damaged={'type': 'noul', 'instructions': 'Товар пришёл повреждённым?'})
        answers = decide(self.model, 'Чайник сломался, верните деньги', questions)
        self.assertEqual(set(answers), {'queue', 'damaged'})
        self.assertGreater(answers['damaged']['noul'], 0.5)
        self.assertEqual(route(answers, threshold=0.5), answers['queue']['choice'])
        self.assertEqual(route(answers, threshold=1.01), 'человеку')

    def test_jev_request(self):
        server = HTTPServer(('127.0.0.1', 0), FakeJev)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/api/alpha/decisions'
            answers = ask_jev('Курьер опоздал на три часа', self.questions, api_key='test-key', url=url)
        finally:
            server.shutdown()
            server.server_close()
        path, authorization, body = FakeJev.received[-1]
        self.assertEqual((path, authorization), ('/api/alpha/decisions', 'Bearer test-key'))
        self.assertEqual(body, {'model': 'typesafe/jev-1.14', 'state': 'Курьер опоздал на три часа',
                                'questions': self.questions})
        self.assertEqual(route(answers), 'доставка')

    def test_jev_needs_key(self):
        with self.assertRaises(ValueError):
            ask_jev('текст', self.questions, api_key='')

    def test_key_from_main_course_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'connection.json'
            path.write_text(json.dumps({'provider': 'openrouter', 'model': 'openrouter/free',
                                        'api_key': 'from-file'}), encoding='utf-8')
            with mock.patch.dict(os.environ, {'HARNESS_CONNECTION_FILE': str(path)}):
                os.environ.pop('OPENROUTER_API_KEY', None)
                self.assertEqual(openrouter_key(), 'from-file')
                path.write_text(json.dumps({'provider': 'ollama', 'model': 'qwen3:0.6b'}), encoding='utf-8')
                with self.assertRaises(ValueError):
                    openrouter_key()

    def test_frida_request(self):
        judge = FakeJudge()
        answers = ask_frida(judge, 'Курьер опоздал на три часа', self.questions)
        self.assertEqual(judge.requests[-1], {'state': 'Курьер опоздал на три часа', 'questions': self.questions})
        self.assertEqual(route(answers, threshold=0.7), 'доставка')
        self.assertEqual(route(answers), 'доставка')


if __name__ == '__main__':
    unittest.main()
