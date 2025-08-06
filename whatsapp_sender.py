import os
import requests
import time
from urllib.parse import unquote

class WhatsAppSender:
    """
    WhatsApp message sender using Meta's WhatsApp Cloud API.
    Provides both automatic sending and manual link generation.
    """
    
    def __init__(self):
        """Initialize WhatsApp sender with API credentials from environment variables."""
        # Meta WhatsApp Cloud API credentials
        self.access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
        self.business_account_id = os.environ.get("WHATSAPP_BUSINESS_ACCOUNT_ID")
        
        # API endpoints
        self.base_url = "https://graph.facebook.com/v18.0"
        self.messages_url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
        
    def is_configured(self):
        """Check if WhatsApp API is properly configured."""
        return bool(self.access_token and self.phone_number_id)
    
    def _rate_limit(self):
        """Implement basic rate limiting to avoid API throttling."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def format_phone_number(self, phone_number):
        """
        Format phone number for WhatsApp API.
        Removes all non-numeric characters and ensures proper format.
        """
        if not phone_number:
            return None
        
        # Remove all non-numeric characters
        cleaned = ''.join(filter(str.isdigit, str(phone_number)))
        
        # Remove leading zeros if present
        cleaned = cleaned.lstrip('0')
        
        # Add country code if not present (assuming +1 for demo)
        if len(cleaned) == 10:  # US number without country code
            cleaned = "1" + cleaned
        
        return cleaned
    
    def send_text_message(self, to_number, message_text):
        """
        Send a text message via WhatsApp Cloud API.
        
        Args:
            to_number (str): Recipient's phone number
            message_text (str): Message content
            
        Returns:
            dict: API response with success/error information
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp API not configured. Please add WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID to your environment variables.",
                "message_id": None
            }
        
        # Format phone number
        formatted_number = self.format_phone_number(to_number)
        if not formatted_number:
            return {
                "success": False,
                "error": "Invalid phone number format",
                "message_id": None
            }
        
        # Apply rate limiting
        self._rate_limit()
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_number,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        try:
            response = requests.post(
                self.messages_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "error": None,
                    "message_id": response_data.get("messages", [{}])[0].get("id"),
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": response_data.get("error", {}).get("message", "Unknown error"),
                    "message_id": None,
                    "response": response_data
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout - WhatsApp API did not respond in time",
                "message_id": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "message_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "message_id": None
            }
    
    def send_batch_messages(self, messages_data):
        """
        Send multiple messages with proper rate limiting.
        
        Args:
            messages_data (list): List of dicts with 'phone' and 'message' keys
            
        Returns:
            list: List of results for each message
        """
        results = []
        
        for i, data in enumerate(messages_data):
            phone = data.get('phone')
            message = data.get('message')
            lead_name = data.get('lead_name', f"Lead {i+1}")
            
            if not phone or not message:
                results.append({
                    "lead_name": lead_name,
                    "success": False,
                    "error": "Missing phone number or message",
                    "message_id": None
                })
                continue
            
            result = self.send_text_message(phone, message)
            result["lead_name"] = lead_name
            results.append(result)
            
            # Progress feedback
            print(f"Sent message {i+1}/{len(messages_data)} to {lead_name}")
        
        return results
    
    def get_setup_instructions(self):
        """Return instructions for setting up WhatsApp Cloud API."""
        return """
        ## WhatsApp Cloud API Setup Instructions
        
        To enable automatic WhatsApp message sending, you need to set up Meta's WhatsApp Cloud API:
        
        ### Step 1: Create Meta Business Account
        1. Go to https://business.facebook.com/
        2. Create a Business Account (if you don't have one)
        3. Verify your business information
        
        ### Step 2: Set up WhatsApp Business API
        1. Go to https://developers.facebook.com/
        2. Create a new app (Business type)
        3. Add WhatsApp product to your app
        4. Go to WhatsApp → Getting Started
        
        ### Step 3: Get Your Credentials
        1. **Access Token**: From your app dashboard
        2. **Phone Number ID**: From WhatsApp → Getting Started
        3. **Business Account ID**: From your Business Manager
        
        ### Step 4: Add to Environment Variables
        Add these to your Replit Secrets:
        - WHATSAPP_ACCESS_TOKEN: Your access token
        - WHATSAPP_PHONE_NUMBER_ID: Your phone number ID
        - WHATSAPP_BUSINESS_ACCOUNT_ID: Your business account ID
        
        ### Step 5: Verify Phone Number
        1. Add and verify your business phone number
        2. Complete the verification process
        3. Submit for approval if sending to numbers outside test group
        
        ### Free Tier Limits:
        - 1,000 free conversations per month
        - Service messages are completely free
        - 24-hour free response window after customer messages
        
        ### Note:
        - You can send to test numbers immediately after setup
        - For production use, you need Meta's approval
        - Template messages required for business-initiated conversations
        """
    
    def create_whatsapp_link(self, phone_number, message):
        """
        Create a clickable WhatsApp link as fallback.
        
        Args:
            phone_number (str): Phone number
            message (str): Message content
            
        Returns:
            str: WhatsApp web link
        """
        if not phone_number or not message:
            return "Invalid phone/message"
        
        formatted_number = self.format_phone_number(phone_number)
        if not formatted_number:
            return "Invalid phone number"
        
        # URL encode the message
        from urllib.parse import quote
        encoded_message = quote(message)
        
        return f"https://wa.me/{formatted_number}?text={encoded_message}"

def get_whatsapp_sender():
    """Factory function to get WhatsApp sender instance."""
    return WhatsAppSender()