from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/update/", views.profile_update_view, name="profile-update"),
    path("users/", views.users_list_create_view, name="users-list-create"),
    path("users/<int:pk>/", views.user_detail_view, name="user-detail"),
    # Organization management
    path("companies/", views.company_list_create, name="company-list-create"),
    path("companies/<int:pk>/", views.company_detail, name="company-detail"),
    path("divisions/", views.division_list_create, name="division-list-create"),
    path("divisions/<int:pk>/", views.division_detail, name="division-detail"),
    path("teams/", views.team_list_create, name="team-list-create"),
    path("teams/<int:pk>/", views.team_detail, name="team-detail"),
    path("org-tree/", views.org_tree, name="org-tree"),
    # Custom Role Management
    path("roles/", views.role_list_create, name="role-list-create"),
    path("roles/<int:pk>/", views.role_detail, name="role-detail"),
]
