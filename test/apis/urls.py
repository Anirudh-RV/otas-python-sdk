from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import API

urlpatterns = [
    path('api/v1/', csrf_exempt(API.as_view()), name='api-call-v1'),
    path('api/v2/', csrf_exempt(API.as_view()), name='api-call-v2')
]
