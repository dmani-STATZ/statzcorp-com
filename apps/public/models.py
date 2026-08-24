from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.db import models

HERO_MIN_WIDTH = 1600
HERO_MIN_RATIO = 1.5
HERO_MAX_RATIO = 4.0
TEAM_MEMBER_MIN_WIDTH = 200
TEAM_MEMBER_MIN_RATIO = 0.8
TEAM_MEMBER_MAX_RATIO = 1.5


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


class PublishedTeamPageBannerManager(models.Manager):
    """Public manager — only published banners, newest update first."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True)
            .order_by('-updated_at')
        )


class TeamPageBanner(models.Model):
    image = models.ImageField(upload_to='team/banner/')
    alt_text = models.CharField(
        max_length=255,
        help_text='Accessible description rendered as the image alt attribute.',
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published_objects = PublishedTeamPageBannerManager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Team page banner'
        verbose_name_plural = 'Team page banners'

    def __str__(self):
        return self.alt_text


class PublishedTeamGroupManager(models.Manager):
    """Public manager — only published team groups in display order."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True)
            .order_by('sort_order', 'id')
        )


class TeamGroup(models.Model):
    heading = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published_objects = PublishedTeamGroupManager()

    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['is_published', 'sort_order']),
        ]

    def __str__(self):
        return self.heading


class TeamMember(models.Model):
    PHOTO_ALIGN_LEFT = 'left'
    PHOTO_ALIGN_RIGHT = 'right'
    PHOTO_ALIGN_CHOICES = (
        (PHOTO_ALIGN_LEFT, 'Left'),
        (PHOTO_ALIGN_RIGHT, 'Right'),
    )

    group = models.ForeignKey(
        TeamGroup,
        on_delete=models.CASCADE,
        related_name='members',
    )
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='team/members/')
    photo_align = models.CharField(
        max_length=5,
        choices=PHOTO_ALIGN_CHOICES,
        default=PHOTO_ALIGN_LEFT,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group', 'sort_order', 'id']
        indexes = [
            models.Index(fields=['group', 'is_published', 'sort_order']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.photo:
            return
        try:
            width, height = get_image_dimensions(self.photo)
        except Exception:
            return
        if not width or not height:
            return
        ratio = width / height
        # Adjustable if the design changes; these bounds reflect existing
        # near-square team assets (roughly 150×150 through 300×300).
        if (
            width < TEAM_MEMBER_MIN_WIDTH
            or ratio < TEAM_MEMBER_MIN_RATIO
            or ratio > TEAM_MEMBER_MAX_RATIO
        ):
            raise ValidationError({
                'photo': (
                    f'Image is {width}×{height} (ratio {ratio:.2f}). '
                    f'Team photos must have a ratio between '
                    f'{TEAM_MEMBER_MIN_RATIO} and {TEAM_MEMBER_MAX_RATIO}, '
                    f'with a minimum width of {TEAM_MEMBER_MIN_WIDTH}px.'
                ),
            })
