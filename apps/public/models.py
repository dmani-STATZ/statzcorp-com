from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.db import models

HERO_MIN_WIDTH = 1600
HERO_MIN_RATIO = 1.5
HERO_MAX_RATIO = 4.0


class PublishedHeroSlideManager(models.Manager):
    """Public manager — only published slides for the home page hero."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True)
            .order_by('sort_order', 'id')
        )


class HeroSlide(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Internal label for admin lists — not shown on the public site.',
    )
    alt_text = models.CharField(
        max_length=255,
        help_text='Accessible description rendered as the image alt attribute.',
    )
    image = models.ImageField(upload_to='hero_slides/')
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published_objects = PublishedHeroSlideManager()

    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['is_published', 'sort_order']),
        ]
        verbose_name = 'Hero slide'
        verbose_name_plural = 'Hero slides'

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.image:
            return
        try:
            width, height = get_image_dimensions(self.image)
        except Exception:
            return
        if not width or not height:
            return
        ratio = width / height
        if (
            width < HERO_MIN_WIDTH
            or ratio < HERO_MIN_RATIO
            or ratio > HERO_MAX_RATIO
        ):
            raise ValidationError(
                f'Image is {width}×{height} (ratio {ratio:.2f}). '
                f'Hero slides must be landscape, ratio between {HERO_MIN_RATIO} '
                f'and {HERO_MAX_RATIO} — 2000×615 (panoramic, ~3.25) recommended '
                f'to match the hero band; minimum width {HERO_MIN_WIDTH}px.'
            )
