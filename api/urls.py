from django.urls import path, include
from rest_framework.authtoken import views
from . import views as api_views
from .views_auth import CustomAuthToken

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
    path('contacts/convert_from_lead/', api_views.ContactViewSet.as_view({'post': 'convert_from_lead'}), name='convert-from-lead'),
    
    # Deal endpoints with custom actions
    path('deals/', api_views.DealViewSet.as_view({'get': 'list', 'post': 'create'}), name='deals-list'),
    path('deals/<int:pk>/', api_views.DealViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='deals-detail'),
    path('deals/<int:pk>/update_stage/', api_views.DealViewSet.as_view({'patch': 'update_stage'}), name='deal-update-stage'),
    path('deals/pipeline_analytics/', api_views.DealViewSet.as_view({'get': 'pipeline_analytics'}), name='pipeline-analytics'),
    
    # Dashboard
    path('dashboard/', api_views.DashboardView.as_view(), name='dashboard'),
]