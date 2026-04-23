
from rest_framework.routers import DefaultRouter
from .views import ScanJobViewSet
from .views_auth import RegisterView

router = DefaultRouter()
router.register(r'scans', ScanJobViewSet, basename='scan')

urlpatterns = router.urls

# Registration endpoint
from django.urls import path
urlpatterns += [
	path('register/', RegisterView.as_view(), name='register'),
]
