from django.urls import path
from . import views

urlpatterns = [
    path("", views.dataset_list, name="dataset-list"),
    path("upload/", views.dataset_upload, name="dataset-upload"),
    path("<int:pk>/", views.dataset_detail, name="dataset-detail"),
    path("<int:pk>/query/", views.dataset_query, name="dataset-query"),
]
