from django.contrib import admin
from .models import Question, Speaker, Event

admin.site.register(Question)
admin.site.register(Speaker)
admin.site.register(Event)

