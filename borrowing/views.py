from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from borrowing.models import Borrowing
from borrowing.serializers import BorrowingSerializer, BorrowingRetrieveSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BorrowingRetrieveSerializer
        return BorrowingSerializer

    def get_queryset(self):
        return Borrowing.objects.filter(user=self.request.user)
