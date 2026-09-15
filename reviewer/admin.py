from django.contrib import admin
from reviewer.models import AnalysisHistory


@admin.register(AnalysisHistory)
class AnalysisHistoryAdmin(admin.ModelAdmin):
    """
    Ye admin panel mein AnalysisHistory model ko customize karta hai —
    kaunse columns list mein dikhein, search/filter options waghera.
    """
    list_display = ("source_name", "user", "created_at")
    list_filter = ("user", "created_at")
    search_fields = ("source_name", "user__username")
    readonly_fields = ("results_json",)