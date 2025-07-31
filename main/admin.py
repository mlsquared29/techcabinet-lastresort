from django.contrib import admin

from .models import Question, Solution, Answer

admin.site.register(Question)
admin.site.register(Solution)
admin.site.register(Answer)