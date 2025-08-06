import os
from openai import OpenAI

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_whatsapp_message(lead_name, risk_score):
    """
    Generate a personalized WhatsApp message using GPT based on the lead's risk score.
    
    Args:
        lead_name (str): Name of the lead
        risk_score (str): Risk category ('High', 'Medium', or 'Low')
        
    Returns:
        str: Generated WhatsApp message
    """
    
    # Fallback template messages in case API fails
    fallback_messages = {
        'High': f"Hi {lead_name}, your demo is scheduled but we missed you last time. Can we quickly reconnect today or tomorrow?",
        'Medium': f"Hi {lead_name}, just checking in. Shall we go ahead with the demo this week?",
        'Low': f"Hey {lead_name}, just a friendly nudge to confirm our upcoming demo. Excited to connect!"
    }
    
    # If no API key is provided or it's the default, use fallback
    if OPENAI_API_KEY == "your-api-key-here" or not OPENAI_API_KEY:
        return fallback_messages.get(risk_score, fallback_messages['Medium'])
    
    try:
        # Create context-aware prompt for GPT
        risk_context = {
            'High': "This lead is high risk - they have missed demos, have been inactive for a long time, or haven't engaged with our content. We need to be more direct and urgent in our approach to re-engage them.",
            'Medium': "This lead is medium risk - they show some engagement but need gentle follow-up. They might need a bit more nurturing to move forward.",
            'Low': "This lead is low risk - they are engaged and have shown up for demos or interacted recently. Keep the tone friendly and confirmatory."
        }
        
        prompt = f"""
        You are a sales outreach specialist. Generate a UNIQUE, personalized WhatsApp message for a lead named "{lead_name}" 
        who has been categorized as "{risk_score}" risk.
        
        Context for {risk_score} risk: {risk_context.get(risk_score, '')}
        
        IMPORTANT: Create a UNIQUE message that varies significantly from other messages. Use different:
        - Conversation starters (Hi/Hey/Hello/Good day)
        - Phrasing and sentence structure
        - Call-to-action approaches
        - Time references (today/tomorrow/this week/soon)
        - Conversation tone (casual/professional/friendly)
        
        Guidelines:
        - Keep the message under 160 characters for WhatsApp
        - Use a friendly, professional tone
        - Include the lead's name naturally
        - Make it conversational and not too salesy
        - For High risk: Be more direct and suggest immediate action
        - For Medium risk: Be encouraging and suggest this week
        - For Low risk: Be friendly and confirmatory
        - Don't use excessive punctuation or emojis
        - Vary the message structure and wording significantly
        
        Generate only the message text, no quotes or additional formatting.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "system", "content": "You are a creative sales outreach specialist who creates unique, personalized WhatsApp messages. Never repeat the same phrasing or structure. Always vary your approach significantly for each lead."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.9  # Increased temperature for more variation
        )
        
        generated_message = response.choices[0].message.content
        if generated_message:
            generated_message = generated_message.strip()
        else:
            generated_message = ""
        
        # Validate the generated message
        if len(generated_message) > 200:  # Reasonable limit for WhatsApp
            return fallback_messages.get(risk_score, fallback_messages['Medium'])
        
        if not generated_message or len(generated_message.strip()) < 10:
            return fallback_messages.get(risk_score, fallback_messages['Medium'])
        
        return generated_message
        
    except Exception as e:
        # Log the error (in a real app, you'd use proper logging)
        print(f"Error generating WhatsApp message: {str(e)}")
        
        # Return fallback message
        return fallback_messages.get(risk_score, fallback_messages['Medium'])

def generate_batch_messages(leads_data):
    """
    Generate WhatsApp messages for multiple leads efficiently.
    
    Args:
        leads_data (list): List of dictionaries with 'lead_name' and 'risk_score' keys
        
    Returns:
        list: List of generated messages corresponding to input leads
    """
    
    messages = []
    
    for lead in leads_data:
        lead_name = lead.get('lead_name', 'there')
        risk_score = lead.get('risk_score', 'Medium')
        
        message = generate_whatsapp_message(lead_name, risk_score)
        messages.append(message)
    
    return messages

def validate_message_length(message):
    """
    Validate that the message is appropriate for WhatsApp.
    
    Args:
        message (str): The message to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    
    if not message or not message.strip():
        return False, "Message is empty"
    
    if len(message) > 200:
        return False, "Message too long for WhatsApp (max 200 characters recommended)"
    
    if len(message.strip()) < 10:
        return False, "Message too short to be meaningful"
    
    return True, "Message is valid"

def get_message_templates():
    """
    Get the template messages for each risk category.
    
    Returns:
        dict: Template messages for each risk level
    """
    
    return {
        'High': "Hi [Lead Name], your demo is scheduled but we missed you last time. Can we quickly reconnect today or tomorrow?",
        'Medium': "Hi [Lead Name], just checking in. Shall we go ahead with the demo this week?",
        'Low': "Hey [Lead Name], just a friendly nudge to confirm our upcoming demo. Excited to connect!"
    }
