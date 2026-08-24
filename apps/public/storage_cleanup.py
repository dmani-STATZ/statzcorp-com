import logging

logger = logging.getLogger('apps')

_IMAGE_FIELDS = {
    'TeamMember': 'photo',
    'TeamPageBanner': 'image',
}


def _image_field_name(sender):
    return _IMAGE_FIELDS.get(sender.__name__)


def _delete_file(field_file, *, model_name, field_name):
    if not field_file or not field_file.name:
        return
    try:
        if field_file.storage.exists(field_file.name):
            field_file.storage.delete(field_file.name)
    except Exception:
        logger.exception(
            'Failed to delete old storage file for %s.%s',
            model_name,
            field_name,
        )


def delete_old_file_on_change(sender, instance, **kwargs):
    """Delete a replaced image through its configured storage backend."""
    field_name = _image_field_name(sender)
    if not field_name or not instance.pk:
        return

    try:
        current = sender.objects.only(field_name).get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    except Exception:
        logger.exception(
            'Failed to inspect old storage file for %s.%s',
            sender.__name__,
            field_name,
        )
        return

    old_file = getattr(current, field_name)
    new_file = getattr(instance, field_name)
    if old_file.name and old_file.name != new_file.name:
        _delete_file(
            old_file,
            model_name=sender.__name__,
            field_name=field_name,
        )


def delete_file_on_instance_delete(sender, instance, **kwargs):
    """Delete an instance image through its configured storage backend."""
    field_name = _image_field_name(sender)
    if not field_name:
        return
    _delete_file(
        getattr(instance, field_name),
        model_name=sender.__name__,
        field_name=field_name,
    )
