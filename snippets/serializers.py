from django.contrib.auth.models import User
from rest_framework import serializers
from snippets.models import AuditLog, Snippet


class SnippetSerializer(serializers.HyperlinkedModelSerializer): 
    owner = serializers.ReadOnlyField(source="owner.username")
    highlight = serializers.HyperlinkedIdentityField(  
        view_name="snippet-highlight", format="html"
    )

    class Meta:
        model = Snippet
        fields = (
            "url",
            "id",
            "highlight",
            "title",
            "code",
            "linenos",
            "language",
            "style",
            "owner",
        )  


class UserSerializer(serializers.HyperlinkedModelSerializer):
    snippets = serializers.HyperlinkedRelatedField(  
        many=True, view_name="snippet-detail", read_only=True
    )

    class Meta:
        model = User
        fields = (
            "url",
            "id",
            "is_active",
            "username",
            "email",
            "password",
            "snippets"
        )
        extra_kwargs = {
            "is_active": {"read_only": True},
            "password": {"write_only": True}
        }


class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog
        fields = (
            "action",
            "model_name",
            "model_id",
            "timestamp"
        )