from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from books.serializers import BookSerializer

from books.models import Book

BOOK_URL = reverse("library:book-list")


def sample_book(**additional) -> Book:
    defaults = {
        "title": "Book title",
        "author": "Author Sample",
        "cover": "SOFT",
        "inventory": 10,
        "daily_fee": Decimal("1.04")
    }
    defaults.update(additional)

    return Book.objects.create(**defaults)


class UnAuthenticatedBookAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books(self) -> None:
        sample_book()
        sample_book(title="Test2", cover="HARD")
        sample_book(title="Test3", inventory=11)

        response = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_book(self) -> None:
        book = sample_book()

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.get(url)

        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_unauthenticated(self) -> None:
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": Decimal("2.04")
        }

        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_book_unauthenticated(self) -> None:
        book = sample_book()
        payload = {
            "title": "Updated Book",
            "author": "Updated Author",
            "cover": "HARD",
            "inventory": 15,
            "daily_fee": Decimal("3.04")
        }

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='testuser',
            password='testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_books(self) -> None:
        sample_book()
        sample_book(title="Test2", cover="HARD")
        sample_book(title="Test3", inventory=11)

        response = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_book(self) -> None:
        book = sample_book()

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.get(url)

        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_authenticated(self) -> None:
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": Decimal("2.04")
        }

        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_book_authenticated(self) -> None:
        book = sample_book()
        payload = {
            "title": "Updated Book",
            "author": "Updated Author",
            "cover": "HARD",
            "inventory": 15,
            "daily_fee": Decimal("3.04")
        }

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_book_authenticated(self) -> None:
        book = sample_book()

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            email="user@test.com",
            password="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_books(self) -> None:
        sample_book()
        sample_book(title="Test2", cover="HARD")
        sample_book(title="Test3", inventory=11)

        response = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_admin(self) -> None:
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": Decimal("2.04")
        }

        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(response.data['title'], payload['title'])

    def test_update_book_admin(self) -> None:
        book = sample_book()
        payload = {
            "title": "Updated Book",
            "author": "Updated Author",
            "cover": "HARD",
            "inventory": 15,
            "daily_fee": Decimal("3.04")
        }

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.title, payload['title'])
        self.assertEqual(book.author, payload['author'])
        self.assertEqual(book.cover, payload['cover'])
        self.assertEqual(book.inventory, payload['inventory'])
        self.assertEqual(book.daily_fee, payload['daily_fee'])

    def test_partial_update_book_admin(self) -> None:
        book = sample_book()
        payload = {
            "inventory": 15
        }

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.inventory, payload['inventory'])

    def test_destroy_book_admin(self) -> None:
        book = sample_book()

        url = reverse("library:book-detail", kwargs={"pk": book.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)
