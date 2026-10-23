from django.urls import path

from . import views

urlpatterns = [
    path("api/slots/", views.slot_collection, name="slot-collection"),
    path("api/slots/status/", views.slot_status_bulk, name="slot-status-bulk"),
    path("api/slots/<int:slot_id>/", views.slot_detail, name="slot-detail"),
    path("api/slots/<int:slot_id>/status/", views.slot_status, name="slot-status"),
]
