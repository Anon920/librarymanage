from rest_framework import serializers

from books.serializers import BookSerializer
from borrowing.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = "id", "borrow_date", "expected_date_returned", "actual_date_returned", "book", "user"
        read_only_fields = ("borrow_date", "expected_date_returned", "actual_date_returned", "user")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BorrowingRetrieveSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
