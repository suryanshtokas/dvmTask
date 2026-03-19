from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect


class DriverRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.profile.role != "driver":
            messages.error(request, "Only drivers can access this page.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)
    

class PassengerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.profile.role != "passenger":
            messages.error(request, "Only passengers can access this page.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)