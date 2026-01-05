"""
Azure Entra ID (Azure AD) Zero-Trust Integration
Authentication and authorization with conditional access
"""
import os
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from datetime import datetime, timedelta
from functools import wraps

security = HTTPBearer()

class EntraIDAuth:
    """
    Azure Entra ID authentication and authorization
    """
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        self.jwks_uri = f"{self.authority}/discovery/v2.0/keys"
        self.issuer = f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
        
        self.required_roles = {
            "admin": ["VeriShield.Admin"],
            "analyst": ["VeriShield.Analyst", "VeriShield.Admin"],
            "viewer": ["VeriShield.Viewer", "VeriShield.Analyst", "VeriShield.Admin"]
        }
    
    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> Dict[str, Any]:
        """
        Verify JWT token from Azure Entra ID
        """
        token = credentials.credentials
        
        try:
            # Get signing keys
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri)
                jwks = response.json()
            
            # Decode token header to get kid
            unverified_header = jwt.get_unverified_header(token)
            
            # Find matching key
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            
            if not rsa_key:
                raise HTTPException(
                    status_code=401,
                    detail="Unable to find appropriate key"
                )
            
            # Verify token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer
            )
            
            return {
                "user_id": payload.get("oid"),
                "email": payload.get("preferred_username"),
                "name": payload.get("name"),
                "roles": payload.get("roles", []),
                "tenant_id": payload.get("tid")
            }
            
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Token validation failed: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Authentication error: {str(e)}"
            )
    
    def require_role(self, required_role: str):
        """
        Decorator to require specific role
        """
        async def role_checker(
            user: Dict[str, Any] = Depends(self.verify_token)
        ) -> Dict[str, Any]:
            user_roles = user.get("roles", [])
            allowed_roles = self.required_roles.get(required_role, [])
            
            if not any(role in user_roles for role in allowed_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required role: {required_role}"
                )
            
            return user
        
        return role_checker
    
    async def get_access_token(self) -> str:
        """
        Get application access token using client credentials
        """
        token_url = f"{self.authority}/oauth2/v2.0/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            token_data = response.json()
            
            return token_data.get("access_token")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Microsoft Graph
        """
        access_token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(
                f"https://graph.microsoft.com/v1.0/users/{user_id}",
                headers=headers
            )
            
            return response.json()
    
    async def check_conditional_access(
        self,
        user: Dict[str, Any],
        ip_address: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate conditional access policies
        """
        policies = {
            "ip_allowed": self._check_ip_whitelist(ip_address),
            "device_compliant": self._check_device_compliance(device_info),
            "mfa_required": True,
            "risk_level": self._calculate_risk_level(user, ip_address)
        }
        
        access_granted = all([
            policies["ip_allowed"],
            policies["device_compliant"]
        ])
        
        return {
            "access_granted": access_granted,
            "policies_evaluated": policies,
            "user_id": user.get("user_id"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_ip_whitelist(self, ip_address: str) -> bool:
        """Check if IP is in whitelist"""
        # Implement IP whitelist logic
        return True
    
    def _check_device_compliance(
        self,
        device_info: Optional[Dict[str, Any]]
    ) -> bool:
        """Check device compliance status"""
        # Implement device compliance check
        return True
    
    def _calculate_risk_level(
        self,
        user: Dict[str, Any],
        ip_address: str
    ) -> str:
        """Calculate authentication risk level"""
        # Implement risk calculation
        return "low"

# Create global instance
entra_auth = EntraIDAuth()

# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    return await entra_auth.verify_token(credentials)
