from rest_framework import generics
from .models import AuditLog
from unittest.mock import MagicMock


def save_log(request, action, response):
    # don't create audit log if test
    if not isinstance(response, MagicMock):
        AuditLog.objects.create(user=request.user,
                                action=action,
                                model_name=response.data.serializer.Meta.model.__name__,
                                model_id=response.data["id"])


def save_log_destroy(request, instance):
    # don't create audit log if test
    if not isinstance(request, MagicMock):
        AuditLog.objects.create(user=request.user,
                                action="destroy",
                                model_name=instance.__class__.__name__,
                                model_id=instance.id)


class AuditListCreateAPIView(generics.ListCreateAPIView):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        save_log(request, "create", response)
        return response


class AuditRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        save_log(request, "update", response)
        return response

    def perform_destroy(self, instance):
        save_log_destroy(self.request, instance)


class AuditRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
    def perform_destroy(self, instance):
        save_log_destroy(self.request, instance)