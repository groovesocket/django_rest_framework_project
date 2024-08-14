from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from .views import UserList
from .models import Snippet, AuditLog
from .serializers import AuditLogSerializer, SnippetSerializer, UserSerializer


class TestSnippetList(TestCase):
    # These test use token auth just for giggles to test token login
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        Snippet.objects.create(code='foo', owner=self.user)
        Snippet.objects.create(code='bar', owner=self.user)

    def test_get_snippet_list_authenticated(self):
        response = self.client.get(reverse('snippet-list'))
        request = APIRequestFactory().get('/snippets/')
        snippets = Snippet.objects.all()
        serializer = SnippetSerializer(snippets, many=True, context={'request': request})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_get_snippet_list_unauthenticated(self):
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse('snippet-list'))
        request = APIRequestFactory().get('/snippets/')
        snippets = Snippet.objects.all()
        serializer = SnippetSerializer(snippets, many=True, context={'request': request})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)  # Unauthenticated users can still read

    def test_create_snippet_authenticated(self):
        data = {'code': 'baz'}
        response = self.client.post(reverse('snippet-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Snippet.objects.count(), 3)
        self.assertEqual(Snippet.objects.last().code, 'baz')
        self.assertEqual(Snippet.objects.last().owner, self.user)

    def test_create_snippet_unauthenticated(self):
        self.client.credentials()  # Remove authentication
        data = {'code': 'qux'}
        response = self.client.post(reverse('snippet-list'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Unauthenticated users cannot create


class TestSnippetDetail(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.snippet_code = 'print("Hello, world!")'
        self.snippet = Snippet.objects.create(
            title='Test Snippet',
            code=self.snippet_code,
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_snippet_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Updated Snippet', 'code': self.snippet_code}
        response = self.client.put(f'/snippets/{self.snippet.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Snippet')

    def test_delete_snippet_unauthenticated(self):
        response = self.client.delete(f'/snippets/{self.snippet.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_snippet_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/snippets/{self.snippet.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Snippet.objects.filter(id=self.snippet.id).exists())


class TestUserList(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.view = UserList()
        self.staff_user = User.objects.create_user(username='staffuser', password='staffpassword', is_staff=True)
        self.regular_user = User.objects.create_user(username='regularuser', password='regularpassword', is_staff=False)

    def test_create_user_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        data = {'username': 'newuser', 'password': 'newpassword'}
        response = self.client.post(reverse('user-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(User.objects.get(username='newuser').username, 'newuser')

    def test_create_user_non_staff(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {'username': 'anotheruser', 'password': 'anotherpassword'}
        self.client.post(reverse('user-list'), data)
        self.assertRaises(PermissionDenied)


    def test_get_user_list_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        request = self.factory.get('/users/')
        response = self.client.get(reverse('user-list'))
        users = User.objects.all()
        serializer = UserSerializer(users, many=True, context={'request': request})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_get_user_list_non_staff(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_queryset_staff_no_include_deactivated_param(self):
        # Create a request without include_deactivated parameter
        request = Request(self.factory.get('/users/'))
        request.user = self.staff_user

        # Create a view instance
        self.view.setup(request=request)

        # Create some test users
        User.objects.create(username="active_user", is_active=True)
        User.objects.create(username="inactive_user", is_active=False)

        queryset = self.view.filter_queryset(User.objects.all())
        # get only the active users
        active_users_queryset = User.objects.filter(is_active=True)
        self.assertEqual(queryset.count(), len(active_users_queryset))
        self.assertTrue(queryset.first().is_active)

    def test_filter_queryset_staff_no_include_deactivated(self):
        # Create a request with url attribute include_deactivated=0 (or any value other than "1").
        request = Request(self.factory.get('/users/?include_deactivated=0'))
        request.user = self.staff_user

        # Create a view instance
        self.view.setup(request=request)

        # Create some test users
        User.objects.create(username="active_user", is_active=True)
        User.objects.create(username="inactive_user", is_active=False)

        queryset = self.view.filter_queryset(User.objects.all())
        # get only the active users
        active_users_queryset = User.objects.filter(is_active=True)
        self.assertEqual(queryset.count(), len(active_users_queryset))
        self.assertTrue(queryset.first().is_active)

    def test_filter_queryset_staff_include_deactivated(self):
        # Create a request with url attribute include_deactivated=1
        request = Request(self.factory.get('/users/?include_deactivated=1'))
        request.user = self.staff_user

        # Create a view instance
        self.view.setup(request=request)

        # Create some test users
        User.objects.create(username="active_user", is_active=True)
        User.objects.create(username="inactive_user", is_active=False)

        queryset = self.view.filter_queryset(User.objects.all())
        # get only the active users
        all_users_queryset = User.objects.all()
        self.assertEqual(queryset.count(), len(all_users_queryset.all()))
        self.assertTrue(queryset.first().is_active)


class TestUserDetail(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(username='staffuser', password='staffpassword', is_staff=True)
        self.regular_user = User.objects.create_user(username='regularuser', password='regularpassword', is_staff=False)
        self.user_to_delete = User.objects.create_user(username='deleteuser', password='deletepassword')

    def test_get_user_detail_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/users/{self.staff_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'staffuser')

    def test_get_user_detail_non_staff(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/users/{self.staff_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'staffuser')

    def test_delete_user_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('user-detail', kwargs={'pk': self.user_to_delete.pk})  # Replace 'user-detail' with your actual URL name
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        deleted_user = User.objects.get(pk=self.user_to_delete.pk)
        self.assertFalse(deleted_user.is_active)  # Check if user is deactivated

    def test_delete_user_non_staff(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('user-detail', kwargs={'pk': self.user_to_delete.pk})  # Replace 'user-detail' with your actual URL name
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Non-staff cannot delete


class TestAuditLog(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(username='staffuser', password='staffpassword', is_staff=True)
        self.regular_user = User.objects.create_user(username='regularuser', password='regularpassword', is_staff=False)
        AuditLog.objects.create(user=self.staff_user, action='test create', model_id=1, model_name="test audit log 1")
        AuditLog.objects.create(user=self.regular_user, action='test destroy', model_id=2, model_name="test audit log 2")

    def test_get_audit_log_list_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(reverse('audit-log'))  # Replace 'auditlog-list' with your actual URL name
        audit_logs = AuditLog.objects.all()
        serializer = AuditLogSerializer(audit_logs, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_get_audit_log_list_non_staff(self):
        self.client.force_authenticate(user=self.regular_user)
        self.client.get(reverse('audit-log'))
        self.assertRaises(PermissionDenied)