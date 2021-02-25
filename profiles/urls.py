from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import SimpleRouter, Route, DynamicRoute, DefaultRouter

from .views import UserViewSet, AddressViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="Profile API",
        default_version="v1",
        description="Getting image absolute URL",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@test.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


class CustomUserRouter(SimpleRouter):
    routes = [
        Route(
            url=r'^{prefix}/{lookup}$',
            mapping={'patch': 'update'},
            name='{basename}-update',
            detail=True,
            initkwargs={'suffix': 'Update'}
        ),
        DynamicRoute(
            url=r'^{prefix}/{url_path}{trailing_slash}$',
            name='{basename}-{url_name}',
            detail=False,
            initkwargs={}
        ),
    ]


router = CustomUserRouter()
router.register('users', UserViewSet, basename='users')

r = DefaultRouter()
r.register('address', AddressViewSet, basename='address')

urlpatterns = [
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('', include((router.urls, 'customusers'), namespace='users')),
]

urlpatterns += router.urls
urlpatterns += r.urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
