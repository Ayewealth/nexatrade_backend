# authentication/serializers.py
from rest_framework import serializers
from .models import User, KYCDocument
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'full_name',
                  'phone_number', 'date_of_birth', 'address', 'kyc_status', 'profile_pic', 'is_staff')
        read_only_fields = ('id', 'kyc_status')


# serializers.py

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password')

    def validate(self, attrs):
        password = attrs['password']
        if len(password) < 8:
            raise serializers.ValidationError(
                {"password": "Password must be at least 8 characters long"})
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError(
                {"password": "Password must contain at least one number"})
        if not any(char.isalpha() for char in password):
            raise serializers.ValidationError(
                {"password": "Password must contain at least one letter"})
        return attrs

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'full_name',
                  'phone_number', 'date_of_birth', 'address', 'kyc_status', 'profile_pic', 'is_staff')
        read_only_fields = ('id', 'kyc_status')


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC documents"""
    status = serializers.CharField(source='user.kyc_status', read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = KYCDocument
        fields = ('id', 'user', 'document_type',
                  'document', 'uploaded_at', 'status')
        read_only_fields = ('id', 'user', 'uploaded_at', 'status')


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                "New password must be different from the old password.")
        return attrs


class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'is_staff', 'is_superuser']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
