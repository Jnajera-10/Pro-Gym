import requests, os

WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL', '')
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN', '')

def send_whatsapp_message(phone, message):
    if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
        print(f'[WhatsApp] Simulated: {phone} -> {message}')
        return True
    response = requests.post(
        WHATSAPP_API_URL,
        headers={'Authorization': f'Bearer {WHATSAPP_TOKEN}'},
        json={'phone': phone, 'message': message}
    )
    return response.status_code == 200
