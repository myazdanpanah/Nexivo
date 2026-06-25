from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_list, name="dashboard-list"),
    path("templates/", views.dashboard_templates, name="dashboard-templates"),
    path("create-from-template/", views.dashboard_create_from_template, name="dashboard-create-from-template"),
    path("<int:pk>/", views.dashboard_detail, name="dashboard-detail"),
    path("<int:pk>/layout/", views.dashboard_layout, name="dashboard-layout"),
    path("<int:pk>/filter-controls/", views.dashboard_filter_controls, name="dashboard-filter-controls"),
    path("<int:pk>/duplicate/", views.dashboard_duplicate, name="dashboard-duplicate"),
    path("<int:pk>/share/", views.dashboard_share, name="dashboard-share"),
    path("clear-all/", views.dashboard_clear_all, name="dashboard-clear-all"),
    path("audit-log/", views.audit_log_list, name="audit-log-list"),
    path("assignments/", views.assignment_list_create, name="assignment-list-create"),
    path("assignments/<int:pk>/", views.assignment_detail, name="assignment-detail"),
    path("my-assigned/", views.my_assigned_dashboards, name="my-assigned-dashboards"),
    path("<int:dashboard_pk>/pages/", views.page_create, name="page-create"),
    path("<int:dashboard_pk>/pages/reorder/", views.page_reorder, name="page-reorder"),
    path("<int:dashboard_pk>/pages/import/", views.page_import, name="page-import"),
    path("<int:dashboard_pk>/pages/<int:page_pk>/", views.page_detail, name="page-detail"),
    path("<int:dashboard_pk>/pages/<int:page_pk>/duplicate/", views.page_duplicate, name="page-duplicate"),
    path("<int:dashboard_pk>/pages/<int:page_pk>/export/", views.page_export, name="page-export"),
    path("<int:dashboard_pk>/widgets/", views.widget_create, name="widget-create"),
    path("<int:dashboard_pk>/widgets/<int:widget_pk>/", views.widget_detail, name="widget-detail"),
]
