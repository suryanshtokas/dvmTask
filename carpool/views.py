from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import CreateView, ListView, DetailView, View
from django.urls import reverse_lazy
from accounts.mixins import DriverRequiredMixin, PassengerRequiredMixin
from network.models import Node
from trips.models import Trip, TripNode
from .models import CarpoolOffer, CarpoolRequest
from .forms import CarpoolRequestForm
from .utils import get_proximity_nodes, get_remaining_route, calculate_detour, calculate_fare

from .serializers import CarpoolRequestSerializer, CarpoolOfferSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


class CarpoolRequestCreateView(PassengerRequiredMixin, CreateView):
    model = CarpoolRequest
    form_class = CarpoolRequestForm
    template_name = "carpool/request_create.html"
    success_url = reverse_lazy("carpool_request_list")

    def form_valid(self, form):
        carpool_request = form.save(commit=False)
        carpool_request.passenger = self.request.user
        carpool_request.save()

        proximity = get_proximity_nodes(carpool_request.pickup_node)
        carpool_request.proximity_nodes.set(proximity)

        messages.success(self.request, "Carpool request created successfully!")
        return redirect(self.success_url)
    

class CarpoolRequestListView(PassengerRequiredMixin, ListView):
    model = CarpoolRequest
    template_name = "carpool/request_list.html"
    context_object_name = "carpool_requests"

    def get_queryset(self):
        return CarpoolRequest.objects.filter(passenger=self.request.user).order_by("-created_at")


class CarpoolRequestDetailView(PassengerRequiredMixin, DetailView):
    model = CarpoolRequest
    template_name = "carpool/request_detail.html"
    context_object_name = "carpool_request"

    def get_queryset(self):
        return CarpoolRequest.objects.filter(passenger=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["offers"] = self.object.offers.filter(status="pending")
        return context


class CarpoolOfferSelectView(PassengerRequiredMixin, View):

    def post(self, request, pk):
        offer = get_object_or_404(CarpoolOffer, pk=pk, carpool_request__passenger=request.user)
        carpool_request = offer.carpool_request

        if carpool_request.status != "pending":
            messages.error(request, "This carpool request is no longer available.")
            return redirect("carpool_request_detail", pk=carpool_request.pk)
        
        carpool_request.offers.exclude(pk=offer.pk).update(status="rejected") # reject other offers
        offer.status = "accepted"
        offer.save()

        carpool_request.status = "confirmed"
        carpool_request.save()

        messages.success(request, f"Carpool confirmed with {offer.trip.driver.username}!")
        return redirect("carpool_request_detail", pk=carpool_request.pk)


class CarpoolRequestCancelView(PassengerRequiredMixin, View):

    def post(self, request, pk):
        carpool_request = get_object_or_404(CarpoolRequest, pk=pk, passenger=request.user)

        if carpool_request.status != "pending":
            messages.error(request, "only pending carpool requests can be cancelled.")
            return redirect("carpool_request_detail", pk=pk)
        
        carpool_request.status = "cancelled"
        carpool_request.save()

        messages.success(request, "Carpool request cancelled.")
        return redirect("carpool_request_list")
    


class DriverCarpoolRequestListView(DriverRequiredMixin, ListView):
    template_name = "carpool/driver_request_list.html"
    context_object_name = "carpool_requests"

    def get_queryset(self):
        trip = get_object_or_404(Trip, driver=self.request.user, pk=self.kwargs["trip_pk"])
        remaining_route = get_remaining_route(trip)
        remaining_node_ids = [node.id for node in remaining_route]

        # filtering out requests whose proximity_nodes in remaining route
        return CarpoolRequest.objects.filter(status="pending",
            proximity_nodes__id__in=remaining_node_ids).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = get_object_or_404(Trip, pk=self.kwargs["trip_pk"], driver=self.request.user)
        return context  
    

class CarpoolOfferCreateView(DriverRequiredMixin, View):

    def post(self, request, trip_pk, request_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, driver=request.user)
        carpool_request = get_object_or_404(CarpoolRequest, pk=request_pk, status="pending")

        if CarpoolOffer.objects.filter(trip=trip, carpool_request=carpool_request).exists():
            messages.error(request, "You have already made an offer for this request.")
            return redirect("driver_carpool_request_list", trip_pk=trip_pk)
        
        confirmed_offers = CarpoolOffer.objects.filter(trip=trip, status="accepted").select_related(
            "carpooL_request__pickup_node", "carpool_request__dropoff_node"
        )

        confirmed_passengers = [
            (offer.carpool_request.pickup_node, offer.carpool_request.dropoff_node)
            for offer in confirmed_offers
        ]

        detour, new_route = calculate_detour(trip, carpool_request.pickup_node, carpool_request.dropoff_node)

        if detour is None:
            messages.error(request, "Cannot calculate valid detour for this request.")
            return redirect("driver_carpool_request_list", trip_pk=trip_pk)
        
        fare = calculate_fare(new_route, confirmed_passengers, carpool_request.pickup_node, carpool_request.dropoff_node)

        CarpoolOffer.objects.create(
            trip = trip,
            carpool_request = carpool_request,
            detour_length = detour,
            fare = fare
        )

        messages.success(request, f"Offer created successfully")
        return redirect("driver_carpool_request_list", trip_pk=trip_pk)


class CarpoolRequestListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, driver=request.user)

        remaining_route = get_remaining_route(trip)
        remaining_node_ids = [node.id for node in remaining_route]

        carpool_requests = CarpoolRequest.objects.filter(
            status="pending",
            proximity_nodes__id__in=remaining_node_ids
        ).distinct()

        serializer = CarpoolRequestSerializer(carpool_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
