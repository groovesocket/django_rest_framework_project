from django.contrib.auth.models import User
from rest_framework import generics, permissions, renderers
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import Snippet, AuditLog
from .permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly
from .serializers import AuditLogSerializer, SnippetSerializer, UserSerializer
from .mixins import AuditRetrieveUpdateDestroyAPIView, AuditListCreateAPIView, AuditRetrieveDestroyAPIView


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "snippets": reverse("snippet-list", request=request, format=format),
        }
    )


class SnippetHighlight(generics.GenericAPIView):
    queryset = Snippet.objects.all()
    renderer_classes = (renderers.StaticHTMLRenderer,)

    def get(self, request, *args, **kwargs):
        snippet = self.get_object()
        return Response(snippet.highlighted)


class SnippetList(AuditListCreateAPIView):
    serializer_class = SnippetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Snippet.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SnippetDetail(AuditRetrieveUpdateDestroyAPIView):
    serializer_class = SnippetSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly,
    )

    def get_queryset(self):
        return Snippet.objects.all()


class UserList(AuditListCreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied

        return super().create(request, *args, **kwargs)

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


class UserDetail(AuditRetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self):
        return User.objects.all()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class AuditLogList(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_staff:
            raise PermissionDenied
        return AuditLog.objects.all()


# CREATE TOKEN: curl -u admin:admin1 -X POST http://localhost:8000/create_token/
# USING TOKEN: curl -v -H "Authorization: Token 3aa4fa4d06ece12bae2ae3941c85d0dbba1e7d73" -X DELETE http://localhost:8000/users/5/
class CreateToken(generics.CreateAPIView):
    permission_classes = (permissions.IsAdminUser, )
    
    def post(self, request, *args, **kwargs):
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({'token': token.key})
