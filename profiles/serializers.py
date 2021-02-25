import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate
from django.core import exceptions
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'password', 're_password']

    def validate(self, attrs):
        # print(attrs)
        if attrs['password'] != attrs['re_password']:
            raise serializers.ValidationError("Password not same")

        errors = dict()
        try:
            validators.validate_password(password=attrs['password'], user=CustomUser)
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        user = CustomUser(
            email=validated_data['email'],
            name=validated_data['name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        print(user)
        return user


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        label=_("Email"),
        write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        write_only=True)
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'token']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = None
        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'profile_image', 'date_joined']


class PasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email']


class ResetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=100,
        allow_blank=False,
        style={'input_type': 'password', 'placeholder': 'Password', 'autofocus': True}
    )
    confirm_password = serializers.CharField(
        max_length=100,
        allow_blank=False,
        style={'placeholder': 'Confirm Password'},
        write_only=True,
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'password', 'confirm_password']

    def validate(self, attrs):
        errors = dict()
        if attrs['password'] != attrs['confirm_password']:
            errors['errors'] = "Password not same"
            raise serializers.ValidationError(errors)
        try:
            validators.validate_password(password=attrs['password'], user=CustomUser)
        except exceptions.ValidationError as e:
            errors['errors'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def update(self, instance, validated_data):
        print(validated_data)
        print(instance)
        instance.has_requested_password_reset = False
        instance.set_password(validated_data['password'])
        instance.save()
        return instance
