from django.db import models
from django.contrib.auth.models import User 
from network.models import Node
from trips.models import Trip


class FareConfig(models.Model):
    # unit price p
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    base_fee = models.DecimalField(max_digits=6, decimal_places=2, default=2.00)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fare Configuration"

    def __str__(self):
        return f"Fare Config (p={self.unit_price}, base_fee={self.base_fee})"
    

class CarpoolRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carpool_requests")
    pickup_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="pickup_requests")
    dropoff_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="dropoff_requests")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    proximity_nodes = models.ManyToManyField(Node, related_name="proximity_requests", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger.username}: {self.pickup_node} -> {self.dropoff_node} ({self.status})"
    

class CarpoolOffer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="carpool_offers")
    carpool_request = models.ForeignKey(CarpoolRequest, on_delete=models.CASCADE, related_name="offers")
    detour_length = models.PositiveIntegerField()
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("trip", "carpool_request")

    def __str__(self):
        return f"Offer by {self.trip.driver.username} for {self.carpool_request} (Fare: ${self.fare}, Status: {self.status})"
