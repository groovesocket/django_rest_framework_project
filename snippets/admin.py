from django.contrib import admin
from .models import Snippet, AuditLog


class AuditLogAdmin(admin.ModelAdmin):
    readonly_fields = ("model_id", "model_name", "timestamp", "action", "user")
    # prevent adding or deleting audit logs
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class SnippetAdmin(admin.ModelAdmin):
    readonly_fields = ("highlighted",)


admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Snippet, SnippetAdmin)
