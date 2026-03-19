from rest_framework import serializers
from .models import CarpoolRequest, CarpoolOffer


class CarpoolOfferSerializer(serializers.ModelSerializer):
    driver_username = serializers.CharField(source="trip.driver.username", read_only=True)
    trip_start = serializers.CharField(source="trip.start_node.name", read_only=True)
    trip_end = serializers.CharField(source="trip.end_node.name", read_only=True)

    class Meta:
        model = CarpoolOffer
        fields = ["id", "driver_username", "trip_start", "trip_end", "detour_length", "fare", "status"]


class CarpoolRequestSerializer(serializers.ModelSerializer):
    passenger_username = serializers.CharField(source="passenger.username", read_only=True)
    pickup_node_name = serializers.CharField(source="pickup_node.name", read_only=True)
    dropoff_node_name = serializers.CharField(source="dropoff_node.name", read_only=True)
    offers = CarpoolOfferSerializer(many=True, read_only=True)

    class Meta:
        model = CarpoolRequest
        fields = ["id", "passenger_username", "pickup_node_name", "dropoff_node_name", "status", "offers", "created_at"]