from rest_framework.permissions import BasePermission
from .models import Property, HomeMember


def get_user_property_access(user, property_id):
    """
    Returns the access level a user has to a property.
    Returns None if no access.
    """
    # Admin and staff see everything
    if user.role in ['admin', 'staff']:
        return 'admin'

    # Owner has full access
    try:
        prop = Property.objects.get(id=property_id, owner=user)
        return 'owner'
    except Property.DoesNotExist:
        pass

    # Family member access
    try:
        membership = HomeMember.objects.get(property_id=property_id, user=user)
        return membership.role
    except HomeMember.DoesNotExist:
        return None


class IsPropertyOwnerOrMember(BasePermission):
    """Allows access if user owns or is a member of the property."""

    def has_object_permission(self, request, view, obj):
        property_id = obj.id if isinstance(obj, Property) else obj.property_id
        access = get_user_property_access(request.user, property_id)
        return access is not None


class IsPropertyOwnerOrAdmin(BasePermission):
    """Only owner or admin can modify — members can only view."""

    def has_object_permission(self, request, view, obj):
        from rest_framework.permissions import SAFE_METHODS
        property_id = obj.id if isinstance(obj, Property) else obj.property_id
        access = get_user_property_access(request.user, property_id)

        if request.method in SAFE_METHODS:
            return access is not None         # any member can read
        return access in ['owner', 'admin']   # only owner/admin can write