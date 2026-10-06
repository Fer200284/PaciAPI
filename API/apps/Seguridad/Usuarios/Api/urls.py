from django.urls import include, path

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.Seguridad.Usuarios.models import User
from .views import UserViewSet


class MobileTokenSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.rol == User.Roles.ADMINISTRADOR:
            raise AuthenticationFailed(
                "El usuario Administrador no puede iniciar sesión desde la aplicación móvil."
            )

        return data


class MobileTokenView(TokenObtainPairView):
    serializer_class = MobileTokenSerializer


class WebTokenSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.rol != User.Roles.ADMINISTRADOR:
            raise AuthenticationFailed(
                "Solo los usuarios Administrador pueden iniciar sesión en la web."
            )

        return data


class WebTokenView(TokenObtainPairView):
    serializer_class = WebTokenSerializer


router = DefaultRouter()

router.register(
    r'usuarios',
    UserViewSet,
    basename='usuarios'
)


urlpatterns = [
    # Login exclusivo para la aplicación móvil
    path(
        'token/',
        MobileTokenView.as_view(),
        name='token_obtain_pair'
    ),

    # Login exclusivo para la web
    path(
        'web/token/',
        WebTokenView.as_view(),
        name='web_token_obtain_pair'
    ),

    # Renovación del token móvil
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    path(
        '',
        include(router.urls)
    ),
]