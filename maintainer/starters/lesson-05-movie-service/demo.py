import json
from pathlib import Path

from demo_check import check_exercise
from local_llm import load_embedder
from search import KeywordSearch, SemanticSearch

ROOT = Path(__file__).resolve().parent
QUERIES = ['путешествие во времени', 'кино про хоккей', 'смешное про любовь на работе', 'добрый мультик перед сном']


def main():
    try:
        check_exercise()
        movies = json.loads((ROOT / 'data' / 'movies.json').read_text(encoding='utf-8'))
        for number, movie in enumerate(movies, start=1):
            movie['id'] = number
        keywords = KeywordSearch()
        with load_embedder() as model:
            semantic = SemanticSearch(model)
            for query in QUERIES:
                print(query)
                print('  по словам:', [movie['title'] for movie in keywords.find(query, movies)])
                print('  по смыслу:', [movie['title'] for movie in semantic.find(query, movies)])
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
