from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_video_mime, video_extension_validator


class PublishedVideoManager(models.Manager):
    """Public manager — only published videos for public views."""

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class VideoAsset(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    video_file = models.FileField(
        upload_to='videos/',
        validators=[video_extension_validator, validate_video_mime],
    )
    thumbnail = models.ImageField(
        upload_to='videos/thumbnails/',
        blank=True,
        null=True,
        help_text='Used as the video poster and for email/link previews. '
                  'Upload manually — email clients cannot embed video.',
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers — mirror surveys ClassifiedModel pattern
    objects = models.Manager()
    published_objects = PublishedVideoManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', '-created_at']),
        ]
        verbose_name = 'Video asset'
        verbose_name_plural = 'Video assets'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'video'
            slug = base_slug
            counter = 1
            while VideoAsset.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f'{base_slug}-{counter}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('videos:detail', kwargs={'slug': self.slug})
