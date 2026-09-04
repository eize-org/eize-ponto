import threading
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def _post_sync(url, payload):
    sync_url = getattr(settings, 'SYNC_URL', '')
    sync_key = getattr(settings, 'SYNC_KEY', '')
    
    if not sync_url or not sync_key:
        return

    headers = {'X-Sync-Key': sync_key}
    endpoint = f"{sync_url.rstrip('/')}/{url.lstrip('/')}/"
    
    try:
        # 5s timeout evita travar a thread caso o PythonAnywhere caia
        requests.post(endpoint, json=payload, headers=headers, timeout=5)
    except Exception as e:
        # A falha não quebra o sistema local — o ponto foi batido com sucesso
        logger.error(f"Falha ao sincronizar com a nuvem ({endpoint}): {e}")

def sincronizar_bolsista_bg(bolsista):
    payload = {
        'token': bolsista.token,
        'nome': bolsista.nome,
        'pendencia_min': bolsista.pendencia_min
    }
    threading.Thread(target=_post_sync, args=('sincronizar/bolsista', payload), daemon=True).start()

def sincronizar_sessao_bg(sessao):
    payload = {
        'id_origem': sessao.id,
        'bolsista_token': sessao.bolsista.token,
        'tipo': sessao.tipo,
        'entrada': sessao.entrada.isoformat() if sessao.entrada else None,
        'saida': sessao.saida.isoformat() if sessao.saida else None,
        'min_trabalhados': sessao.min_trabalhados,
        'diferenca_min': sessao.diferenca_min,
        'pendencia_abatida_min': sessao.pendencia_abatida_min
    }
    threading.Thread(target=_post_sync, args=('sincronizar/sessao', payload), daemon=True).start()
