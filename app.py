from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = "bookingapp"
Bootstrap(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tarunjethwani@localhost/MovieBookingApp'
app.debug = True

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True)
    password = db.Column(db.String(100))
    city = db.Column(db.String(15))

    def __init__(self, username, password, city):
        self.username = username
        self.password = password
        self.city = city


class Cinema(db.Model):
    __tablename__ = 'cinemas'
    id = db.Column(db.Integer, primary_key=True)
    cinema = db.Column(db.String(20), unique=True)
    movie = db.Column(db.String(20))
    city = db.Column(db.String(15))
    showtimes = db.Column(db.Text)

    def __init__(self, cinema, movie, city, showtimes):
        self.cinema = cinema
        self.movie = movie
        self.city = city
        self.showtimes = showtimes


class Bookings(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(10))
    cinema = db.Column(db.String(20))
    movie = db.Column(db.String(20))
    city = db.Column(db.String(15))
    showtime = db.Column(db.String(10))
    seats = db.Column(db.Text)

    def __init__(self, user, cinema, movie, city, showtime, seats):
        self.user = user
        self.cinema = cinema
        self.movie = movie
        self.city = city
        self.showtime = showtime
        self.seats = seats


def read_seat_matrix(filename):
    with open('seat_availability_matrix/%s' % filename, 'rb') as file:
        seat_matrix = pickle.load(file)
    return seat_matrix


def calculate_seat_number(seat_matrix):
    data = []
    for i in range(len(seat_matrix)):
        new_row = []
        for j in range(len(seat_matrix[i])):
            new_row.append([seat_matrix[i][j], i * len(seat_matrix) + (j + 1)])
        data.append(new_row)
    return data


def seat_number_to_row_col_idx(row_height, col_width, seat_number):
    row_id = int(seat_number) // row_height
    col_id = int(seat_number) % col_width
    return row_id, col_id


def overwrite_seat_matrix(seat_matrix, row_height, col_width, seat_numbers):
    for seat_number in seat_numbers:
        row_id, col_id = seat_number_to_row_col_idx(row_height, col_width, seat_number)
        seat_matrix[row_id][col_id] = 0
    return seat_matrix


def update_seat_matrix(updated_seat_matrix, filename):
    with open('seat_availability_matrix/%s' % filename, 'wb') as file:
        pickle.dump(updated_seat_matrix, file, protocol=pickle.HIGHEST_PROTOCOL)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=3, max=10)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=3, max=20)])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/seats_availability/<string:movie_detail>', methods=['POST', 'GET'])
@login_required
def seats_availability(movie_detail):
    seat_matrix = read_seat_matrix(movie_detail)
    movie_detail = movie_detail.split('_')
    all_movies = set()
    data = calculate_seat_number(seat_matrix)
    for cinema in Cinema.query.all():
        all_movies.add(cinema.movie)
    return render_template('seat_availability.html', data=data, movie_detail=movie_detail, user=current_user.username,
                           all_movies=all_movies)


@app.route('/movie_dropdown/<string:movie>', methods=['GET'])
@login_required
def movie_dropdown(movie):
    cinemas = []
    all_movies = set()
    movie_detail = movie.split('_')
    for cinema in Cinema.query.all():
        all_movies.add(cinema.movie)

    if len(movie_detail) == 2:
        movie, city = movie_detail[0], movie_detail[1]
        for cinema in Cinema.query.filter_by(movie=movie, city=city):
            record = [cinema.cinema, cinema.city, cinema.showtimes.split(', ')]
            cinemas.append(record)
        return render_template('movie_details.html', cinemas=cinemas, movie=movie, all_movies=all_movies,
                               user=current_user.username, city=city)
    else:
        for cinema in Cinema.query.filter_by(movie=movie):
            record = [cinema.cinema, cinema.city, cinema.showtimes.split(', ')]
            cinemas.append(record)
        return render_template('movie_details.html', cinemas=cinemas, movie=movie, all_movies=all_movies,
                               user=current_user.username)


@app.route('/get_booking', methods=['POST'])
@login_required
def get_booking():
    cinema = request.form.get('cinema')
    movie = request.form.get('movie')
    city = request.form.get('city')
    show_time = request.form.get('show_time')

    filename = '_'.join([cinema, movie, city, show_time])

    seat_matrix = read_seat_matrix(filename)
    row_height = len(seat_matrix)
    col_width = len(seat_matrix[0])
    seat_numbers = request.form.getlist('seats')
    updated_seat_matrix = overwrite_seat_matrix(seat_matrix, row_height,
                                                col_width, seat_numbers)
    update_seat_matrix(updated_seat_matrix, filename)

    # Add booking details in Booking Model
    booking = Bookings(current_user.username, cinema, movie, city, show_time, ' ,'.join(seat_numbers))
    db.session.add(booking)
    db.session.commit()
    return redirect(url_for('show_bookings'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
        return '<h3> Invalid Username or password </h3>'

    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    current_city = current_user.city
    all_movies = set()
    current_movies = []
    for cinema in Cinema.query.filter_by(city=current_city).all():
        current_movies.append(cinema.movie)
    for cinema in Cinema.query.all():
        all_movies.add(cinema.movie)
    return render_template('dashboard.html', user=current_user.username, city=current_user.city, movies=current_movies,
                           all_movies=all_movies)


@app.route("/bookings")
@login_required
def show_bookings():
    bookings = Bookings.query.filter_by(user=current_user.username)
    booking_history = []
    for booking in bookings:
        booking_detail = [booking.cinema, booking.movie,
                          booking.city, booking.showtime, booking.seats]
        booking_history.append(booking_detail)

    booking_history.reverse()

    return render_template('bookings.html', user = current_user.username,
                           recent_booking=booking_history[0],
                           past_bookings=booking_history[1:])


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
