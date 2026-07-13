from django.apps import AppConfig


class PublicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.public'

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = 'STATZ Corporation Administration'
        admin.site.site_title = 'STATZ Admin'
        admin.site.index_title = 'Site Management'
