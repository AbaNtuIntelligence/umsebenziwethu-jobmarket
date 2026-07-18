from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import User

class IsEmployer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.EMPLOYER

class IsJobSeeker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.JOB_SEEKER

class IsJobOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.employer_id == request.user.id

