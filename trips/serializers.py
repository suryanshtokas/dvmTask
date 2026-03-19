from rest_framework import serializers
from .models import Trip, TripNode


class TripNodeSerializer(serializers.ModelSerializer):
    node_name = serializers.CharField(source="node.name", read_only=True)

    class Meta:
        model = TripNode
        fields = ["id", "node", "node_name", "order", "is_passed"]


class TripSerializer(serializers.ModelSerializer):
    trip_nodes = TripNodeSerializer(many=True, read_only=True)
    driver_username = serializers.CharField(source="driver.username", read_only=True)

    class Meta:
        model = Trip
        fields = ["id", "driver", "driver_username", "start_node", "end_node", "current_node", "status", "max_passengers", "trip_nodes"]
        