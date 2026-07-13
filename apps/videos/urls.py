from django.urls import path

from .views import VideoDetailView

app_name = 'videos'

urlpatterns = [
    path('<slug:slug>/', VideoDetailView.as_view(), name='detail'),
]
