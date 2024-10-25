from rest_framework import routers

from django.urls import path, include

from borrowing.views import BorrowingViewSet

router = routers.DefaultRouter()
router.register("", BorrowingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

app_name = "borrowing"
