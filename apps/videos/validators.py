from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

ALLOWED_VIDEO_EXTENSIONS = ('mp4', 'webm', 'ogg', 'mov', 'm4v')

ALLOWED_VIDEO_CONTENT_TYPES = frozenset({
    'video/mp4',
    'video/webm',
    'video/ogg',
    'video/quicktime',
    'video/x-m4v',
    'video/x-msvideo',
    'application/octet-stream',  # some browsers omit a specific video MIME type
})

video_extension_validator = FileExtensionValidator(
    allowed_extensions=list(ALLOWED_VIDEO_EXTENSIONS),
)


@deconstructible
class VideoMimeTypeValidator:
    """Reject uploads whose declared content type is not a known video type."""

    message = 'Upload a valid video file (MP4, WebM, OGG, MOV, or M4V).'
    code = 'invalid_video_type'

    def __call__(self, value):
        content_type = getattr(value, 'content_type', None)
        if content_type and content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
            raise ValidationError(self.message, code=self.code)


validate_video_mime = VideoMimeTypeValidator()
