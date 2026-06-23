from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_list, name="dashboard-list"),
    path("templates/", views.dashboard_templates, name="dashboard-templates"),
    path("create-from-template/", views.dashboard_create_from_template, name="dashboard-create-from-template"),
    path("<int:pk>/", views.dashboard_detail, name="dashboard-detail"),
    path("<int:pk>/layout/", views.dashboard_layout, name="dashboard-layout"),
    path("<int:pk>/filter-controls/", views.dashboard_filter_controls, name="dashboard-filter-controls"),
    path("<int:dashboard_pk>/pages/", views.page_create, name="page-create"),
    path("<int:dashboard_pk>/pages/reorder/", views.page_reorder, name="page-reorder"),
    path("<int:dashboard_pk>/pages/import/", views.page_import, name="page-import"),
    path("<int:dashboard_pk>/pages/<int:page_pk>/", views.page_detail, name="page-detail"),
    path("<int:dashboard_pk>/pages/<int:page_pk>/duplicate/", views.page_duplicate, name="page-duplicate"),
    path("<int:dashboard_pk>/pages/<int:page_pk>/export/", views.page_export, name="page-export"),
    path("<int:dashboard_pk>/widgets/", views.widget_create, name="widget-create"),
    path("<int:dashboard_pk>/widgets/<int:widget_pk>/", views.widget_detail, name="widget-detail"),
]
