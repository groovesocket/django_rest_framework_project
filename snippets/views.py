from django.contrib.auth.models import User
from rest_framework import generics, permissions, renderers
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import Snippet, AuditLog
from .permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly
from .serializers import AuditLogSerializer, SnippetSerializer, UserSerializer

ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "snippets": reverse("snippet-list", request=request, format=format),
        }
    )


def save_audit_log(request, action, model_name, model_id):
    AuditLog.objects.create(user=request.user,
                            action=action,
                            model_name=model_name,
                            model_id=model_id)


class SnippetHighlight(generics.GenericAPIView):
    queryset = Snippet.objects.select_related("owner").all()
    renderer_classes = (renderers.StaticHTMLRenderer,)

    def get(self, request, *args, **kwargs):
        snippet = self.get_object()
        return Response(snippet.highlighted)


class SnippetList(generics.ListCreateAPIView, CreateModelMixin):
    serializer_class = SnippetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Snippet.objects.select_related("owner").all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        save_audit_log(request=request,
                       action=ACTION_CREATE,
                       model_name=response.data.serializer.Meta.model.__name__,
                       model_id=response.data["id"])
        return response


class SnippetDetail(generics.RetrieveUpdateDestroyAPIView, DestroyModelMixin):
    serializer_class = SnippetSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly,
    )

    def get_queryset(self):
        return Snippet.objects.select_related("owner").all()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        save_audit_log(request=request,
                       action=ACTION_UPDATE,
                       model_name=response.data.serializer.Meta.model.__name__,
                       model_id=response.data["id"])
        return response

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        save_audit_log(request=self.request,
                       action=ACTION_DELETE,
                       model_name=instance.__class__.__name__,
                       model_id=instance.id)
        instance.delete()


class UserList(generics.ListCreateAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # Don't include deactivated unless staff, and also specified flag "?include_deactivated=1"
        include_deactivated = False
        if self.request.user.is_staff:
            include_deactivated = bool(self.request.query_params.get("include_deactivated", "") == "1")

        # Filter deactivated, unless flag set
        if not include_deactivated:
            queryset = queryset.filter(is_active=True)

        return queryset

    def create(self, request, *args, **kwargs):
        # Only staff users can create new users
        if not request.user.is_staff:
            raise PermissionDenied

        response = super().create(request, *args, **kwargs)
        save_audit_log(request=request,
                       action=ACTION_CREATE,
                       model_name=response.data.serializer.Meta.model.__name__,
                       model_id=response.data["id"])
        return response


class UserDetail(generics.RetrieveDestroyAPIView, DestroyModelMixin):
    serializer_class = UserSerializer
    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self):
        return User.objects.all()

    def perform_destroy(self, instance):
        save_audit_log(request=self.request,
                       action=ACTION_DELETE,
                       model_name=instance.__class__.__name__,
                       model_id=instance.id)
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class AuditLogList(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_staff:
            raise PermissionDenied
        return AuditLog.objects.select_related("user").all()


# CREATE TOKEN: curl -u admin:admin1 -X POST http://localhost:8000/create_token/
# USING TOKEN: curl -v -H "Authorization: Token 3aa4fa4d06ece12bae2ae3941c85d0dbba1e7d73" -X DELETE http://localhost:8000/users/5/
class CreateToken(generics.CreateAPIView):
    permission_classes = (permissions.IsAdminUser, )
    
    def post(self, request, *args, **kwargs):
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({'token': token.key})
