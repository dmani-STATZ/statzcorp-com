from django.views.generic import DetailView

from .models import VideoAsset


class VideoDetailView(DetailView):
    """Public landing page for a published marketing video."""

    model = VideoAsset
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Unpublished / missing videos 404 — do not use the default manager
        return VideoAsset.published_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.object
        # build_absolute_uri leaves already-absolute Azure blob URLs unchanged
        context['og_page_url'] = self.request.build_absolute_uri()
        context['og_video_url'] = self.request.build_absolute_uri(video.video_file.url)
        if video.thumbnail:
            context['og_image_url'] = self.request.build_absolute_uri(video.thumbnail.url)
        else:
            context['og_image_url'] = None
        return context
