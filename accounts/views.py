from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserProfileSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .models import PasswordResetRequest
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset           = User.objects.all()
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()   # ← invalidates the token permanently

            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_205_RESET_CONTENT
            )

        except TokenError:
            return Response(
                {'error': 'Token is invalid or already expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        




class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            # Invalidate any previous unused requests for this user
            PasswordResetRequest.objects.filter(user=user, is_used=False).delete()

            # Create fresh token + OTP
            reset_request = PasswordResetRequest.objects.create(user=user)

            reset_link = (
                f"{settings.FRONTEND_URL}/reset-password/{reset_request.reset_token}"
            )

            send_mail(
                subject="Reset your password — Smart EM",
                message=(
                    f"Hi {user.first_name or user.email},\n\n"
                    f"We received a request to reset your password.\n\n"
                    f"1. Click this link to open the reset page:\n"
                    f"   {reset_link}\n\n"
                    f"2. Enter this OTP when prompted:\n"
                    f"   {reset_request.otp}\n\n"
                    f"This OTP expires in 15 minutes.\n"
                    f"If you didn't request this, you can safely ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

        except User.DoesNotExist:
            pass  # Same response either way — prevents email enumeration

        return Response(
            {"message": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_request = serializer.validated_data["reset_request"]
        user = reset_request.user

        # Update password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # Mark token as used — can never be replayed
        reset_request.is_used = True
        reset_request.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )