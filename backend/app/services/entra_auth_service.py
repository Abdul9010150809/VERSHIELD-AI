"""
Entra ID Zero-Trust Integration Service
Microsoft Entra ID authentication with zero-trust security
"""

from typing import Dict, List, Any, Optional
import jwt
import requests
import time
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import base64

class EntraAuthService:
    """
    Microsoft Entra ID integration for zero-trust authentication
    """

    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")

        # Entra ID endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
        self.jwks_endpoint = f"{self.authority}/discovery/v2.0/keys"
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"

        # Token cache
        self.token_cache = {}

        # JWKS cache
        self.jwks_cache = None
        self.jwks_cache_time = 0

    def get_authorization_url(self, redirect_uri: str, state: str = None,
                             scope: str = "openid profile email") -> Dict[str, Any]:
        """
        Generate authorization URL for OAuth2 flow

        Args:
            redirect_uri: OAuth redirect URI
            state: State parameter for CSRF protection
            scope: Requested scopes

        Returns:
            {"auth_url": url, "state": state, "nonce": nonce}
        """
        if not state:
            state = secrets.token_urlsafe(32)

        nonce = secrets.token_urlsafe(16)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "nonce": nonce,
            "response_mode": "query"
        }

        auth_url = f"{self.authority}/oauth2/v2.0/authorize"

        query_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])

        return {
            "auth_url": f"{auth_url}?{query_string}",
            "state": state,
            "nonce": nonce
        }

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used in auth request

        Returns:
            Token response with access_token, id_token, etc.
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(self.token_endpoint, data=data, headers=headers)
            response.raise_for_status()

            token_data = response.json()

            # Validate and decode ID token
            if "id_token" in token_data:
                decoded_id_token = self._validate_id_token(token_data["id_token"])
                token_data["decoded_id_token"] = decoded_id_token

            # Cache access token
            if "access_token" in token_data:
                self.token_cache[token_data["access_token"]] = {
                    "expires_at": time.time() + token_data.get("expires_in", 3600),
                    "token_data": token_data
                }

            return {
                "success": True,
                "tokens": token_data
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Token exchange failed: {str(e)}"
            }

    def validate_access_token(self, access_token: str) -> Dict[str, Any]:
        """
        Validate access token and extract claims

        Args:
            access_token: JWT access token

        Returns:
            {"valid": bool, "claims": dict, "user_info": dict}
        """
        try:
            # Check cache first
            if access_token in self.token_cache:
                cached = self.token_cache[access_token]
                if time.time() < cached["expires_at"]:
                    return {
                        "valid": True,
                        "claims": self._decode_jwt(access_token),
                        "cached": True
                    }
                else:
                    # Remove expired token
                    del self.token_cache[access_token]

            # Decode and validate JWT
            header = jwt.get_unverified_header(access_token)
            claims = jwt.decode(access_token, options={"verify_signature": False})

            # Verify signature using JWKS
            if not self._verify_token_signature(access_token, header):
                return {"valid": False, "error": "Invalid token signature"}

            # Check expiration
            if claims.get("exp", 0) < time.time():
                return {"valid": False, "error": "Token expired"}

            # Check issuer
            expected_issuer = f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
            if claims.get("iss") != expected_issuer:
                return {"valid": False, "error": "Invalid issuer"}

            # Check audience
            if self.client_id not in claims.get("aud", []):
                return {"valid": False, "error": "Invalid audience"}

            # Get user info from Graph API
            user_info = self._get_user_info(access_token)

            return {
                "valid": True,
                "claims": claims,
                "user_info": user_info
            }

        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    def _validate_id_token(self, id_token: str) -> Dict[str, Any]:
        """Validate ID token"""
        try:
            header = jwt.get_unverified_header(id_token)
            claims = jwt.decode(id_token, options={"verify_signature": False})

            # Verify signature
            if not self._verify_token_signature(id_token, header):
                raise ValueError("Invalid ID token signature")

            # Check claims
            if claims.get("iss") != f"https://login.microsoftonline.com/{self.tenant_id}/v2.0":
                raise ValueError("Invalid issuer")

            if self.client_id not in claims.get("aud", []):
                raise ValueError("Invalid audience")

            if claims.get("exp", 0) < time.time():
                raise ValueError("ID token expired")

            return claims

        except Exception as e:
            raise ValueError(f"ID token validation failed: {str(e)}")

    def _verify_token_signature(self, token: str, header: Dict[str, Any]) -> bool:
        """Verify JWT signature using JWKS"""
        try:
            # Get JWKS
            jwks = self._get_jwks()

            # Get key
            kid = header.get("kid")
            if not kid:
                return False

            key = None
            for jwk_key in jwks.get("keys", []):
                if jwk_key.get("kid") == kid:
                    key = jwk_key
                    break

            if not key:
                return False

            # Convert JWK to PEM
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

            # Verify signature
            jwt.decode(token, public_key, algorithms=["RS256"])

            return True

        except Exception:
            return False

    def _get_jwks(self) -> Dict[str, Any]:
        """Get JWKS from Microsoft"""
        # Cache JWKS for 24 hours
        if self.jwks_cache and (time.time() - self.jwks_cache_time) < 86400:
            return self.jwks_cache

        try:
            response = requests.get(self.jwks_endpoint)
            response.raise_for_status()
            self.jwks_cache = response.json()
            self.jwks_cache_time = time.time()
            return self.jwks_cache
        except Exception as e:
            raise ValueError(f"Failed to get JWKS: {str(e)}")

    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        """Decode JWT without verification"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except:
            return {}

    def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{self.graph_endpoint}/me", headers=headers)
            response.raise_for_status()
            return response.json()
        except:
            return {}

    def get_app_token(self) -> Optional[str]:
        """
        Get application token for service-to-service calls

        Returns:
            Access token or None
        """
        # Check cache
        cache_key = f"app_token_{self.client_id}"
        if cache_key in self.token_cache:
            cached = self.token_cache[cache_key]
            if time.time() < cached["expires_at"]:
                return cached["token_data"]["access_token"]

        # Get new token
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default"
        }

        try:
            response = requests.post(self.token_endpoint, data=data)
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get("access_token")

            if access_token:
                self.token_cache[cache_key] = {
                    "expires_at": time.time() + token_data.get("expires_in", 3600),
                    "token_data": token_data
                }

            return access_token

        except Exception as e:
            print(f"Failed to get app token: {e}")
            return None

    def check_user_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if user has permission for resource/action

        Args:
            user_id: User ID from token
            resource: Resource being accessed
            action: Action being performed

        Returns:
            True if authorized
        """
        # This would integrate with Azure AD roles/groups
        # Simplified implementation
        return True  # Placeholder

    def create_conditional_access_policy(self, policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create conditional access policy (requires admin consent)

        Args:
            policy_config: Policy configuration

        Returns:
            Policy creation result
        """
        app_token = self.get_app_token()
        if not app_token:
            return {"success": False, "error": "No app token available"}

        # This would use Microsoft Graph API to create policies
        # Placeholder implementation
        return {
            "success": True,
            "policy_id": "placeholder_policy_id",
            "message": "Policy creation not implemented"
        }


# Example usage
if __name__ == "__main__":
    auth_service = EntraAuthService()

    # Get authorization URL
    auth_info = auth_service.get_authorization_url(
        redirect_uri="http://localhost:3000/auth/callback"
    )
    print(f"Authorization URL: {auth_info['auth_url']}")

    # In real flow:
    # 1. User visits auth URL
    # 2. User authenticates and gets redirected with code
    # 3. Exchange code for tokens
    # token_result = auth_service.exchange_code_for_token(code, redirect_uri)
    # 4. Validate tokens for subsequent requests
    # validation = auth_service.validate_access_token(access_token)