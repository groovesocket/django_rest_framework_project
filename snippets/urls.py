from django.urls import path
from rest_framework.authtoken import views as auth_views
from rest_framework.urlpatterns import format_suffix_patterns
from snippets import views

urlpatterns = [
    path("", views.api_root),

    path("snippets/", views.SnippetList.as_view(), name="snippet-list"),
    path("snippets/<int:pk>/", views.SnippetDetail.as_view(), name="snippet-detail"),
    path("snippets/<int:pk>/highlight/", views.SnippetHighlight.as_view(), name="snippet-highlight"),

    path("users/", views.UserList.as_view(), name="user-list"),
    path("users/<int:pk>/", views.UserDetail.as_view(), name="user-detail"),

    path("audit_log/", views.AuditLogList.as_view(), name="audit-log"),

    # CREATE TOKEN: curl -X POST http://localhost:8000/api_token_auth/ -d 'username=[username]&password=[password]'
    # USING TOKEN: curl -v -H "Authorization: Token 3aa4fa4d06ece12bae2ae3941c85d0dbba1e7d73" -X DELETE http://localhost:8000/users/5/
    path("api_token_auth/", auth_views.obtain_auth_token, name="api-token-auth"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
