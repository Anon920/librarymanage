from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny

from books.models import Book
from books.permissions import IsAdminOrIfAuthenticatedReadOnly
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    authentication_classes = (TokenAuthentication,)

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminOrIfAuthenticatedReadOnly]
        return [permission() for permission in permission_classes]

