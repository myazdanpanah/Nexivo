"""
Middleware to inject role context for PostgreSQL Row-Level Security.
Sets session variables that PostgreSQL RLS policies can use.
"""


class RoleMiddleware:
    """
    Sets PostgreSQL session variables based on the authenticated user's role.
    This enables PostgreSQL RLS policies to filter data automatically
    without modifying the original data.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, "user") and request.user.is_authenticated:
            # Store role info on request for use in queries
            request.user_role = request.user.role
            request.user_department = getattr(request.user, "department", "")
