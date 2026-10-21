from pathlib import Path

from similar import build_index, find_similar, read_requests

ROOT = Path(__file__).resolve().parent
QUERY = 'товар пришёл сломанным'


class ExampleEmbedder:
    """Подставной объект вместо модели: каждое измерение вектора отвечает за одну тему."""
    TOPICS = [('слома', 'разбит', 'не включается'), ('опозда', 'позже', 'не пришла'),
              ('дважды', 'два раза'), ('размер',), ('кабинет',)]

    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(text)
        lowered = text.casefold()
        return [1.0 + sum(word in lowered for word in words) * 5 for words in self.TOPICS]


def check_exercise():
    model = ExampleEmbedder()
    index = build_index(model, read_requests(ROOT / 'data' / 'requests.json'))
    found = find_similar(model, QUERY, index, top=3)
    assert model.calls[-1].endswith(QUERY), 'Сначала превратите в вектор сам запрос'
    assert len(found) == 3, 'Верните столько результатов, сколько указано в top'
    scores = [score for score, _ in found]
    assert scores == sorted(scores, reverse=True), 'Сначала самые близкие обращения'
    assert all(isinstance(record, dict) for _, record in found), 'Возвращаем пары (близость, обращение)'
    return found[0][1]['text']


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
