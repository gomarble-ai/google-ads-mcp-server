# Google Ads MCP Server - OAuth Setup Guide 🔐

This guide explains how to set up OAuth 2.0 authentication for the Google Ads MCP Server with automatic token management.

## 🏗️ Project Structure

```
google-ads-mcp-server/
├── server.py                    # Main MCP server with TokenManager
├── oauth/
│   ├── __init__.py             # OAuth module exports
│   └── google_auth.py          # OAuth helper functions (format_customer_id, etc.)
├── google_ads_token.json       # Auto-generated token storage (created after OAuth)
├── .env                        # Your environment variables
├── .gitignore                  # Git ignore file
├── requirements.txt            # Python dependencies
└── README.md                   # Main documentation
```

## 🔑 Prerequisites

### 1. Google Ads Developer Token

1. **Visit Google Ads API Center**
   - Go to [Google Ads Console](https://ads.google.com/)
   - Navigate to **Tools & Settings** → **Setup** → **API Center**
   - Apply for a **Developer Token**
   - ⚠️ **Note**: Approval can take 2-5 business days

2. **Token Types**
   - **Test Token**: For development (limited to test accounts)
   - **Production Token**: For live accounts (requires approval)

### 2. Google Cloud Console Setup

1. **Create/Select Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one
   - Note your **Project ID**

2. **Enable Google Ads API**
   - Navigate to **APIs & Services** → **Library**
   - Search for "Google Ads API"
   - Click **Enable**

3. **Create OAuth 2.0 Credentials**
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth 2.0 Client IDs**
   - Choose **Desktop Application**
   - Name it (e.g., "Google Ads MCP Server")
   - **Download** the JSON file or copy **Client ID** and **Client Secret**

## ⚙️ Configuration

### Environment Variables Setup

Create a `.env` file in your project root:

```bash
# Required: Google Ads API Configuration
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here

# Required: OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret_here

# Optional: Manager Account (if using MCC)
# GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

### Example `.env` File

```bash
# Google Ads Developer Token (get from Google Ads Console)
GOOGLE_ADS_DEVELOPER_TOKEN=ABcdEF1234567890

# OAuth 2.0 Credentials (get from Google Cloud Console)
GOOGLE_CLIENT_ID=987654321-abcdefghijk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-aBcDeFgHiJkLmNoPqRs

# Optional: Manager Customer ID for MCC accounts
# GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

## 🚀 OAuth Flow Walkthrough

### Automatic Authentication Process

The MCP server handles OAuth automatically using the **TokenManager** class:

```
1. User calls any tool (e.g., list_accounts)
2. TokenManager.ensure_valid_token() runs
3. Checks for google_ads_token.json file
4. If missing/expired → OAuth flow starts
5. Browser opens to Google consent screen
6. User grants permissions
7. Tokens saved locally
8. API call proceeds
```

### First-Time Setup

1. **Start the MCP Server**
   ```bash
   python3 server.py
   ```

2. **Call Any Tool** (triggers OAuth)
   ```bash
   # In Claude Desktop, ask:
   "List my Google Ads accounts"
   ```

3. **OAuth Flow Begins**
   ```
   🔐 Starting OAuth authentication...
   📋 Please complete the following steps:
   1. A browser window will open
   2. Sign in to your Google account
   3. Grant permissions for Google Ads access
   4. Return to this application

   🖥️  Starting local server to capture authorization...
   🌐 Opening browser to: https://accounts.google.com/o/oauth2/auth?...
   ⏳ Waiting for authorization...
   ```

4. **Complete in Browser**
   - Sign in to your Google account
   - Review permissions
   - Click **Allow**
   - See success message: "Authorization Successful!"

5. **Back to Server**
   ```
   ✅ Authorization code received
   🔄 Exchanging authorization code for tokens...
   ✅ OAuth flow completed successfully!
   ```

### Token Storage

After successful OAuth, a `google_ads_token.json` file is created:

```json
{
  "access_token": "ya29.a0ARrd...",
  "refresh_token": "1//04...",
  "expires_at": "2024-06-13T15:30:00.123456",
  "token_type": "Bearer"
}
```

## 🔄 Token Management

### Automatic Refresh

The system automatically handles token refresh:

```python
def ensure_valid_token(self) -> str:
    # 1. Load existing tokens
    token_data = self.load_tokens()
    
    if token_data:
        # 2. Check if current token is valid
        if self.is_token_valid(token_data):
            return token_data['access_token']  # ✅ Use existing
        
        # 3. Try to refresh token
        refresh_token = token_data.get('refresh_token')
        if refresh_token:
            new_token_data = self.refresh_access_token(refresh_token)
            if new_token_data:
                self.save_tokens(new_token_data)
                return new_token_data['access_token']  # ✅ Refreshed
    
    # 4. Need to perform OAuth flow
    if self.perform_oauth_flow():
        token_data = self.load_tokens()
        return token_data['access_token']  # ✅ New tokens
    
    raise Exception("Failed to obtain valid access token")
```

### Token Validation

Tokens are validated with a 5-minute safety buffer:

```python
def is_token_valid(self, token_data: Dict[str, Any]) -> bool:
    expires_at_str = token_data.get('expires_at')
    expires_at = datetime.fromisoformat(expires_at_str)
    # Add 5 minute buffer
    return datetime.now() < (expires_at - timedelta(minutes=5))
```

## 🛠️ Troubleshooting

### Common OAuth Issues

#### 1. "Environment variables not set"

**Error:**
```
❌ GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables!
```

**Solution:**
```bash
# Check your .env file
cat .env

# Ensure these variables are set:
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

#### 2. "OAuth flow failed"

**Error:**
```
❌ OAuth flow failed: [Various OAuth errors]
```

**Solutions:**
- Check internet connection
- Verify OAuth credentials are correct
- Ensure Google Ads API is enabled in Google Cloud Console
- Try copying OAuth URL manually if browser doesn't open

#### 3. "Token refresh failed"

**Error:**
```
❌ Token refresh failed: 400 - invalid_grant
```

**Solution:**
```bash
# Delete existing tokens and re-authenticate
rm google_ads_token.json
python3 server.py
# Complete OAuth flow again
```

#### 4. "Browser doesn't open"

**Error:**
```
🌐 Opening browser to: https://...
# But no browser opens
```

**Solution:**
```bash
# Copy the URL from console and open manually
# The URL will look like:
# https://accounts.google.com/o/oauth2/auth?client_id=...
```

### Debug Mode

Enable detailed logging:

```python
# Add to server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test OAuth Setup

```bash
# Test authentication
python3 -c "
from server import token_manager
try:
    token = token_manager.ensure_valid_token()
    print('✅ OAuth setup successful!')
except Exception as e:
    print(f'❌ OAuth setup failed: {e}')
"
```

## 🔐 OAuth Consent Screen Setup

### Required Configuration

1. **Go to Google Cloud Console**
   - Navigate to **APIs & Services** → **OAuth consent screen**

2. **Configure Consent Screen**
   - **User Type**: External (for most users)
   - **App Name**: "Google Ads MCP Server"
   - **User Support Email**: Your email
   - **Developer Contact**: Your email

3. **Scopes** (automatically handled by the server)
   - `https://www.googleapis.com/auth/adwords`

4. **Test Users** (if app is in testing mode)
   - Add your Google account email
   - Add any other users who need access

### Publishing Status

- **Testing**: Only test users can authenticate (recommended for development)
- **Published**: Anyone with a Google account can authenticate (requires verification for sensitive scopes)

## 🚀 Advanced Configuration

### Custom Redirect URI

The default redirect URI is `http://localhost:8080/oauth/callback`. To customize:

```python
# In server.py, modify TokenManager
class TokenManager:
    def __init__(self):
        self.redirect_uri = "http://localhost:9999/oauth/callback"  # Custom port
        # ... rest of initialization
```

**Update Google Cloud Console:**
- Go to **Credentials** → Your OAuth Client
- Add the new redirect URI to **Authorized redirect URIs**

### Manager Customer ID

For Manager (MCC) accounts, add to `.env`:

```bash
# Optional: Manager Customer ID for MCC accounts
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

The server will automatically use this for API calls requiring manager access.

### Custom Token Storage

```python
# Modify token file location
class TokenManager:
    def __init__(self):
        self.token_file = "/custom/path/google_ads_token.json"
        # ... rest of initialization
```

## 🔒 Security Best Practices

### File Permissions

```bash
# Set secure permissions
chmod 600 .env
chmod 600 google_ads_token.json

# Verify permissions
ls -la .env google_ads_token.json
```

### Gitignore Setup

Ensure sensitive files are ignored:

```bash
# .gitignore
.env
google_ads_token.json
*.log
__pycache__/
*.pyc
```

### Production Security

1. **Use Environment Variables**
   ```bash
   # Instead of .env file in production
   export GOOGLE_CLIENT_ID="your_client_id"
   export GOOGLE_CLIENT_SECRET="your_client_secret"
   export GOOGLE_ADS_DEVELOPER_TOKEN="your_token"
   ```

2. **Secure Token Storage**
   - Use encrypted storage systems
   - Implement token rotation policies
   - Monitor for unauthorized access

3. **Network Security**
   - Use HTTPS in production
   - Implement IP whitelisting if needed
   - Monitor authentication failures

## 📋 OAuth Checklist

Before first run, ensure:

- [ ] Google Cloud project created
- [ ] Google Ads API enabled
- [ ] OAuth 2.0 credentials created
- [ ] Google Ads Developer Token obtained
- [ ] `.env` file configured with all credentials
- [ ] OAuth consent screen configured
- [ ] Required Python dependencies installed
- [ ] Firewall allows localhost:8080 (for OAuth callback)

## 🎯 Quick Setup Script

For faster setup, you can create this helper script:

```bash
#!/bin/bash
# setup_oauth.sh

echo "🚀 Google Ads MCP Server OAuth Setup"
echo "======================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it first."
    echo "📋 Required variables:"
    echo "   GOOGLE_ADS_DEVELOPER_TOKEN"
    echo "   GOOGLE_CLIENT_ID"
    echo "   GOOGLE_CLIENT_SECRET"
    exit 1
fi

# Check environment variables
source .env

if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ OAuth credentials missing in .env file"
    exit 1
fi

if [ -z "$GOOGLE_ADS_DEVELOPER_TOKEN" ]; then
    echo "❌ Google Ads Developer Token missing in .env file"
    exit 1
fi

echo "✅ Environment variables configured"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Test OAuth setup
echo "🔐 Testing OAuth setup..."
python3 -c "
from server import token_manager
try:
    token = token_manager.ensure_valid_token()
    print('✅ OAuth setup successful!')
except Exception as e:
    print(f'❌ OAuth setup failed: {e}')
"

echo "🎉 Setup complete! You can now use the MCP server."
```

Run with:
```bash
chmod +x setup_oauth.sh
./setup_oauth.sh
```

## 📞 Support

### OAuth-Specific Issues

- **Google OAuth Documentation**: [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- **Google Ads API Auth**: [Authentication Guide](https://developers.google.com/google-ads/api/docs/oauth/overview)
- **Google Cloud Console**: [Managing OAuth Credentials](https://cloud.google.com/docs/authentication/external/oauth)

### Common Resources

- **OAuth 2.0 Playground**: [Test OAuth flows](https://developers.google.com/oauthplayground/)
- **Google Ads API Explorer**: [Test API calls](https://developers.google.com/google-ads/api/rest/explorer/)
- **Token Introspection**: [Check token validity](https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=YOUR_TOKEN)

---

**🔐 OAuth authentication is the foundation of secure Google Ads API access. Take time to set it up correctly for a smooth experience!**