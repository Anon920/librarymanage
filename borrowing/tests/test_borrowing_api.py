import os
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowing.models import Borrowing

BORROWINGS_URL = reverse("borrowing:borrowing-list")


def get_detail(borrowing_id: int) -> str:
    return reverse("borrowing:borrowing-detail", args=[borrowing_id])


def get_return_url(borrowing_id: int) -> str:
    return reverse("borrowing:borrowing-return-borrowings", args=[borrowing_id])


def sample_user(email, password):
    return get_user_model().objects.create_user(email, password)


def sample_book(**additional) -> Book:
    defaults = {
        "title": "Book title",
        "author": "Author Sample",
        "cover": "SOFT",
        "inventory": 10,
        "daily_fee": Decimal("1.04"),
    }
    defaults.update(additional)

    return Book.objects.create(**defaults)


@patch("stripe.checkout.Session.create")
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def sample_borrowing(
        mocked_notify,
        mock_create_session,
        user,
        book,
        **additional
) -> Borrowing:
    mock_create_session.return_value = SessionStripe(
        id="fake_session_id", url="https://fake-stripe-url.com"
    )
    defaults = {
        "user": user,
        "book": book,
        "expected_return_date": date.today() + timedelta(days=7),
    }
    defaults.update(additional)

    return Borrowing.objects.create(**defaults)


class SessionStripe:
    def __init__(self, id: str, url: str) -> None:
        self.id = id
        self.url = url


class UnAuthenticatedBorrowingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_borrowings_forbidden(self):
        response = self.client.get(BORROWINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_borrowing_forbidden(self):
        book = sample_book()
        data = {
            "book": book.id,
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        response = self.client.post(BORROWINGS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_return_borrowing_forbidden(self):
        user = sample_user(email="test@test.com", password="password")
        book = sample_book()
        borrowing = sample_borrowing(user=user, book=book)
        response = self.client.post(get_return_url(borrowing.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingTests(TestCase):
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def setUp(self, mocked_notify):
        self.user = sample_user(email="test@test.com", password="password")
        self.user_2 = sample_user(email="test1@test1.com", password="password")
        self.book = sample_book()

        sample_borrowing(user=self.user, book=self.book)
        sample_borrowing(user=self.user_2, book=self.book)

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("stripe.checkout.Session.create")
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_create_borrowing(self, mocked_notify, mock_create_session):
        data = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        mock_create_session.return_value = SessionStripe(
            id="fake_session_id", url="https://fake-stripe-url.com"
        )
        response = self.client.post(BORROWINGS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 3)
        self.assertEqual(Borrowing.objects.first().user, self.user)

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_list_borrowings(self, mocked_notify):
        response = self.client.get(BORROWINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_borrowing_detail(self, mocked_notify):
        borrowing = sample_borrowing(user=self.user, book=self.book)
        response = self.client.get(get_detail(borrowing.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.id)

    @patch("stripe.checkout.Session.create")
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_inventory_decrease_on_borrow(self, mocked_notify, mock_create_session):
        initial_inventory = self.book.inventory

        borrowing_data = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
        }

        mock_create_session.return_value = SessionStripe(
            id="fake_session_id", url="https://fake-stripe-url.com"
        )
        response = self.client.post(BORROWINGS_URL, borrowing_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_create_borrowing_out_of_stock(self, mocked_notify):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        response = self.client.post(BORROWINGS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This book is out of stock.', response.json()['book'])
