"""
WebIntel URL Configuration

API endpoints for web intelligence module.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebScanViewSet, WebFindingViewSet, WebThreatViewSet, WebIntelligenceReportViewSet
)

router = DefaultRouter()
router.register(r'scans', WebScanViewSet, basename='webscan')
router.register(r'findings', WebFindingViewSet, basename='webfinding')
router.register(r'threats', WebThreatViewSet, basename='webthreat')
router.register(r'reports', WebIntelligenceReportViewSet, basename='webintelligence-report')

urlpatterns = [
    path('', include(router.urls)),
]
