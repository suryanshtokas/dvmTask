from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.contrib.auth import login
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile
from django.shortcuts import redirect
from django.contrib import messages


class UserRegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        user.profile.role = form.cleaned_data["role"]
        user.profile.save()

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(self.success_url)
    

class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = "accounts/login.html"
    next_page = reverse_lazy("dashboard")


class CustomLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy("login")


class DashboardView(LoginRequiredMixin, TemplateView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.profile.role:
            return redirect("role_select")
        return super().dispatch(request, *args, **kwargs)

    # depending on the role, we can show different dashboards
    def get_template_names(self):
        role = self.request.user.profile.role
        if role == "driver":
            return ["accounts/driver_dashboard.html"]
        return ["accounts/passenger_dashboard.html"]


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = UserUpdateForm(instance=self.request.user)
        context["profile_form"] = ProfileUpdateForm(instance=self.request.user.profile)
        return context
    
    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("dashboard")
        return self.render_to_response(self.get_context_data())
    

class RoleSelectView(LoginRequiredMixin, View):

    def get(self, request):
        if request.user.profile.role:
            return redirect("dashboard")
        return render(request, "accounts/role_select.html")
    
    def post(self, request):
        role = request.POST.get("role")
        if role not in ["driver", "passenger"]:
            messages.error(request, "Please select a valid role.")
            return render(request, "accounts/role_select.html")
        request.user.profile.role = role
        request.user.profile.save()
        messages.success(request, "Role selected successfully.")
        return redirect("dashboard")
