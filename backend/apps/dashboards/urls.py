from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_list, name="dashboard-list"),
    path("<int:pk>/", views.dashboard_detail, name="dashboard-detail"),
    path("<int:pk>/layout/", views.dashboard_layout, name="dashboard-layout"),
    path("<int:dashboard_pk>/widgets/", views.widget_create, name="widget-create"),
    path("<int:dashboard_pk>/widgets/<int:widget_pk>/", views.widget_detail, name="widget-detail"),
]
