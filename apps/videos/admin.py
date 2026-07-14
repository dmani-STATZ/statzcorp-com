from django.contrib import admin
from django.utils.html import format_html

from .models import VideoAsset


def _copy_button(url, label='Copy'):
    """Clipboard copy button; URL escaped via format_html (secure-context only)."""
    return format_html(
        '<button type="button" data-url="{}" data-label="{}" '
        'onclick="navigator.clipboard.writeText(this.dataset.url);'
        "this.textContent='Copied!';"
        "setTimeout(()=>this.textContent=this.dataset.label,1500)\""
        '>{}</button>',
        url,
        label,
        label,
    )


@admin.register(VideoAsset)
class VideoAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'video_url_display', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'public_video_url',
        'landing_page_url',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'is_published'),
        }),
        ('Media', {
            'fields': ('video_file', 'thumbnail'),
            'description': (
                'Videos are stored in Azure Blob Storage when '
                'AZURE_CONNECTION_STRING is configured; otherwise locally under MEDIA_ROOT.'
            ),
        }),
        ('Share Links', {
            'fields': ('public_video_url', 'landing_page_url'),
            'description': (
                'Public Blob URL and shareable landing page. Save the record after '
                'uploading to generate these links.'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Public video URL')
    def public_video_url(self, obj):
        if not obj or not obj.pk or not obj.video_file:
            return 'Save the video first to generate its URL.'
        url = obj.video_file.url
        return format_html(
            '<p><a href="{0}" target="_blank" rel="noopener noreferrer">{0}</a></p>'
            '<p><input type="text" readonly value="{0}" '
            'style="width:100%;box-sizing:border-box;" onclick="this.select()"></p>'
            '<p>{1}</p>',
            url,
            _copy_button(url, 'Copy'),
        )

    @admin.display(description='Landing page URL')
    def landing_page_url(self, obj):
        if not obj or not obj.pk:
            return 'Save the video first to generate its URL.'
        path = obj.get_absolute_url()
        return format_html(
            '<p><a href="{0}">Open landing page</a></p>'
            '<p>Shareable page for emails (relative path: <code>{0}</code>).</p>',
            path,
        )

    @admin.display(description='Video URL')
    def video_url_display(self, obj):
        if not obj or not obj.pk or not obj.video_file:
            return '—'
        return _copy_button(obj.video_file.url, 'Copy URL')
