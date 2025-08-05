"""
JWT Authentication for Supabase integration

This module provides JWT token validation for FastAPI endpoints using Supabase Auth.
"""
import jwt
import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import settings

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class JWTBearer(HTTPBearer):
    """
    FastAPI dependency for validating Supabase JWT tokens.
    
    This class extends HTTPBearer to automatically extract and validate
    JWT tokens from the Authorization header.
    """
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        """
        Extract and validate JWT token from request.
        
        Returns:
            str: The validated JWT token
            
        Raises:
            HTTPException: If token is missing, invalid, or expired
        """
        logger.info(f"🔐 Authentication attempt for {request.method} {request.url.path}")
        
        # Check if Authorization header exists
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("❌ No Authorization header found in request")
            raise HTTPException(
                status_code=401, 
                detail="Authorization header missing"
            )
        
        logger.info(f"📋 Authorization header present: {auth_header[:20]}...")
        
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if not credentials:
            logger.error("❌ Failed to extract credentials from Authorization header")
            raise HTTPException(
                status_code=401, 
                detail="Authorization header missing"
            )
            
        if credentials.scheme != "Bearer":
            logger.error(f"❌ Invalid auth scheme: {credentials.scheme}, expected Bearer")
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication scheme. Expected Bearer token."
            )
            
        logger.info("🔍 Validating JWT token...")
        if not self.verify_jwt(credentials.credentials):
            logger.error("❌ JWT token validation failed")
            raise HTTPException(
                status_code=401, 
                detail="Invalid or expired token"
            )
            
        logger.info("✅ JWT token validation successful")
        return credentials.credentials

    def verify_jwt(self, token: str) -> bool:
        """
        Verify JWT token signature and expiration.
        
        Args:
            token: JWT token string
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            logger.info(f"🔍 Decoding JWT token (first 20 chars): {token[:20]}...")
            
            # Check if JWT secret is configured
            if not settings.supabase_jwt_secret:
                logger.error("❌ SUPABASE_JWT_SECRET not configured in environment")
                return False
                
            logger.info("🔑 JWT secret found, proceeding with validation")
            
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            logger.info(f"✅ JWT decoded successfully. User ID: {payload.get('sub', 'N/A')}")
            logger.info(f"📧 User email: {payload.get('email', 'N/A')}")
            logger.info(f"⏰ Token expires: {payload.get('exp', 'N/A')}")
            
            return True
        except jwt.ExpiredSignatureError:
            logger.error("❌ JWT token has expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ Invalid JWT token: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error validating JWT: {str(e)}")
            return False


def decode_jwt_token(token: str) -> dict:
    """
    Decode JWT token and return payload.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Token payload containing user information
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Token validation failed: {str(e)}"
        )


async def get_current_user_id(token: str = Depends(JWTBearer())) -> str:
    """
    Extract user ID from validated JWT token.
    
    This function replaces the insecure header-based user ID extraction
    with proper JWT validation.
    
    Args:
        token: Validated JWT token from JWTBearer dependency
        
    Returns:
        str: User ID (UUID) from token's 'sub' field
        
    Raises:
        HTTPException: If user ID is missing from token
    """
    logger.info("👤 Extracting user ID from validated JWT token")
    
    payload = decode_jwt_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        logger.error("❌ User ID (sub) field missing from JWT payload")
        raise HTTPException(
            status_code=401, 
            detail="User ID missing from token"
        )
    
    logger.info(f"✅ User ID extracted: {user_id}")
    return user_id


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Extract user ID from JWT token, returns None if no token provided.
    
    This is useful for endpoints that can work with or without authentication.
    
    Args:
        credentials: Optional HTTP credentials
        
    Returns:
        Optional[str]: User ID if valid token provided, None otherwise
    """
    if not credentials or credentials.scheme != "Bearer":
        return None
        
    try:
        payload = decode_jwt_token(credentials.credentials)
        return payload.get("sub")
    except HTTPException:
        return None


async def get_user_email(token: str = Depends(JWTBearer())) -> Optional[str]:
    """
    Extract user email from validated JWT token.
    
    Args:
        token: Validated JWT token from JWTBearer dependency
        
    Returns:
        Optional[str]: User email from token, if available
    """
    payload = decode_jwt_token(token)
    return payload.get("email")





# Legacy compatibility - for gradual migration
jwt_bearer = JWTBearer()