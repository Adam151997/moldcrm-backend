from django.urls import path, include
from rest_framework.authtoken import views
from . import views as api_views
from .views_dashboard import DashboardView
from .views_auth import CustomAuthToken  # ADD THIS IMPORT

urlpatterns = [
    # Authentication - USE CUSTOM AUTH
    path('auth/login/', CustomAuthToken.as_view(), name='login'),
    
    # User endpoints
    path('users/profile/', api_views.UserProfileView.as_view(), name='user-profile'),
    
    # CRM endpoints
    path('leads/', api_views.LeadViewSet.as_view({'get': 'list', 'post': 'create'}), name='leads-list'),
    path('leads/<int:pk>/', api_views.LeadViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='leads-detail'),
    
    path('contacts/', api_views.ContactViewSet.as_view({'get': 'list', 'post': 'create'}), name='contacts-list'),
    path('contacts/<int:pk>/', api_views.ContactViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='contacts-detail'),
    
    path('deals/', api_views.DealViewSet.as_view({'get': 'list', 'post': 'create'}), name='deals-list'),
    path('deals/<int:pk>/', api_views.DealViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='deals-detail'),
    
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]