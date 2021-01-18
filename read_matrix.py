import pickle
from app import Cinema

for cinema in Cinema.query.all():
    movie_detail = [cinema.cinema, cinema.movie, cinema.city]
    movie_detail = '_'.join(movie_detail)
    for show_time in cinema.showtimes.split(', '):
        seat_matrix_file = movie_detail + '_' + show_time

        with open('seat_availability_matrix/%s' % seat_matrix_file, 'rb') as file:
            print(seat_matrix_file)
            seat_matrix = pickle.load(file)
            print(seat_matrix)
