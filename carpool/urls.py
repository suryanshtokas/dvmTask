from django.urls import path
from .views import (
    CarpoolRequestCreateView,
    CarpoolRequestListView,
    CarpoolRequestDetailView,
    CarpoolOfferSelectView, 
    CarpoolRequestCancelView,
    DriverCarpoolRequestListView,
    CarpoolOfferCreateView,
    CarpoolRequestListAPI,
)

urlpatterns = [
    path("request/", CarpoolRequestCreateView.as_view(), name="carpool_request_create"),
    path("request/list/", CarpoolRequestListView.as_view(), name="carpool_request_list"),
    path("request/<int:pk>/", CarpoolRequestDetailView.as_view(), name="carpool_request_detail"),
    path("request/<int:pk>/cancel/", CarpoolRequestCancelView.as_view(), name="carpool_request_cancel"),
    path("offer/<int:pk>/select/", CarpoolOfferSelectView.as_view(), name="carpool_offer_select"),

    path("trip/<int:trip_pk>/requests/", DriverCarpoolRequestListView.as_view(), name="driver_carpool_request_list"),
    path("trip/<int:trip_pk>/requests/<int:request_pk>/offer/", CarpoolOfferCreateView.as_view(), name="carpool_offer_create"),

    path("api/trip/<int:trip_pk>/requests/", CarpoolRequestListAPI.as_view(), name="carpool_request_api"),
]