from django.urls import path
from .views import TripCreateView, TripListView, TripCancelView, TripDetailView, UpdateCurrentNodeAPI

urlpatterns = [
    path("", TripListView.as_view(), name="trip_list"),
    path("create/", TripCreateView.as_view(), name="trip_create"),
    path("<int:pk>/", TripDetailView.as_view(), name="trip_detail"),
    path("<int:pk>/cancel/", TripCancelView.as_view(), name="trip_cancel"),
    path("<int:pk>/update-node", UpdateCurrentNodeAPI.as_view(), name="update_current_node"),
]