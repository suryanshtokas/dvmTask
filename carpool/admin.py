from django.contrib import admin
from .models import CarpoolRequest, CarpoolOffer, FareConfig

@admin.register(FareConfig)
class FareConfigAdmin(admin.ModelAdmin):
    list_display = ["unit_price", "base_fee", "updated_at"]

    def has_add_permission(self, request):
        if FareConfig.objects.exists(): # if multiple objects exist
            return False
        return True
    
@admin.register(CarpoolRequest)
class CarpoolRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "passenger", "pickup_node", "dropoff_node", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["passenger__username"]

@admin.register(CarpoolOffer)
class CarpoolOfferAdmin(admin.ModelAdmin):
    list_display = ["id", "trip", "carpool_request", "detour_length", "fare", "status"]
    list_filter = ["status"]
