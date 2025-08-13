# API Authentication Strategies

This document outlines the different authentication methods for various types of API access.

## Authentication Hierarchy

### 1. Internal Service Authentication

**Who**: Your Flask app, background jobs, internal services  
**Purpose**: Trusted components of your application ecosystem  
**Implementation**: Shared service key

```python
from ichrisbirch.api.client import internal_service_client

# Your Flask app calling your API
client = internal_service_client("flask-frontend")
users = client.resource('users', UserModel)
user = users.list(username="john_doe")[0]  # Check username for login
```

### 2. Developer API Keys

**Who**: External developers building their own frontends  
**Purpose**: Third-party application access with controlled permissions  
**Implementation**: Individual API keys with scoping

```python
# Custom provider for external developers
class DeveloperAPIKeyProvider(CredentialProvider):
    def __init__(self, api_key: str, app_name: str = "external-app"):
        self.api_key = api_key
        self.app_name = app_name

    def get_credentials(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-App-Name": self.app_name
        }

    def is_available(self) -> bool:
        return bool(self.api_key)

# External developer usage
client = APIClient(credential_provider=DeveloperAPIKeyProvider("dev_abc123"))
```

### 3. User Token Authentication

**Who**: End users of external applications  
**Purpose**: User-scoped access through external frontends  
**Implementation**: OAuth 2.0 or JWT tokens

```python
# For user-specific operations
class UserBearerTokenProvider(CredentialProvider):
    def __init__(self, user_token: str):
        self.user_token = user_token

    def get_credentials(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.user_token}"}

    def is_available(self) -> bool:
        return bool(self.user_token)

# External app on behalf of user
client = APIClient(credential_provider=UserBearerTokenProvider("user_jwt_token"))
```

## API Access Scenarios

### Scenario 1: Your Flask App (Current)

```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Check credentials via API
    with internal_service_client("flask-frontend") as client:
        users = client.resource('users', UserModel)

        # Find user by username
        user_list = users.list(username=username)
        if not user_list:
            return "Invalid username", 401

        user = user_list[0]

        # Verify password via API action
        auth_result = users.action('verify_password', {
            'user_id': user.id,
            'password': password
        })

        if auth_result['valid']:
            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            return "Invalid password", 401
```

### Scenario 2: External Developer Building Mobile App

```python
# Mobile app developer gets API key: "dev_mobile_app_xyz789"
# They build a React Native app

// In their mobile app
const apiKey = "dev_mobile_app_xyz789";

// Login endpoint for their users
async function loginUser(username, password) {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });

    if (response.ok) {
        const { user_token } = await response.json();
        // Store user token for subsequent requests
        return user_token;
    }
}

// Accessing user data
async function getUserTasks(userToken) {
    const response = await fetch('/api/tasks', {
        headers: {
            'Authorization': `Bearer ${userToken}`,
            'X-API-Key': apiKey
        }
    });
    return response.json();
}
```

### Scenario 3: External Web App Developer

```python
# Python web developer gets API key: "dev_web_portal_abc456"
# They build a Django app that integrates with your API

from your_api_client import APIClient, DeveloperAPIKeyProvider, UserBearerTokenProvider

class ExternalTaskService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        provider = DeveloperAPIKeyProvider(self.api_key, "external-web-app")

        with APIClient(credential_provider=provider) as client:
            auth = client.resource('auth', AuthModel)
            result = auth.action('login', {
                'username': username,
                'password': password
            })

            return result.get('token') if result['success'] else None

    def get_user_tasks(self, user_token: str) -> List[dict]:
        """Get tasks for authenticated user"""
        user_provider = UserBearerTokenProvider(user_token)

        with APIClient(credential_provider=user_provider) as client:
            tasks = client.resource('tasks', TaskModel)
            return tasks.list()
```

## Backend API Implementation

You'd need to add authentication middleware to your FastAPI backend:

```python
# In your FastAPI app
from fastapi import HTTPException, Depends, Header
from typing import Optional

async def get_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """Extract API key from headers"""
    return x_api_key

async def get_user_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user token from Authorization header"""
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]  # Remove "Bearer " prefix
    return None

async def get_internal_service(x_internal_service: Optional[str] = Header(None)) -> Optional[str]:
    """Extract internal service auth"""
    return x_internal_service

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Authentication middleware to validate requests"""

    # Internal service requests
    if request.headers.get("X-Internal-Service"):
        # Validate service key
        service_key = request.headers.get("Authorization", "").replace("Service ", "")
        if not validate_service_key(service_key):
            raise HTTPException(401, "Invalid service key")

    # Developer API key requests
    elif request.headers.get("X-API-Key"):
        api_key = request.headers.get("X-API-Key")
        if not validate_developer_key(api_key):
            raise HTTPException(401, "Invalid API key")

    # User token requests
    elif request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers.get("Authorization")[7:]
        if not validate_user_token(token):
            raise HTTPException(401, "Invalid user token")

    else:
        raise HTTPException(401, "Authentication required")

    response = await call_next(request)
    return response
```

## Developer Onboarding Process

### For External Developers

1. **Registration**: Developer signs up on your developer portal
2. **API Key Generation**: System generates unique API key
3. **Documentation**: Provide API docs and client library
4. **Rate Limiting**: Apply limits based on their plan
5. **Monitoring**: Track usage and provide analytics

```python
# Developer management endpoints
@router.post("/developer/register")
async def register_developer(developer_info: DeveloperRegistration):
    """Register new developer and generate API key"""
    api_key = generate_api_key()

    # Store in database
    dev_record = DeveloperAccount(
        name=developer_info.name,
        email=developer_info.email,
        api_key=api_key,
        rate_limit=1000,  # requests per hour
        scopes=["read:tasks", "read:users"]  # limited permissions
    )

    return {"api_key": api_key, "documentation": "/docs/api"}

@router.get("/developer/usage")
async def get_usage_stats(api_key: str = Depends(get_api_key)):
    """Get API usage statistics for developer"""
    return get_developer_usage(api_key)
```

## Summary

- **Internal Service Auth**: Your Flask app and internal services (current implementation)
- **Developer API Keys**: External developers building applications
- **User Tokens**: End users of those external applications

The key insight is that you have **three layers of authentication**:

1. **Service-level** (your internal components)
2. **Application-level** (external developers)  
3. **User-level** (end users through external apps)

Would you like me to help implement any of these authentication providers or show you how to set up the developer registration system?
