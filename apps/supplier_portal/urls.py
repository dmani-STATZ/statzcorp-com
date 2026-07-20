from django.urls import path

from .views import SupplierDashboardView, SupplierLoginView, SupplierLogoutView

app_name = 'supplier_portal'

urlpatterns = [
    path('', SupplierLoginView.as_view(), name='login'),
    path('logout/', SupplierLogoutView.as_view(), name='logout'),
    path('dashboard/', SupplierDashboardView.as_view(), name='dashboard'),
]
