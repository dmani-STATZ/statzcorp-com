from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import HeroSlide, TeamGroup, TeamMember, TeamPageBanner


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


class TeamMemberInline(admin.StackedInline):
    model = TeamMember
    extra = 0
    readonly_fields = ('thumbnail_preview', 'created_at', 'updated_at')
    fields = (
        'name',
        'title',
        'bio',
        'photo',
        'thumbnail_preview',
        'photo_align',
        'sort_order',
        'is_published',
        'created_at',
        'updated_at',
    )

    @admin.display(description='Preview')
    def thumbnail_preview(self, obj):
        if not obj or not obj.photo:
            return '—'
        return format_html(
            '<img src="{}" style="height:50px; width:auto; border-radius:4px;" />',
            obj.photo.url,
        )


@admin.register(TeamGroup)
class TeamGroupAdmin(admin.ModelAdmin):
    list_display = (
        'heading',
        'member_count',
        'sort_order',
        'is_published',
        'updated_at',
    )
    list_editable = ('sort_order', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('heading', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (TeamMemberInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_member_count=Count('members'))

    @admin.display(description='Members', ordering='_member_count')
    def member_count(self, obj):
        return obj._member_count


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_preview',
        'name',
        'group',
        'sort_order',
        'is_published',
        'updated_at',
    )
    list_editable = ('sort_order', 'is_published')
    list_filter = ('group', 'is_published')
    search_fields = ('name', 'title', 'bio', 'group__heading')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': (
                'group',
                'name',
                'title',
                'bio',
                'photo_align',
                'sort_order',
                'is_published',
            ),
        }),
        ('Media', {
            'fields': ('photo', 'image_preview'),
            'description': (
                'Near-square images are required (ratio 0.8–1.5) with a '
                'minimum width of 200px. Images are stored in Azure Blob '
                'Storage when AZURE_CONNECTION_STRING is configured; otherwise '
                'locally under MEDIA_ROOT.'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Preview')
    def thumbnail_preview(self, obj):
        if not obj or not obj.photo:
            return '—'
        return format_html(
            '<img src="{}" style="height:50px; width:auto; border-radius:4px;" />',
            obj.photo.url,
        )

    @admin.display(description='Current image')
    def image_preview(self, obj):
        if not obj or not obj.photo:
            return 'Save the member after uploading to preview the image.'
        return format_html(
            '<img src="{}" style="max-width:100%; max-height:320px; '
            'width:auto; height:auto; border-radius:4px;" />',
            obj.photo.url,
        )


@admin.register(TeamPageBanner)
class TeamPageBannerAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_preview',
        'alt_text',
        'is_published',
        'updated_at',
    )
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    search_fields = ('alt_text',)
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('alt_text', 'is_published'),
        }),
        ('Media', {
            'fields': ('image', 'image_preview'),
            'description': (
                'Full-width team banner. Images are stored in Azure Blob '
                'Storage when AZURE_CONNECTION_STRING is configured; otherwise '
                'locally under MEDIA_ROOT.'
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
            return 'Save the banner after uploading to preview the image.'
        return format_html(
            '<img src="{}" style="max-width:100%; max-height:320px; '
            'width:auto; height:auto; border-radius:4px;" />',
            obj.image.url,
        )
