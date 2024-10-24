from django.contrib.auth import get_user_model
from django.db import models

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_date_returned = models.DateField()
    actual_date_returned = models.DateField()
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    def __str__(self):
        return f"Borrowing of {self.book.title} by {self.user.username} on {self.borrow_date}"

