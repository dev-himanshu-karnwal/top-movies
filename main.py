from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Movie>: {self.title}'


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g. 7.5",
                        validators=[DataRequired(message='Please provide Rating'), NumberRange(min=1, max=10, message='Rating can only be from 1 to 10')])
    review = StringField(label="Your Review", validators=[
                         DataRequired(message='Please provide Review')])
    submit = SubmitField(label="Done")


class FindMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[
                        DataRequired(message='Enter movie title to search for it')])
    submit = SubmitField(label="Search Movies")


@app.route("/")
def home():
    movies = db.session.execute(
        db.select(Movie).order_by(Movie.rating).order_by(Movie.year)).scalars().all()

    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()

    return render_template("index.html", movies=movies, number_of_movies=len(movies))


@app.route('/edit', methods=['POST', 'GET'])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    if request.method == 'POST':
        if form.validate_on_submit():
            movie.rating = float(form.rating.data)
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))

    return render_template("edit.html", movie=movie, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add():
    form = FindMovieForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            endpoint = "https://api.themoviedb.org/3/search/movie"
            params = {
                "query": request.form.get('title'),
                "include_adult": True,
            }
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer authorization-token"
            }
            response = requests.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            movies = response.json()['results']

            return render_template('select.html', movies=movies)

    return render_template('add.html', form=form)


@app.route('/find')
def find():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        endpoint = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer authorization-token"
        }
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()

        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{'https://image.tmdb.org/t/p/original'}{data['poster_path']}",
            description=data["overview"]
        )

        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
