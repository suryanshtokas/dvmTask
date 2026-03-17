from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from network.models import Node
from .models import Trip, TripNode
from .forms import TripCreateForm
from .utils import find_shortest_route


class DriverRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.profile.role != "driver":
            messages.error(request, "Only drivers can access this page.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)
    

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