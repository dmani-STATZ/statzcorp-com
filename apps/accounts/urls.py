from django.urls import path

from .views import (
    StaffPasswordResetCompleteView,
    StaffPasswordResetConfirmView,
    StaffPasswordResetDoneView,
    StaffPasswordResetView,
)

app_name = 'accounts'

urlpatterns = [
    path(
        'password-reset/',
        StaffPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        StaffPasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'password-reset/confirm/<uidb64>/<token>/',
        StaffPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        StaffPasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
]
