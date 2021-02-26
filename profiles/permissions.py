from rest_framework import permissions


class UserAccessPermission(permissions.BasePermission):
    message = "User is not allowed to update"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            print('Unknown')
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # print(request.user)
        # print(obj)
        return obj == request.user
