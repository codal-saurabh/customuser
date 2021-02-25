import smtplib

from django.conf import settings
from django.contrib.auth.models import update_last_login
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from .models import CustomUser
from .permissions import UserAccessPermission
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, PasswordSerializer, \
    ResetPasswordSerializer
from .tokens import default_token_generator


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserAccessPermission]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser]
    http_method_names = ['get', 'patch', 'post']

    lookup_field = 'pk'
    lookup_value_regex = '[0-9]+'

    def get_serializer_class(self):
        # print(self.action)
        if self.action == 'register':
            return RegisterSerializer
        if self.action == 'login':
            return LoginSerializer
        if self.action == 'forget_password':
            return PasswordSerializer
        if self.action == 'reset_password':
            return ResetPasswordSerializer
        return UserSerializer

    def get_authenticators(self):
        # print(self.action)
        if self.request.method == "POST":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        # print(self.action)
        # if self.action == 'register':
        #     return []
        if self.action == 'login':
            return []
        elif self.action == 'forget_password':
            return []
        elif self.action == 'reset_password':
            return []
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        elif self.action == 'forget_password':
            return super().get_queryset()
        else:
            return super().get_queryset().filter(email=self.request.user)

    @action(detail=False, methods=['post'], url_path='register', url_name='register', permission_classes=[])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.get_success_headers(serializer.data)
        return Response({'result': 'User created', 'user_data': serializer.data},
                        status=status.HTTP_201_CREATED, )

    @action(detail=False, methods=['post'], url_path='login', url_name='login', permission_classes=[])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user:
            update_last_login(None, user)
            t, _ = Token.objects.get_or_create(user=user)
            return Response({'result': str(user), "token": t.key}, status=status.HTTP_202_ACCEPTED, )
        return Response({'result': 'Wrong credentials'})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        response = super(UserViewSet, self).update(request, *args, **kwargs)
        print(response.data['profile_image'])
        return Response({'Update': instance.email, 'Profile Image': response.data['profile_image']},
                        status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def me(self, request):
        content = {
            "user": str(request.user),
            "token": str(request.auth)
        }
        user = self.get_serializer(self.get_queryset(), many=True)
        return Response({"Message": "Hello Good Morning", "content": content, "user": user.data},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='logout', url_name='logout')
    def logout(self, request):
        user = self.request.user
        # print(user)
        try:
            user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            return Response({'result': 'error in logout, try again'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'result': 'successfully logged out'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='forget-password', url_name='forget-password')
    def forget_password(self, request):
        print(request.data['email'])
        email = request.data['email']
        try:
            qs = self.get_queryset().filter(email=email)
            match = self.get_queryset().get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'result': 'Email not registered'}, status=status.HTTP_404_NOT_FOUND)
        if len(qs) > 0:
            user = qs[0]
        print(user.has_requested_password_reset)
        user.has_requested_password_reset = True
        user.save()
        print(user.has_requested_password_reset)
        token = default_token_generator.make_token(user)
        print(token)
        site = get_current_site(request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        print(uid)
        url = UserViewSet.reverse_action(self, UserViewSet.reset_password.url_name, args=[uid, token])
        print(url)
        # link = "{}".format(reverse('users:users-reset-password', args=[uid, token]))
        message = render_to_string('password_reset_request.html', {
            'user': user,
            'domain': site.domain,
            'link': url,
        })
        subject = "Reset Password"
        # message = "Click on the below link to reset your password"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        print(recipient_list)
        try:
            send_mail(subject=subject, message='', from_email=email_from, recipient_list=recipient_list,
                      html_message=message)
        except smtplib.SMTPException:
            return Response({'result': 'Error sending mail'})
        return Response({'result': 'Mail sent successfully'})

    @action(detail=False, methods=['get', 'post'], url_path='reset-password/(?P<uid>[\w-]+)/(?P<token>[\w-]+)',
            url_name='reset-password', renderer_classes=[TemplateHTMLRenderer], authentication_classes=[],
            permission_classes=[], parser_classes=[FormParser])
    def reset_password(self, request, uid, token, *args, **kwargs):
        print(self.request.method)
        if self.request.method == 'POST':
            print(self.request.data)
            # print(self.kwargs)
            data = self.request.data
            u_id = force_text(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=u_id)
            token_result = default_token_generator.check_token(user, token)
            print(token_result)
            if user is not None and token_result:
                print('here')
                return self.change_password(user, data)
            return Response({'errors': ['invalid token'], 'reset_password': self.get_serializer()},
                            template_name='reset_password.html')
        else:
            # print(self.kwargs)
            u_id = force_text(urlsafe_base64_decode(self.kwargs['uid']))
            user = CustomUser.objects.get(pk=u_id)
            token_result = default_token_generator.check_token(user, self.kwargs['token'])
            print(token_result)
            print(user.has_requested_password_reset)
            if token_result and user.has_requested_password_reset:
                return Response({'view': UserViewSet, 'reset_password': self.get_serializer()},
                                template_name='reset_password.html')
            return Response(template_name='error_password.html')

    def change_password(self, user, data):
        s = self.get_serializer(user, data=data)
        print('here2')
        # print(s)
        if s.is_valid(raise_exception=False):
            print('here3')
            s.save()
            print(s.data)
            return Response(
                {'message': 'Password Updated', 'reset_password': self.get_serializer()},
                template_name='reset_password.html')
        else:
            errors = s.errors
            error_msg_list = []
            if len(errors) > 0:
                print(errors)
            if 'password' in errors:
                error_msg = "Password: "
                error_msg += errors.get('password')[0]
                error_msg_list.append(error_msg)
                print(error_msg)
            if 'confirm_password' in errors:
                error_msg = "\nConfirm Password: "
                error_msg += errors.get('confirm_password')[0]
                error_msg_list.append(error_msg)
                print(error_msg)
            if 'errors' in errors:
                for e in errors.get('errors'):
                    print(e)
                    error_msg_list.append(e)
            return Response({'errors': error_msg_list, 'reset_password': self.get_serializer()},
                            template_name='reset_password.html')
