from django.contrib import admin
from django.utils.html import format_html

from .models import HeroSlide


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_preview',
        'title',
        'sort_order',
        'is_published',
        'updated_at',
    )
    list_editable = ('sort_order', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('title', 'alt_text')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'alt_text', 'sort_order', 'is_published'),
        }),
        ('Media', {
            'fields': ('image', 'image_preview'),
            'description': (
                'Landscape images only — 2000×615 (panoramic) recommended to '
                'match the existing hero band; 16:9 also accepted but will crop '
                'more on desktop. Minimum width 1600px. Images are stored in '
                'Azure Blob Storage when AZURE_CONNECTION_STRING is configured; '
                'otherwise locally under MEDIA_ROOT.'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Preview')
    def thumbnail_preview(self, obj):
        if not obj or not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="height:50px; width:auto; border-radius:4px;" />',
            obj.image.url,
        )

    @admin.display(description='Current image')
    def image_preview(self, obj):
        if not obj or not obj.image:
            return 'Save the slide after uploading to preview the image.'
        return format_html(
            '<img src="{}" style="max-width:100%; max-height:320px; '
            'width:auto; height:auto; border-radius:4px;" />',
            obj.image.url,
        )
