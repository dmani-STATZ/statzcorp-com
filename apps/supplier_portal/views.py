from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from .auth import get_current_account, login_supplier, logout_supplier
from .forms import SupplierLoginForm


class SupplierLoginRequiredMixin:
    """Gate for portal pages — checks the supplier_portal session, not request.user."""

    def dispatch(self, request, *args, **kwargs):
        account = get_current_account(request)
        if account is None:
            messages.info(request, "Please log in to view your supplier data.")
            return redirect('supplier_portal:login')
        request.supplier_account = account
        return super().dispatch(request, *args, **kwargs)


class SupplierLoginView(FormView):
    template_name = 'supplier_portal/login.html'
    form_class = SupplierLoginForm
    success_url = reverse_lazy('supplier_portal:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if get_current_account(request) is not None:
            return redirect('supplier_portal:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login_supplier(self.request, form.account)
        return super().form_valid(form)


class SupplierLogoutView(View):
    def post(self, request, *args, **kwargs):
        logout_supplier(request)
        messages.success(request, "You have been logged out.")
        return redirect('supplier_portal:login')


class SupplierDashboardView(SupplierLoginRequiredMixin, TemplateView):
    template_name = 'supplier_portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.request.supplier_account
        return context
