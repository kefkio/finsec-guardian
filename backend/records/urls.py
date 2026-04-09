from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TamperProofRecordViewSet

router = DefaultRouter()
router.register(r'records', TamperProofRecordViewSet, basename='record')

urlpatterns = [
    path('', include(router.urls)),
]
