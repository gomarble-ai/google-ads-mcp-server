"""
Google Ads OAuth Authentication - cohnen's approach integrated into tool calls
"""

import os
import json
import requests
import logging
from typing import Dict, Any

# Google Auth libraries
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Constants
SCOPES = ['https://www.googleapis.com/auth/adwords']
API_VERSION = "v19"

# Environment variables
GOOGLE_ADS_OAUTH_CONFIG_PATH = os.environ.get("GOOGLE_ADS_OAUTH_CONFIG_PATH")
GOOGLE_ADS_DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
GOOGLE_ADS_CLIENT_ID = os.environ.get("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_CREDENTIALS_PATH = os.environ.get("GOOGLE_ADS_CREDENTIALS_PATH")

def format_customer_id(customer_id: str) -> str:
    """Format customer ID to ensure it's 10 digits without dashes."""
    customer_id = str(customer_id)
    customer_id = customer_id.replace('\"', '').replace('"', '')
    customer_id = ''.join(char for char in customer_id if char.isdigit())
    return customer_id.zfill(10)

def create_client_config_from_env() -> Dict[str, Any]:
    """Create OAuth client configuration from environment variables.

    This function creates a client configuration dictionary from GOOGLE_ADS_CLIENT_ID
    and GOOGLE_ADS_CLIENT_SECRET environment variables, matching the format of
    Google Cloud Console's downloaded client_secret.json file.

    Returns:
        Dict containing the OAuth client configuration

    Raises:
        ValueError: If required environment variables are missing
    """
    if not GOOGLE_ADS_CLIENT_ID or not GOOGLE_ADS_CLIENT_SECRET:
        raise ValueError(
            "GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET must be set "
            "when not using a client secret JSON file"
        )

    return {
        "installed": {
            "client_id": GOOGLE_ADS_CLIENT_ID,
            "client_secret": GOOGLE_ADS_CLIENT_SECRET,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
    }

def get_oauth_credentials():
    """Get and refresh OAuth user credentials.

    Supports two configuration methods:

    OPTION 1: Use a client_secret.json file downloaded from Google Cloud Console
        Set GOOGLE_ADS_CREDENTIALS_PATH or GOOGLE_ADS_OAUTH_CONFIG_PATH to the path
        of your client_secret JSON file.

    OPTION 2: Use environment variables
        Set GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET manually.
        Set GOOGLE_ADS_CREDENTIALS_PATH to where tokens should be saved.

    Returns:
        Credentials object for Google Ads API authentication
    """
    # Support both old and new environment variable names
    config_path = GOOGLE_ADS_CREDENTIALS_PATH or GOOGLE_ADS_OAUTH_CONFIG_PATH

    creds = None
    client_config = None
    token_path = None

    # Determine which option to use
    if config_path and os.path.exists(config_path):
        # OPTION 1: Load from existing JSON file
        logger.info(f"Loading OAuth configuration from file: {config_path}")

        try:
            with open(config_path, 'r') as f:
                file_content = json.load(f)

            # Check if this is a saved token file or a client secret file
            if 'refresh_token' in file_content or 'access_token' in file_content:
                # This is a saved token file
                logger.info("File appears to be a saved token file")
                token_path = config_path
                # We'll need client config from env vars or error
                if GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET:
                    client_config = create_client_config_from_env()
                else:
                    logger.warning("Token file exists but no client credentials available for refresh")
            else:
                # This is a client secret file
                logger.info("File appears to be a client secret file")
                client_config = file_content
                # Store tokens in the same directory
                config_dir = os.path.dirname(os.path.abspath(config_path))
                token_path = os.path.join(config_dir, 'google_ads_token.json')
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON file: {config_path}")
        except Exception as e:
            raise ValueError(f"Error reading config file {config_path}: {e}")

    elif GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET:
        # OPTION 2: Use environment variables
        logger.info("Using OAuth credentials from environment variables")
        client_config = create_client_config_from_env()

        # Determine token storage path
        if config_path:
            token_path = config_path
        else:
            # Default to current directory
            token_path = os.path.join(os.getcwd(), 'google_ads_token.json')

        logger.info(f"Tokens will be saved to: {token_path}")

    else:
        raise ValueError(
            "OAuth configuration missing. Please set either:\n"
            "  OPTION 1: GOOGLE_ADS_CREDENTIALS_PATH pointing to client_secret.json\n"
            "  OPTION 2: GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET environment variables"
        )
    
    # Load existing token if it exists
    if token_path and os.path.exists(token_path):
        try:
            logger.info(f"Loading existing OAuth token from {token_path}")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            logger.warning(f"Error loading existing token: {e}")
            creds = None

    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired OAuth token")
                creds.refresh(Request())
                logger.info("Token successfully refreshed")
            except RefreshError as e:
                logger.warning(f"Token refresh failed: {e}, will get new token")
                creds = None
            except Exception as e:
                logger.error(f"Unexpected error refreshing token: {e}")
                raise

        # Need new credentials - run OAuth flow
        if not creds:
            if not client_config:
                raise ValueError("Client configuration not available for OAuth flow")

            logger.info("Starting OAuth authentication flow")

            try:
                # Create flow from client config (either from file or env vars)
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

                # Run OAuth flow with automatic local server
                try:
                    creds = flow.run_local_server(port=0)
                    logger.info("OAuth flow completed successfully using local server")
                except Exception as e:
                    logger.warning(f"Local server failed: {e}, falling back to console")
                    creds = flow.run_console()
                    logger.info("OAuth flow completed successfully using console")

            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                raise

        # Save the credentials
        if creds and token_path:
            try:
                logger.info(f"Saving credentials to {token_path}")
                token_dir = os.path.dirname(token_path)
                if token_dir:
                    os.makedirs(token_dir, exist_ok=True)
                with open(token_path, 'w') as f:
                    f.write(creds.to_json())
                logger.info("Credentials saved successfully")
            except Exception as e:
                logger.warning(f"Could not save credentials: {e}")

    return creds

def get_headers_with_auto_token() -> Dict[str, str]:
    """Get API headers with automatically managed token - integrated OAuth."""
    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("GOOGLE_ADS_DEVELOPER_TOKEN environment variable not set")
    
    # This will automatically trigger OAuth flow if needed
    creds = get_oauth_credentials()
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Developer-Token': GOOGLE_ADS_DEVELOPER_TOKEN.strip('"').strip("'"),
        'Content-Type': 'application/json'
    }
    
    return headers

def execute_gaql(customer_id: str, query: str, manager_id: str = "") -> Dict[str, Any]:
    """Execute GAQL using the non-streaming search endpoint."""
    # This will automatically trigger OAuth if needed
    headers = get_headers_with_auto_token()
    
    formatted_customer_id = format_customer_id(customer_id)
    url = f"https://googleads.googleapis.com/{API_VERSION}/customers/{formatted_customer_id}/googleAds:search"
    
    if manager_id:
        headers['login-customer-id'] = format_customer_id(manager_id)

    payload = {'query': query}
    resp = requests.post(url, headers=headers, json=payload)
    
    if not resp.ok:
        raise Exception(f"Error executing GAQL: {resp.status_code} {resp.reason} - {resp.text}")
    
    data = resp.json()
    results = data.get('results', [])
    return {
        'results': results,
        'query': query,
        'totalRows': len(results),
    }