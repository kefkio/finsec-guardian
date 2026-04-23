from rest_framework.routers import DefaultRouter
from .views import TamperRecordViewSet

router = DefaultRouter()
router.register(r'records', TamperRecordViewSet, basename='tamper-record')

urlpatterns = router.urls
