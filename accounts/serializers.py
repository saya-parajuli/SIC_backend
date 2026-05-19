from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


User = get_user_model()   # always use this, never import CustomUser directly

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2', 'organization', 'phone']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name',
                  'role', 'organization', 'phone', 'date_joined']
        read_only_fields = ['email', 'role', 'date_joined']


class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid email or password"
            )

        refresh = self.get_token(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
            },
        }
    



class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # We intentionally don't raise an error if email doesn't exist
        # — this prevents user enumeration attacks (attacker can't tell
        #   which emails are registered)
        return value


class ResetPasswordSerializer(serializers.Serializer):
    uid   = serializers.CharField()      # base64-encoded user pk
    token = serializers.CharField()      # signed token from email link
    new_password  = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Decode uid → get user
        try:
            uid  = force_str(urlsafe_base64_decode(data["uid"]))
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid reset link."})

        # Validate token
        if not PasswordResetTokenGenerator().check_token(user, data["token"]):
            raise serializers.ValidationError({"token": "Reset link is invalid or has expired."})

        data["user"] = user
        return data