from django.contrib import admin
from .models import Snippet, AuditLog


class SnippetAdmin(admin.ModelAdmin):
    readonly_fields = ("highlighted",)

class AuditLogAdmin(admin.ModelAdmin):
    readonly_fields = ("model_id", "model_name", "timestamp", "action", "user")

admin.site.register(Snippet, SnippetAdmin)

admin.site.register(AuditLog, AuditLogAdmin)
