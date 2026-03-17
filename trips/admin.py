from django.contrib import admin
from .models import Trip, TripNode


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["id", "driver", "start_node", "end_node", "status", "max_passengers", "created_at"]
    search_fields = ["driver__username", "start_node__name", "end_node__name"]
    ordering = ["-created_at",]


@admin.register(TripNode)
class TripNodeAdmin(admin.ModelAdmin):
    list_display = ["id", "trip", "node", "order", "is_passed"]
    list_filter = ["is_passed",]
