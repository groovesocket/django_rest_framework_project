from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

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
    list_display = ("id", "title", "owner", "language", "code")
    list_display_links = ("title", )
    readonly_fields = ("highlighted",)

# Show all User fields in the list view
UserAdmin.list_display = ("id", "username", "email", "first_name", "last_name", "is_active", "date_joined", "is_staff", "is_superuser")
UserAdmin.list_display_links = ("username", )


admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Snippet, SnippetAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
