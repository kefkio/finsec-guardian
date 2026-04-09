from django.urls import path, include

urlpatterns = [
    path('api/scanner/', include('scanner.urls')),
    path('api/threats/', include('threats.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/records/', include('records.urls')),
]
