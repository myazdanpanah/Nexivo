"""
API Standard Response Format — Enterprise ERP.

Per API_SPECIFICATION.md §6: Standard Response.
Per API_SPECIFICATION.md §7: Standard Metadata.

Every API response follows a consistent format.
"""

from rest_framework.response import Response
from rest_framework import status as http_status
from typing import Any, Dict, List, Optional


def success_response(
    data: Any = None,
    message: str = "",
    meta: Optional[Dict] = None,
    http_status_code: int = http_status.HTTP_200_OK,
) -> Response:
    """
    Standard success response.
    
    Per API_SPECIFICATION.md §6:
    {
        "success": true,
        "message": "",
        "data": {},
        "meta": {}
    }
    """
    payload = {
        "success": True,
        "message": message,
        "data": data,
        "errors": [],
    }
    if meta:
        payload["meta"] = meta
    return Response(payload, status=http_status_code)


def error_response(
    message: str = "Error",
    errors: Optional[List[Dict]] = None,
    http_status_code: int = http_status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Standard error response.
    
    Per API_SPECIFICATION.md §6:
    {
        "success": false,
        "message": "Validation Error",
        "errors": [
            {
                "field": "customer",
                "code": "required",
                "message": "Customer is required."
            }
        ]
    }
    """
    return Response({
        "success": False,
        "message": message,
        "data": None,
        "errors": errors or [],
    }, status=http_status_code)


def validation_error_response(
    message: str = "Validation Error",
    field_errors: Optional[Dict[str, str]] = None,
) -> Response:
    """
    Validation error response with field-level errors.
    
    Per API_SPECIFICATION.md §8: 400 Validation Error.
    """
    errors = []
    if field_errors:
        for field, msg in field_errors.items():
            errors.append({
                "field": field,
                "code": "invalid",
                "message": msg,
            })
    return error_response(message=message, errors=errors, http_status_code=400)


def business_rule_error(message: str) -> Response:
    """
    Business rule violation response.
    
    Per API_SPECIFICATION.md §8: 422 Business Rule Violation.
    """
    return error_response(
        message=message,
        errors=[{"code": "business_rule_violation", "message": message}],
        http_status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def not_found_response(message: str = "Resource not found") -> Response:
    """404 Not Found response."""
    return error_response(message=message, http_status_code=404)


def forbidden_response(message: str = "Permission denied") -> Response:
    """403 Forbidden response."""
    return error_response(message=message, http_status_code=403)


def paginated_response(
    data: List,
    count: int,
    page: int = 1,
    page_size: int = 25,
    ordering: str = "-created_at",
    filters: Optional[Dict] = None,
) -> Response:
    """
    Standard paginated response.
    
    Per API_SPECIFICATION.md §7: Standard Metadata.
    """
    total_pages = (count + page_size - 1) // page_size if page_size > 0 else 1
    return success_response(
        data=data,
        meta={
            "page": page,
            "page_size": page_size,
            "total": count,
            "pages": total_pages,
            "ordering": ordering,
            "filters": filters or {},
        },
    )
