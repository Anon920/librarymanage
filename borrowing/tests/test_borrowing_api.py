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

