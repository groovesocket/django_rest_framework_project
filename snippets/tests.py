from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock
from .views import UserList
from .models import Snippet
from .serializers import UserSerializer


class TestSnippetDetail(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.snippet = Snippet.objects.create(
            title='Test Snippet',
            code='print("Hello, world!")',
            owner=self.user
        )

    def test_get_snippet_detail_unauthenticated(self):
        response = self.client.get(f'/snippets/{self.snippet.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Snippet')

    def test_get_snippet_detail_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/snippets/{self.snippet.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Snippet')

    def test_update_snippet_unauthenticated(self):
        data = {'title': 'Updated Snippet'}
        response = self.client.put(f'/snippets/{self.snippet.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_snippet_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Updated Snippet'}
        response = self.client.put(f'/snippets/{self.snippet.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Snippet')

    def test_delete_snippet_unauthenticated(self):
        response = self.client.delete(f'/snippets/{self.snippet.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_snippet_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/snippets/{self.snippet.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Snippet.objects.filter(id=self.snippet.id).exists())

# TODO
class TestSnippetList(TestCase):
    def test_perform_create(self):
        self.fail()


class TestUserList(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.request_mock = MagicMock()
        # set up mock non staff user
        self.request_mock.user.is_staff = False
        self.view = UserList()
        User.objects.create(username='user1', password='1234')
        User.objects.create(username='user2', password='6789')
        self.users = User.objects.all()

    # The @patch decorator mocks the create method of the parent class to prevent actual database interaction.
    @patch('rest_framework.generics.ListCreateAPIView.create')
    def test_create_permission_denied(self, mock_super_create):
        # Check if PermissionDenied is raised when a non-staff user tries to create a user.
        with self.assertRaises(PermissionDenied):
            self.view.create(self.request_mock)
        # assert_not_called verifies that the parent's create wasn't called.
        mock_super_create.assert_not_called()

    @patch('rest_framework.generics.ListCreateAPIView.create')
    def test_create_staff_user(self, mock_super_create):
        # Check if the create call succeeds when the user is staff.
        self.request_mock.user.is_staff = True
        self.view.create(self.request_mock)
        # assert_called_once verifies that the parent's create was called once.
        mock_super_create.assert_called_once()

    @patch('django.contrib.auth.models.User.objects.all')
    def test_get_queryset(self, mock_all):
        # Mock the return value of User.objects.all()
        mock_all.return_value = self.users

        request = self.factory.get('/users/')
        callable_view = UserList.as_view()
        response = callable_view(request)

        # Check if the response contains the expected data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['username'], 'user1')
        self.assertEqual(response.data['results'][1]['username'], 'user2')

    @patch('rest_framework.generics.ListCreateAPIView.filter_queryset')
    def test_filter_queryset_non_staff(self, mock_super_filter_queryset):
        # Check if non-staff users don't trigger additional filtering.
        request = self.factory.get('/users/')
        request.user = MagicMock(is_staff=False)
        queryset = User.objects.none()  # Mock initial queryset
        self.view.setup(request=request)

        self.view.filter_queryset(queryset)

        mock_super_filter_queryset.assert_called_once_with(queryset)

    @patch('rest_framework.generics.ListCreateAPIView.filter_queryset')
    def test_filter_queryset_staff_no_param(self, mock_super_filter_queryset):
        # Checks if staff users without the include_deactivated parameter don't trigger additional filtering.
        request = Request(self.factory.get('/users/'))
        request.user = MagicMock(is_staff=True)
        self.view.setup(request=request)
        queryset = User.objects.none()

        self.view.filter_queryset(queryset)

        mock_super_filter_queryset.assert_called_once_with(queryset)

    @patch('rest_framework.generics.ListCreateAPIView.filter_queryset')
    def test_filter_queryset_staff_include_deactivated(self, mock_super_filter_queryset):
        # Checks the behavior when a staff user provides include_deactivated=1.
        request = Request(self.factory.get('/users/?include_deactivated=1'))
        request.user = MagicMock(is_staff=True)
        self.view.setup(request=request)
        queryset = User.objects.none()

        self.view.filter_queryset(queryset)

        mock_super_filter_queryset.assert_called_once_with(queryset)

    @patch('rest_framework.generics.ListCreateAPIView.filter_queryset')
    def test_filter_queryset_staff_exclude_deactivated(self, mock_super_filter_queryset):
        # Checks the behavior when a staff user provides include_deactivated=0 (or any value other than "1").
        request = Request(self.factory.get('/users/?include_deactivated=0'))
        request.user = MagicMock(is_staff=True)
        self.view.setup(request=request)
        queryset = User.objects.none()

        self.view.filter_queryset(queryset)

        mock_super_filter_queryset.assert_called_once_with(queryset)

# TODO
class TestUserDetail(TestCase):
    def test_get_queryset(self):
        self.fail()

    def test_destroy(self):
        self.fail()

    def test_perform_destroy(self):
        self.fail()
