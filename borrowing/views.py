from datetime import date

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from borrowing.models import Borrowing

from borrowing.serializers import BorrowingListSerializer, BorrowingRetrieveSerializer, BorrowingSerializer, \
    BorrowingListAdminSerializer, BorrowingListRetrieveSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        serializer = super().get_serializer_class()
        if self.action == "list":
            if not self.request.user.is_staff:
                return BorrowingListSerializer
            serializer = BorrowingListAdminSerializer
        if self.action == "retrieve":
            serializer = BorrowingRetrieveSerializer
        if self.action == "return_borrowings":
            return BorrowingListRetrieveSerializer
        return serializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Borrowing.objects.all()
        return Borrowing.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action == 'list' or self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=["POST"],
        detail=True,
        url_path="return-borrowings",
        url_name="return-borrowings",
        permission_classes=[IsAuthenticated],
    )
    def return_borrowing(self, request: Request, pk: int = None):
        """Endpoint for returning borrowing"""
        borrowing = get_object_or_404(Borrowing, pk=pk)

        if borrowing.actual_return_date:
            return Response(
                {"detail": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if borrowing.user_id != self.request.user.id:
            return Response(
                {"detail": "This is not your borrowing."},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            borrowing.book.inventory += 1
            borrowing.book.save()

            if request.user.is_staff:
                borrowing.actual_return_date = request.data.get('actual_return_date', date.today())
            else:
                borrowing.actual_return_date = date.today()
            borrowing.save()

        return Response({"detail": "The book is returned."}, status=status.HTTP_200_OK)
