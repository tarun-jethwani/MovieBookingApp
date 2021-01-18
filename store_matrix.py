from app import Cinema
import pickle


def build_seat_matrix():
    seat_matrix = []
    for i in range(5):
        seat_row = []
        for j in range(5):
            seat_row.append(1)
        seat_matrix.append(seat_row)
    return seat_matrix


for cinema in Cinema.query.all():
    movie_detail = [cinema.cinema, cinema.movie, cinema.city]
    movie_detail = '_'.join(movie_detail)
    for show_time in cinema.showtimes.split(', '):
        seat_matrix_file = movie_detail + '_' + show_time
        with open('seat_availability_matrix/%s' % seat_matrix_file, 'wb') as file:
            pickle.dump(build_seat_matrix(), file, protocol=pickle.HIGHEST_PROTOCOL)





