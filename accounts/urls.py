from django.urls import path
from .views import UserRegisterView, CustomLoginView, CustomLogoutView, DashboardView, ProfileView, RoleSelectView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("role-select/", RoleSelectView.as_view(), name="role_select"),
]