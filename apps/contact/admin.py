from django.contrib import admin
from .models import ContactMessage, ContactRecipient


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'company', 'email', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(ContactRecipient)
class ContactRecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'label', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('email', 'label')
    readonly_fields = ('created_at',)
    ordering = ('email',)
