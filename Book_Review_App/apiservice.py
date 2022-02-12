import requests

# Get book data from google api
def get_book_data(isbn):
    google_api_response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
    google_api_data = google_api_response.json()['items'][0]['volumeInfo']
    return {
            'title': google_api_data['title'],
            'author': ' '.join(google_api_data['authors']),
            'publishedDate': google_api_data['publishedDate'],
            'ISBN_10': list(filter(lambda isbn:isbn["type"]=="ISBN_10",google_api_data['industryIdentifiers']))[0]["identifier"],
            'ISBN_13': list(filter(lambda isbn:isbn["type"]=="ISBN_13",google_api_data['industryIdentifiers']))[0]["identifier"],
            'reviewCount': google_api_data['ratingsCount'],
            'averageRating': google_api_data['averageRating']
        }
