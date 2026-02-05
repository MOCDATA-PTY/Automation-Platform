from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('turnover/', views.turnover, name='turnover'),
    path('pnl/', views.pnl, name='pnl'),
    path('sync/', views.sync_data, name='sync_data'),
    path('sync/progress/', views.sync_progress, name='sync_progress'),
    path('onedrive/auth/', views.onedrive_auth, name='onedrive_auth'),
    path('onedrive/callback/', views.onedrive_callback, name='onedrive_callback'),
    path('onedrive/check/', views.onedrive_check, name='onedrive_check'),
]
