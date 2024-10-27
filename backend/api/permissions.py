from rest_framework.permissions import BasePermission

class IsAuthor(BasePermission):
    message = 'Только автор может изменять или удалять этот рецепт.'

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
