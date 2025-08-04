from django.contrib import admin
from django.utils import timezone
from .models import PSAGroup, PSAEntry, AIResponse, Competition

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'pub_date', 'end_date', 'is_active', 'status')
    list_filter = ('is_active', 'pub_date', 'end_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'pub_date'
    filter_horizontal = ('user',)
    
    def status(self, obj):
        if obj.is_past_end_date():
            return 'Ended'
        elif obj.is_active:
            return 'Active'
        else:
            return 'Inactive'
    status.short_description = 'Status'

admin.site.register(PSAGroup)
admin.site.register(PSAEntry)
admin.site.register(AIResponse)