from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q 
from .models import Property, HomeMember, SmartMeter, EnergyReading, MeterAlert
from .serializers import (PropertySerializer, HomeMemberSerializer,
                           SmartMeterSerializer, EnergyReadingSerializer,
                           MeterAlertSerializer)
from .permissions import IsPropertyOwnerOrMember, IsPropertyOwnerOrAdmin

User = get_user_model()


class PropertyListCreateView(generics.ListCreateAPIView):
    """GET all properties accessible to user / POST create new property."""
    serializer_class   = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return Property.objects.all()

        # Properties user owns OR is a member of
        owned      = Property.objects.filter(owner=user)
        memberships = Property.objects.filter(members__user=user)
        return (owned | memberships).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET / PUT / DELETE a specific property."""
    serializer_class   = PropertySerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyOwnerOrAdmin]

    def get_queryset(self):
        return Property.objects.all()


class HomeMemberView(APIView):
    """Manage family members for a property."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, property_id):
        """List all members of this property."""
        members = HomeMember.objects.filter(property_id=property_id)
        serializer = HomeMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, property_id):
        """Invite a user to a property by email."""
        email = request.data.get('invite_email')
        role  = request.data.get('role', 'member')

        try:
            prop    = Property.objects.get(id=property_id, owner=request.user)
            invitee = User.objects.get(email=email)
        except Property.DoesNotExist:
            return Response({'error': 'Property not found or you are not the owner.'},
                            status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({'error': 'No user with that email exists.'},
                            status=status.HTTP_404_NOT_FOUND)

        member, created = HomeMember.objects.get_or_create(
            property=prop, user=invitee,
            defaults={'role': role, 'invited_by': request.user}
        )

        if not created:
            return Response({'error': 'User already has access to this property.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = HomeMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, property_id):
        """Remove a member from a property."""
        user_id = request.data.get('user_id')
        try:
            prop   = Property.objects.get(id=property_id, owner=request.user)
            member = HomeMember.objects.get(property=prop, user_id=user_id)
            member.delete()
            return Response({'message': 'Member removed.'})
        except (Property.DoesNotExist, HomeMember.DoesNotExist):
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class SmartMeterListCreateView(generics.ListCreateAPIView):
    """List meters for a property / register a new meter."""
    serializer_class   = SmartMeterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return SmartMeter.objects.all()

        accessible_properties = Property.objects.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
        return SmartMeter.objects.filter(property__in=accessible_properties)

    def get_serializer_context(self):
        return {'request': self.request}


class SmartMeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View, edit, or deactivate a specific meter."""
    serializer_class   = SmartMeterSerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyOwnerOrAdmin]

    def get_queryset(self):
        return SmartMeter.objects.all()


class OnboardingStatusView(APIView):
    """
    GET /api/properties/onboarding/
    Tells React what step the user is on so it can redirect correctly.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Fetch the property directly — we need it for step 2 response
        property_qs = Property.objects.filter(owner=user)
        user_property = property_qs.first()

        has_property = user_property is not None
        has_meter    = SmartMeter.objects.filter(
                         property__owner=user, is_active=True
                       ).exists()

        if not has_property:
            step = 1
        elif not has_meter:
            step = 2
        else:
            step = 3

        # Build property info only if it exists
        property_data = None
        if user_property:
            property_data = {
                'id':           user_property.id,
                'name':         user_property.name,
                'address':      user_property.address_line1,
                'city':         user_property.city,
                'tariff_plan':  user_property.tariff_plan,
            }

        return Response({
            'step':         step,
            'has_property': has_property,
            'has_meter':    has_meter,
            'property':     property_data,   # ← null on step 1, populated on step 2 and 3
            'message': {
                1: 'Please add your home or property to continue.',
                2: 'Please link your smart meter to continue.',
                3: 'Setup complete. Welcome to your dashboard.',
            }[step]
        })