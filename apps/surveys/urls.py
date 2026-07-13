from django.urls import path
from .views import SurveyListView, survey_detail_view

app_name = 'surveys'

urlpatterns = [
    path('', SurveyListView.as_view(), name='list'),
    path('<int:pk>/', survey_detail_view, name='detail'),
]
