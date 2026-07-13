from django.shortcuts import render
from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'public/index.html'

class AboutUsView(TemplateView):
    template_name = 'public/about-us.html'

class OurTeamView(TemplateView):
    template_name = 'public/our-team.html'

class CapabilitiesView(TemplateView):
    template_name = 'public/capabilities.html'

class ProductsView(TemplateView):
    template_name = 'public/products.html'

class AccreditationsView(TemplateView):
    template_name = 'public/accreditations.html'

class ResourcesView(TemplateView):
    template_name = 'public/resources.html'
