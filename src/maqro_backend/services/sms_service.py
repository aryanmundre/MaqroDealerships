"""
Vonage SMS Service for sending and handling SMS messages
"""
import httpx
from typing import Dict, Any
from ..core.config import settings
from ..utils.phone_utils import normalize_phone_number
import logging

logger = logging.getLogger(__name__)


class VonageSMSService:
    """Service for handling Vonage SMS operations"""
    
    def __init__(self):
        self.api_key = settings.vonage_api_key
        self.api_secret = settings.vonage_api_secret
        self.phone_number = settings.vonage_phone_number
        self.base_url = "https://rest.nexmo.com"
    
    def _validate_credentials(self) -> bool:
        """Validate that all required Vonage credentials are available"""
        return all([self.api_key, self.api_secret, self.phone_number])
    
    async def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send SMS via Vonage API
        
        Args:
            to: Recipient phone number
            message: SMS message text
            
        Returns:
            Dict with success status and message ID or error
        """
        if not self._validate_credentials():
            logger.error("Vonage credentials not configured")
            return {"success": False, "error": "Vonage credentials not configured"}
        
        # Prepare request data
        data = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "to": to,
            "from": self.phone_number,
            "text": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sms/json",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Vonage API error: {response.status_code} - {response.text}")
                    return {"success": False, "error": "Failed to send SMS"}
                
                result = response.json()
                logger.info(f"Vonage response: {result}")
                
                # Check if message was sent successfully
                if result.get("messages") and len(result["messages"]) > 0:
                    message_data = result["messages"][0]
                    if message_data.get("status") == "0":
                        return {
                            "success": True,
                            "message_id": message_data.get("message-id"),
                            "to": to,
                            "from": self.phone_number
                        }
                    else:
                        error_text = message_data.get("error-text", "Unknown error")
                        logger.error(f"Vonage message error: {error_text}")
                        return {"success": False, "error": error_text}
                else:
                    return {"success": False, "error": "Invalid response from Vonage"}
                    
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            return {"success": False, "error": "Network error"}
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return {"success": False, "error": "Internal error"}
    
    def validate_webhook_signature(self, params: Dict[str, str], signature: str) -> bool:
        """
        Validate Vonage webhook signature for security
        Note: Implement this based on Vonage webhook security requirements
        """
        # For now, return True - implement signature validation as needed
        logger.info("Webhook signature validation - implement as needed")
        return True
    
    def normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number using centralized utility.
        
        Args:
            phone: Raw phone number from webhook
            
        Returns:
            Normalized phone number or empty string if invalid
        """
        normalized = normalize_phone_number(phone)
        return normalized if normalized else ""


# Global instance
sms_service = VonageSMSService()