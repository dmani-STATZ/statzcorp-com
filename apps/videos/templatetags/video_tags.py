from django import template

from apps.videos.models import VideoAsset

register = template.Library()


@register.simple_tag
def get_video(slug):
    """Return a published VideoAsset by slug, or None if missing/unpublished."""
    return VideoAsset.published_objects.filter(slug=slug).first()
