from django.db import models
from django.contrib.auth.models import User
from network.models import Node


class Trip(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips")
    start_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="trips_starting_here")
    end_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="trips_ending_here")
    current_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null=True, blank=True, related_name="trips_currently_here")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    max_passengers = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver.username}: {self.start_node} → {self.end_node} ({self.status})"
    

class TripNode(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="trip_nodes")
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    is_passed = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        unique_together = ("trip", "order")

    def __str__(self):
        return f"{self.trip} - {self.node} (order {self.order})"