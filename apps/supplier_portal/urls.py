from django.urls import path

from .views import (
    ApiConnectionTestView,
    RequestAccessView,
    SendPasswordLinkView,
    SetPasswordView,
    SupplierDashboardView,
    SupplierLoginView,
    SupplierLogoutView,
)

app_name = 'supplier_portal'

urlpatterns = [
    path('', SupplierLoginView.as_view(), name='login'),
    path('logout/', SupplierLogoutView.as_view(), name='logout'),
    path('dashboard/', SupplierDashboardView.as_view(), name='dashboard'),
    path('request-access/', RequestAccessView.as_view(), name='request_access'),
    path('request-access/send/', SendPasswordLinkView.as_view(), name='send_password_link'),
    path('set-password/<str:token>/', SetPasswordView.as_view(), name='set_password'),
    # TEMPORARY — remove once production VNet integration to STATZWeb is confirmed.
    path('api-test/', ApiConnectionTestView.as_view(), name='api_test'),
]
