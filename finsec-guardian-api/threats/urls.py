from rest_framework.routers import DefaultRouter
from .views import ThreatRecordViewSet

router = DefaultRouter()
router.register(r'threats', ThreatRecordViewSet, basename='threat')

urlpatterns = router.urls
