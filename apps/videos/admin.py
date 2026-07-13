from django.contrib import admin

from .models import VideoAsset


@admin.register(VideoAsset)
class VideoAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
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
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
