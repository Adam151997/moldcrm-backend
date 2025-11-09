from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from api.views import LeadViewSet, ContactViewSet, DealViewSet, DashboardView

router = routers.DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'deals', DealViewSet, basename='deal')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api-auth/', include('rest_framework.urls')),
]