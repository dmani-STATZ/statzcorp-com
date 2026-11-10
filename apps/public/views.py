from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse
from django.views.generic import TemplateView

from apps.public.inventory_diagnostics import run_inventory_connection_check
from apps.public.inventory_service import get_public_inventory_snapshot

from .models import HeroSlide, TeamGroup, TeamMember, TeamPageBanner


class IndexView(TemplateView):
    template_name = 'public/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hero_slides'] = HeroSlide.published_objects.all()
        return context

class AboutUsView(TemplateView):
    template_name = 'public/about-us.html'

class OurTeamView(TemplateView):
    template_name = 'public/our-team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_banner'] = TeamPageBanner.published_objects.first()
        context['groups'] = TeamGroup.published_objects.prefetch_related(
            Prefetch(
                'members',
                queryset=TeamMember.objects.filter(is_published=True),
            )
        )
        return context

class CapabilitiesView(TemplateView):
    template_name = 'public/capabilities.html'

class ProductsView(TemplateView):
    template_name = 'public/products.html'

class AccreditationsView(TemplateView):
    template_name = 'public/accreditations.html'

class ResourcesView(TemplateView):
    template_name = 'public/resources.html'


def _digits(value):
    return ''.join(ch for ch in value if ch.isdigit())


def _inventory_item_matches(item, q_lower, q_digits):
    haystacks = (
        item.get('description', ''),
        item.get('part_number', ''),
        item.get('manufacturer', ''),
        item.get('nsn_display', ''),
    )
    if any(q_lower in str(value).lower() for value in haystacks):
        return True
    return len(q_digits) >= 4 and q_digits in str(item.get('nsn_digits', ''))


class PublicInventoryListView(TemplateView):
    http_method_names = ['get']
    template_name = 'public/inventory_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '')
        q = q.strip()[:100]
        snapshot = get_public_inventory_snapshot()
        items = snapshot.items
        if q:
            q_lower = q.lower()
            q_digits = _digits(q)
            items = [
                item for item in items
                if _inventory_item_matches(item, q_lower, q_digits)
            ]
        paginator = Paginator(items, 25)
        context['page_obj'] = paginator.get_page(self.request.GET.get('page'))
        context['q'] = q
        context['total_count'] = len(items)
        context['snapshot_available'] = snapshot.available
        context['snapshot_is_stale'] = snapshot.is_stale
        context['fetched_at'] = snapshot.fetched_at
        context['contact_url'] = reverse('contact:contact_us')
        return context


class InventoryConnectionCheckView(UserPassesTestMixin, TemplateView):
    """TEMPORARY staff-only inventory connection check. See inventory_diagnostics.py."""

    http_method_names = ['get']
    template_name = 'public/inventory_connection_check.html'
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_active and user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = run_inventory_connection_check()
        return context
