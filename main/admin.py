from django.contrib import admin

from .models import PSAGroup, PSAEntry, AIResponse

admin.site.register(PSAGroup)
admin.site.register(PSAEntry)
admin.site.register(AIResponse)