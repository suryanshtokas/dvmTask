from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from network.models import Node
from .models import Trip, TripNode
from .forms import TripCreateForm
from .utils import find_shortest_route
from accounts.mixins import DriverRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import TripSerializer, TripNodeSerializer

from payments.models import Wallet, Transaction
from carpool.models import CarpoolOffer
from django.db import transaction


class TripCreateView(DriverRequiredMixin, CreateView):
    model = Trip
    form_class = TripCreateForm
    template_name = "trips/trip_create.html"
    success_url = reverse_lazy("trip_list")

    def form_valid(self, form):
        start_node = form.cleaned_data["start_node"]
        end_node = form.cleaned_data["end_node"]

        # finding shortest route
        route = find_shortest_route(start_node, end_node)

        if route is None:
            form.add_error(None, "No route found between the selected nodes.")
            return self.form_invalid(form)
        
        trip = form.save(commit=False)
        trip.driver = self.request.user
        trip.current_node = start_node
        trip.save()

        # save the path in tripnodes
        for index, node in enumerate(route):
            TripNode.objects.create(trip=trip, node=node, order=index)

        messages.success(self.request, "Trip created")
        return redirect(self.success_url)
    

class TripListView(DriverRequiredMixin, ListView):
    model = Trip
    template_name = "trips/trip_list.html"
    context_object_name = "trips"

    def get_queryset(self):
        return Trip.objects.filter(driver=self.request.user).order_by("-created_at")
    

class TripDetailView(DriverRequiredMixin, DetailView):
    model = Trip
    template_name = "trips/trip_detail.html"
    context_object_name = "trip"

    def get_queryset(self):
        # ensuring drivers can only view their own trips
        return Trip.objects.filter(driver=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        context["passed_nodes"] = trip.trip_nodes.filter(is_passed=True)
        context["remaining_nodes"] = trip.trip_nodes.filter(is_passed=False)
        return context


class TripCancelView(DriverRequiredMixin, View):

    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk, driver=request.user)

        if trip.status != "pending":
            messages.error(request, "Only pending trips can be cancelled.")
            return redirect("trip_detail", pk=pk)
        
        trip.status = "cancelled"
        trip.save()
        messages.success(request, "Trip cancelled.")
        return redirect("trip_list")


class UpdateCurrentNodeAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        trip  = get_object_or_404(Trip, pk=pk, driver=request.user)

        if trip.status not in ["pending", "active"]:
            return Response({"error": "Only pending or active trips can be updated."},
                             status=status.HTTP_400_BAD_REQUEST)

        node_id = request.data.get("node_id")
        if not node_id:
            return Response({"error": "node_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        trip_node = trip.trip_nodes.filter(node_id=node_id, is_passed=False).first()
        if not trip_node:
            return Response({"error": "Invalid node_id or node already passed."}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if we're at the end node, if yes, then handle the payments
        if trip_node.node_id == trip.end_node_id:
            confirmed_offers = CarpoolOffer.objects.filter(
                trip=trip,
                status="accepted",
            ).select_related("carpool_request__passenger__wallet")

            # checking if the passengers have sufficient balance
            for offer in confirmed_offers:
                passenger_wallet = offer.carpool_request.passenger.wallet
                if passenger_wallet.balance < offer.fare:
                    return Response({
                        "error": f"Passenger {offer.carpool_request.passenger.username} has insufficient balance.",
                        "required": str(offer.fare),
                        "available": str(passenger_wallet.balance)
                        }, 
                        status=status.HTTP_400_BAD_REQUEST)
                
            # process payments atomically to ensure data integrity
            with transaction.atomic():
                driver_wallet = request.user.wallet
                total_earnings = 0

                for offer in confirmed_offers:
                    passenger = offer.carpool_request.passenger
                    passenger_wallet = passenger.wallet
                    fare = offer.fare

                    passenger_wallet.balance -= fare
                    passenger_wallet.save()

                    total_earnings += fare

                    Transaction.objects.create(
                        user = passenger,
                        transaction_type = "deduction",
                        amount = fare,
                        trip = trip,
                        description = f"Fare (${fare}) for carpool from {offer.carpool_request.pickup_node} to {offer.carpool_request.dropoff_node}"
                    )

                    # mark carpool as completed
                    offer.carpool_request.status = "completed"
                    offer.carpool_request.save()

                driver_wallet.balance += total_earnings
                driver_wallet.save()

                Transaction.objects.create(
                    user = request.user,
                    transaction_type = "earning",
                    amount = total_earnings,
                    trip = trip,
                    description = f"Earnings from trip {trip.start_node} -> {trip.end_node}"
                )

        trip.trip_nodes.filter(order__lte=trip_node.order).update(is_passed=True)
        trip.current_node_id = node_id
        trip.status = "active"

        if trip.current_node_id == trip.end_node_id:
            trip.status = "completed"
        
        trip.save()

        return Response(TripSerializer(trip).data, status=status.HTTP_200_OK)
    
