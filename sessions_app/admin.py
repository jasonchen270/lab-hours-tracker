from django.contrib import admin

from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "start_at", "end_at", "is_open")
    list_filter = ("user",)
    search_fields = ("user__username", "notes")
    date_hierarchy = "start_at"

    @admin.display(boolean=True, description="Open?")
    def is_open(self, obj: Session) -> bool:
        return obj.is_open
