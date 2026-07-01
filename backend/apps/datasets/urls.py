from django.urls import path
from . import views

urlpatterns = [
    path("", views.dataset_list, name="dataset-list"),
    path("upload/", views.dataset_upload, name="dataset-upload"),
    path("<int:pk>/", views.dataset_detail, name="dataset-detail"),
    path("<int:pk>/query/", views.dataset_query, name="dataset-query"),
    # Superset integration
    path("superset/health/", views.superset_health, name="superset-health"),
    path("superset/sync-all/", views.superset_sync_all, name="superset-sync-all"),
    path("<int:pk>/superset/sync/", views.superset_sync_dataset, name="superset-sync-dataset"),
]
