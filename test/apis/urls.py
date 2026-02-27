from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import API

urlpatterns = [
    path('api/', csrf_exempt(API.as_view()), name='api-call')
]
