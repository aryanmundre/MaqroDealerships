"""
WhatsApp Business API Service for sending and handling WhatsApp messages
"""
import httpx
import hmac
import hashlib
from typing import Dict, Any, Optional
from ..core.config import settings
from ..utils.phone_utils import normalize_phone_number
import logging
import json

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for handling WhatsApp Business API operations"""
    
    def __init__(self):
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.webhook_verify_token = settings.whatsapp_webhook_verify_token
        self.app_secret = settings.whatsapp_app_secret
        self.api_version = settings.whatsapp_api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    def _validate_credentials(self) -> bool:
        """Validate that all required WhatsApp credentials are available"""
        return all([
            self.access_token, 
            self.phone_number_id, 
            self.webhook_verify_token,
            self.app_secret
        ])
    
    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send message via WhatsApp Business API
        
        Args:
            to: Recipient phone number (in international format without +)
            message: Message text
            
        Returns:
            Dict with success status and message ID or error
        """
        if not self._validate_credentials():
            logger.error("WhatsApp credentials not configured")
            return {"success": False, "error": "WhatsApp credentials not configured"}
        
        # Prepare request payload for WhatsApp API
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                    return {
                        "success": False, 
                        "error": f"API error: {response.status_code}",
                        "details": response.text
                    }
                
                result = response.json()
                logger.info(f"WhatsApp response: {result}")
                
                # Check if message was sent successfully
                if result.get("messages") and len(result["messages"]) > 0:
                    message_data = result["messages"][0]
                    return {
                        "success": True,
                        "message_id": message_data.get("id"),
                        "to": to,
                        "status": "sent"
                    }
                else:
                    logger.error(f"Invalid response from WhatsApp API: {result}")
                    return {"success": False, "error": "Invalid response from WhatsApp"}
                    
        except httpx.TimeoutException:
            logger.error("WhatsApp API request timeout")
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            return {"success": False, "error": "Network error"}
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {e}")
            return {"success": False, "error": "Internal error"}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify WhatsApp webhook signature for security
        
        Args:
            payload: Raw request body as string
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.app_secret:
            logger.warning("App secret not configured - skipping signature verification")
            return True
            
        try:
            # Remove 'sha256=' prefix from signature
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def verify_webhook_token(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook during setup process
        
        Args:
            mode: hub.mode parameter from Meta
            token: hub.verify_token parameter from Meta  
            challenge: hub.challenge parameter from Meta
            
        Returns:
            Challenge string if verification succeeds, None otherwise
        """
        if mode == "subscribe" and token == self.webhook_verify_token:
            logger.info("Webhook verification successful")
            return challenge
        else:
            logger.warning(f"Webhook verification failed: mode={mode}, token_match={token == self.webhook_verify_token}")
            return None
    
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
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming WhatsApp webhook message
        
        Args:
            webhook_data: Raw webhook JSON payload
            
        Returns:
            Parsed message data or None if invalid
        """
        try:
            # Navigate the WhatsApp webhook structure
            entry = webhook_data.get("entry", [])
            if not entry:
                return None
            
            changes = entry[0].get("changes", [])
            if not changes:
                return None
                
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            metadata = value.get("metadata", {})
            
            if not messages:
                logger.info("No messages in webhook payload")
                return None
            
            message = messages[0]
            contact = contacts[0] if contacts else {}
            
            # Extract message details
            parsed_data = {
                "message_id": message.get("id"),
                "from_phone": message.get("from"),
                "timestamp": message.get("timestamp"),
                "message_type": message.get("type"),
                "phone_number_id": metadata.get("phone_number_id"),
                "display_phone_number": metadata.get("display_phone_number"),
                "contact_name": contact.get("profile", {}).get("name"),
                "wa_id": contact.get("wa_id")
            }
            
            # Extract message content based on type
            if message.get("type") == "text":
                parsed_data["message_text"] = message.get("text", {}).get("body")
            elif message.get("type") == "image":
                image_data = message.get("image", {})
                parsed_data["media_id"] = image_data.get("id")
                parsed_data["media_mime_type"] = image_data.get("mime_type")
                parsed_data["media_caption"] = image_data.get("caption")
            elif message.get("type") == "location":
                location_data = message.get("location", {})
                parsed_data["latitude"] = location_data.get("latitude")
                parsed_data["longitude"] = location_data.get("longitude")
                parsed_data["location_name"] = location_data.get("name")
                parsed_data["location_address"] = location_data.get("address")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing WhatsApp webhook message: {e}")
            return None


# Global instance
whatsapp_service = WhatsAppService()