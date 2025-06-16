"""
OAuth module for Google Ads authentication - cohnen's approach.
"""

from .google_auth import (
    format_customer_id,
    get_headers_with_auto_token,
    execute_gaql,
    get_oauth_credentials
)

__all__ = [
    'format_customer_id',
    'get_headers_with_auto_token', 
    'execute_gaql',
    'get_oauth_credentials'
]

# Version information
__version__ = "2.0.0"
__author__ = "Google Ads MCP Server Contributors"
__description__ = "OAuth 2.0 authentication module for Google Ads API"