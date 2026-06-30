"""
Solución al cold start de Render gratuito.
Este script puede ejecutarse como cron job externo (UptimeRobot, cron-job.org)
apuntando a: https://TU-APP.onrender.com/health
cada 14 minutos para mantener el servidor activo 24/7.
"""
import requests
import os

APP_URL = os.environ.get('APP_URL', 'https://gymsystem.onrender.com')

def ping():
    try:
        r = requests.get(f'{APP_URL}/health', timeout=10)
        print(f'Ping OK: {r.status_code}')
    except Exception as e:
        print(f'Ping fallido: {e}')

if __name__ == '__main__':
    ping()
