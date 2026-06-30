from django.urls import path
from . import views

urlpatterns = [
    # Database Management
    path("databases/", views.database_list, name="db-list"),
    path("databases/<int:pk>/", views.database_detail, name="db-detail"),
    path("databases/<int:pk>/test/", views.database_test, name="db-test"),

    # Table Operations
    path("databases/<str:source>/tables/", views.table_list, name="table-list"),
    path("tables/<str:source>/<str:table>/schema/", views.table_schema, name="table-schema"),
    path("tables/<str:source>/<str:table>/data/", views.table_data, name="table-data"),
    path("tables/<str:source>/<str:table>/count/", views.table_count, name="table-count"),

    # Cell Editing
    path("tables/<str:source>/<str:table>/cell/", views.cell_update, name="cell-update"),
    path("tables/<str:source>/<str:table>/batch/", views.batch_update, name="batch-update"),
    path("tables/<str:source>/<str:table>/rows/", views.row_insert, name="row-insert"),
    path("tables/<str:source>/<str:table>/rows/delete/", views.row_delete, name="row-delete"),

    # Schema Editing
    path("tables/<str:source>/<str:table>/columns/", views.column_add, name="column-add"),
    path("tables/<str:source>/<str:table>/columns/<str:column_name>/", views.column_update, name="column-update"),
    path("tables/<str:source>/<str:table>/columns/<str:column_name>/drop/", views.column_drop, name="column-drop"),

    # File Import
    path("tables/<str:source>/<str:table>/import/", views.file_import, name="file-import"),
    path("import/new/", views.file_import_new, name="file-import-new"),

    # SQL Editor
    path("sql/", views.sql_execute, name="sql-execute"),

    # Google Sheets Sync
    path("syncs/", views.sync_list, name="sync-list"),
    path("syncs/<int:pk>/", views.sync_detail, name="sync-detail"),
    path("syncs/<int:pk>/run/", views.sync_run, name="sync-run"),

    # Permissions Management
    path("permissions/", views.permission_list_create, name="permission-list"),
    path("permissions/<int:pk>/", views.permission_detail, name="permission-detail"),
]
