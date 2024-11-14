from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from user.serializers import UserSerializer

User = get_user_model()


class UserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'user_1@test.com',
            'password': 'test_1',
        }
        self.superuser_data = {
            'email': 'superuser@test.com',
            'password': 'admin',
        }
        self.update_user_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        user = User.objects.create_superuser(**self.superuser_data)
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, self.superuser_data['email'])
        self.assertTrue(user.check_password(self.superuser_data['password']))
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_serialize_user(self):
        user = User.objects.create_user(**self.user_data)
        serializer = UserSerializer(user)
        expected_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": self.user_data["email"],
            "is_staff": False,
        }
        self.assertEqual(serializer.data, expected_data)
        self.assertTrue(user.check_password(self.user_data["password"]))

    def test_deserialize_user(self):
        serializer = UserSerializer(data=self.user_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password"]))

    def test_register_existing_user(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(reverse("user:create"), self.user_data)
        self.assertEqual(response.status_code, 400)

    def test_update_user(self):
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        response = self.client.patch(reverse("user:manage"), self.update_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, self.update_user_data['first_name'])
        self.assertEqual(user.last_name, self.update_user_data['last_name'])


class TokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass"
        )

    def test_obtain_token(self):
        data = {
            "email": "test@test.com",
            "password": "testpass",
        }
        response = self.client.post(reverse("user:token_obtain_pair"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token(self):
        data = {
            "email": "test@test.com",
            "password": "testpass",
        }
        response = self.client.post(reverse("user:token_obtain_pair"), data)
        refresh_token = response.data["refresh"]
        response = self.client.post(
            reverse("user:token_refresh"),
            {"refresh": refresh_token}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
