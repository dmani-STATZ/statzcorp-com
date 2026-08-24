from django.apps import AppConfig


class PublicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.public'

    def ready(self):
        from django.contrib import admin
        from django.db.models.signals import post_delete, pre_save

        from .models import TeamMember, TeamPageBanner
        from .storage_cleanup import (
            delete_file_on_instance_delete,
            delete_old_file_on_change,
        )

        admin.site.site_header = 'STATZ Corporation Administration'
        admin.site.site_title = 'STATZ Admin'
        admin.site.index_title = 'Site Management'

        for model in (TeamMember, TeamPageBanner):
            pre_save.connect(
                delete_old_file_on_change,
                sender=model,
                dispatch_uid=f'public.delete_old_{model._meta.label_lower}',
            )
            post_delete.connect(
                delete_file_on_instance_delete,
                sender=model,
                dispatch_uid=f'public.delete_deleted_{model._meta.label_lower}',
            )
