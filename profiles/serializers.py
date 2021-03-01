import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate
from django.core import exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import CustomUser, Addresses


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


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        ordering = ['-id']
        model = Addresses
        fields = '__all__'
        # extra_kwargs = {'user_address': {'required': False}}

    def create(self, validated_data):
        instance, created = Addresses.objects.get_or_create(**validated_data)
        # print(instance.id)
        return instance


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'profile_image', 'date_joined', 'addresses', ]
        # 'address_line1', 'address_line2', 'city', 'state', 'country', 'zipcode']
        extra_kwargs = {'addresses': {'required': False}, 'profile_image': {'required': False}}

    def update(self, instance, validated_data):
        address_data = list(self.context.get('address'))
        address_serializer = AddressSerializer(many=True, data=address_data)
        address_serializer.is_valid(raise_exception=True)
        address_obj = address_serializer.save()
        user_address_update_id = list(x.id for x in address_obj)
        # print(x)
        remove = []
        address_original_list = {}
        user_address_data_id = list(instance.addresses.values_list("id", flat=True))
        print(address_original_list)
        print(user_address_data_id)
        for y in user_address_data_id:
            if y not in user_address_update_id:
                remove.append(y)
        print(remove)
        for z in Addresses.objects.values_list("id", flat=True):
            # print(z)
            count = Addresses.objects.get(id=z).addresses.count()
            # print(count)
            address_original_list[z] = count
            if z in remove and count > 1:
                remove.remove(z)
        print(remove)
        instance.addresses.set(user_address_update_id)
        instance.save()
        for i in remove:
            try:
                match = Addresses.objects.get(id=i)
                print(type(match))
            except (AttributeError, ObjectDoesNotExist):
                return print('no address at id {}'.format(i))
            match.delete()
        return instance


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
