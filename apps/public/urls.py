from django.urls import path
from .views import (
    IndexView,
    AboutUsView,
    OurTeamView,
    CapabilitiesView,
    ProductsView,
    AccreditationsView,
)

app_name = 'public'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('about-us/', AboutUsView.as_view(), name='about_us'),
    path('our-team/', OurTeamView.as_view(), name='our_team'),
    path('capabilities/', CapabilitiesView.as_view(), name='capabilities'),
    path('products/', ProductsView.as_view(), name='products'),
    path('accreditations/', AccreditationsView.as_view(), name='accreditations'),
]
