# Plugin OAuth Configuration Guide

This guide explains how to configure OAuth for plugin integrations with two approaches:
1. **Centralized OAuth** (Recommended) - Frictionless for users
2. **User-Provided OAuth** - Advanced users who want their own app

---

## 🚀 Approach 1: Centralized OAuth (Recommended)

### Benefits
✅ Users click "Connect" and authorize - that's it!
✅ No technical knowledge required
✅ Higher conversion rates
✅ Professional integration experience
✅ You control the branding

### Setup Steps

You create ONE app per platform and configure credentials via environment variables.

#### 1. Google Ads Setup

**Create App:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "MoldCRM Integration"
3. Enable Google Ads API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Authorized redirect URIs:
   ```
   https://your-domain.com/api/plugins/{id}/oauth-callback/
   https://your-railway-domain.railway.app/api/plugins/{id}/oauth-callback/
   ```
7. Copy Client ID and Client Secret

**Set Environment Variables (Railway):**
```bash
GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
```

**Additional Requirements:**
- Apply for [Google Ads Developer Token](https://developers.google.com/google-ads/api/docs/get-started/dev-token)
- Users will need to provide their Customer ID in the config

---

#### 2. Meta Ads (Facebook & Instagram) Setup

**Create App:**
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create new app → "Business" type
3. Add "Marketing API" product
4. Settings → Basic:
   - App Name: "MoldCRM"
   - Privacy Policy URL
   - Terms of Service URL
5. Add redirect URIs in OAuth Settings:
   ```
   https://your-domain.com/api/plugins/{id}/oauth-callback/
   ```
6. Request permissions:
   - `ads_management`
   - `ads_read`
   - `business_management`
   - `leads_retrieval`
7. Copy App ID and App Secret

**Set Environment Variables (Railway):**
```bash
META_ADS_CLIENT_ID=your_app_id
META_ADS_CLIENT_SECRET=your_app_secret
```

**Note:** App must go through Meta App Review to access production data.

---

#### 3. TikTok Ads Setup

**Create App:**
1. Go to [TikTok Marketing API](https://business-api.tiktok.com/)
2. Register as a developer
3. Create new app: "MoldCRM Integration"
4. Add redirect URIs:
   ```
   https://your-domain.com/api/plugins/{id}/oauth-callback/
   ```
5. Copy App ID and App Secret

**Set Environment Variables (Railway):**
```bash
TIKTOK_ADS_CLIENT_ID=your_app_id
TIKTOK_ADS_CLIENT_SECRET=your_secret
```

---

#### 4. Shopify Setup

**Create App:**
1. Go to [Shopify Partners](https://partners.shopify.com/)
2. Create account if needed
3. Apps → Create app → Custom app
4. App setup:
   - App name: "MoldCRM"
   - App URL: `https://your-domain.com`
   - Allowed redirection URL(s):
     ```
     https://your-domain.com/api/plugins/{id}/oauth-callback/
     ```
5. Configure scopes:
   - `read_orders`
   - `read_customers`
   - `read_products`
6. Copy API key (Client ID) and API secret key

**Set Environment Variables (Railway):**
```bash
SHOPIFY_CLIENT_ID=your_api_key
SHOPIFY_CLIENT_SECRET=your_api_secret_key
```

---

### Deploying Centralized Credentials

**On Railway:**
1. Go to your project settings
2. Variables tab
3. Add all environment variables listed above
4. Deploy

**Verify Configuration:**
```bash
# Check which platforms have centralized auth
curl https://your-api.com/api/plugins/available-platforms/ \
  -H "Authorization: Token your-auth-token"

# Response shows centralized_auth: true for configured platforms
[
  {
    "plugin_type": "google_ads",
    "display_name": "Google Ads",
    "category": "advertising",
    "centralized_auth": true,
    "requires_user_credentials": false
  },
  ...
]
```

---

## 🔧 Approach 2: User-Provided OAuth

### When to Use
- Advanced users who want full control
- Enterprise customers with their own apps
- Testing/development

### User Flow

**1. User Creates Their Own App**
Each user must create an app in the platform's developer console and get credentials.

**2. User Provides Credentials via API**
```bash
POST /api/plugins/
{
  "plugin_type": "google_ads",
  "name": "My Google Ads Account",
  "client_id": "user_provided_client_id",
  "client_secret": "user_provided_client_secret",
  "config": {
    "customer_id": "1234567890"
  }
}
```

**3. User Completes OAuth Flow**
Same as centralized, but uses their app credentials.

---

## 🔀 Hybrid Approach (Best of Both)

You can support BOTH approaches simultaneously!

**How it Works:**
1. If centralized credentials exist → Use them (frictionless)
2. If user provides credentials → Use theirs (advanced mode)

**Implementation:**
Already built in! The system checks environment variables first, falls back to user credentials.

**Frontend Display:**
```javascript
// Check if user needs to provide credentials
fetch('/api/plugins/available-platforms/')
  .then(r => r.json())
  .then(platforms => {
    platforms.forEach(platform => {
      if (platform.centralized_auth) {
        // Show simple "Connect" button
        showConnectButton(platform);
      } else {
        // Show form to enter credentials
        showCredentialForm(platform);
      }
    });
  });
```

---

## 📱 User Experience Comparison

### With Centralized OAuth (Recommended)
```
1. User clicks "Connect Google Ads"
2. Redirects to Google
3. User authorizes "MoldCRM"
4. Redirects back → Connected! ✅
```

### With User-Provided OAuth
```
1. User goes to Google Cloud Console
2. Creates new project
3. Enables APIs
4. Creates OAuth credentials
5. Copies client ID and secret
6. Pastes into MoldCRM
7. Clicks "Connect Google Ads"
8. Redirects to Google
9. User authorizes their own app
10. Redirects back → Connected ✅
```

**Conclusion:** Centralized is 6 fewer steps! 🚀

---

## 🔐 Security Considerations

### Centralized Credentials
- Store in environment variables (Railway Secrets)
- Never commit to git
- Rotate periodically
- Use different credentials per environment (dev/staging/prod)

### Access Tokens
- ALWAYS stored per-user in database
- Encrypted at rest
- Cannot be shared between users
- Each user authorizes independently

---

## 🎯 Recommended Configuration

**For Production SaaS:**
```bash
# Set these on Railway for frictionless UX
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
META_ADS_CLIENT_ID=...
META_ADS_CLIENT_SECRET=...
TIKTOK_ADS_CLIENT_ID=...
TIKTOK_ADS_CLIENT_SECRET=...
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=...
```

**For Enterprise/Advanced Users:**
Don't set environment variables. Each customer provides their own credentials.

---

## 🧪 Testing

**Test Centralized Setup:**
```bash
# 1. Create plugin without credentials
curl -X POST https://your-api.com/api/plugins/ \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_type": "shopify",
    "name": "My Store",
    "config": {"shop_domain": "mystore.myshopify.com"}
  }'
# Note: No client_id/client_secret required!

# 2. Get OAuth URL
curl https://your-api.com/api/plugins/1/oauth-url/ \
  -H "Authorization: Token your-token"

# 3. Should return OAuth URL using centralized credentials
```

---

## 📊 Migration Path

**Already have user-provided credentials?**

No problem! The system will:
1. Check environment variables first
2. Fall back to database credentials if env vars not set
3. Work seamlessly with existing plugins

**To migrate to centralized:**
1. Set environment variables
2. System automatically uses them for new plugins
3. Existing plugins continue working with their credentials
4. Optional: Clear old credentials from database (keep tokens!)

---

## 🆘 Troubleshooting

**"OAuth credentials required" error:**
- Check environment variables are set
- Verify variable names match exactly
- Restart Railway service after setting variables

**"Invalid redirect URI" error:**
- Make sure redirect URI in platform matches exactly
- Include both http://localhost (dev) and https://production URLs
- No trailing slashes

**"Scope not granted" error:**
- Request additional permissions in platform settings
- Some platforms require app review for production access

---

## 📚 References

- [Google Ads API OAuth](https://developers.google.com/google-ads/api/docs/oauth/overview)
- [Meta Marketing API](https://developers.facebook.com/docs/marketing-apis)
- [TikTok Marketing API](https://business-api.tiktok.com/portal/docs)
- [Shopify OAuth](https://shopify.dev/docs/apps/auth/oauth)
