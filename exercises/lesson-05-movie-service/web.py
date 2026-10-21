"""Веб-слой: принимает HTTP-запросы и показывает страницы. Решения принимает сервис."""
from flask import Flask, redirect, render_template, request, url_for


def create_app(service) -> Flask:
    app = Flask(__name__)

    def page(error=None, status=200):
        query = request.args.get('q', '')
        tag = request.args.get('tag')
        movies = service.find(query) if query else service.movies(tag)
        return render_template('index.html', movies=movies, tags=service.all_tags(), current=tag,
                               query=query, error=error), status

    @app.get('/')
    def index():
        return page()

    @app.post('/movies')
    def add_movie():
        try:
            year = int(request.form.get('year') or 0)
            tags = request.form.get('tags', '').split(',')
            service.add_movie(request.form.get('title', ''), year, request.form.get('description', ''), tags)
        except ValueError as error:
            return page(str(error), 400)
        return redirect(url_for('index'))

    @app.get('/api/search')
    def api_search():
        return {'movies': service.find(request.args.get('q', ''))}

    return app
