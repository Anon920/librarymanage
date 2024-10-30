from rest_framework import serializers

from books.serializers import BookSerializer
from borrowing.models import Borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Borrowing
        fields = "id", "borrow_date", "expected_date_returned", "actual_date_returned", "book", "user"
        read_only_fields = ("borrow_date", "actual_date_returned", "user")

    def validate(self, data):
        book = data["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")
        return data

    def create(self, validated_data):
        book = validated_data['book']
        book.inventory -= 1
        book.save()

        borrowing = Borrowing.objects.create(
            **validated_data,
            user=self.context['request'].user
        )
        return borrowing


class BorrowingRetrieveSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = "id", "borrow_date", "expected_date_returned", "actual_date_returned", "book", "user"
