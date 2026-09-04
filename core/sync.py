import threading
import requests
import logging
import base64
import json
from django.conf import settings

logger = logging.getLogger(__name__)

def montar_dados_bolsista(bolsista):
    # Essa função roda de forma síncrona, antes de separar a thread,
    # para evitar problemas de acesso ao banco de dados concorrente.
    sessoes = bolsista.sessaotrabalho_set.all().order_by('entrada')
    dados = {
        "bolsista": {
            "nome": bolsista.nome,
            "pendencia_display": bolsista.pendencia_display
        },
        "sessoes": []
    }
    for s in sessoes:
        dados["sessoes"].append({
            "tipo": s.tipo,
            "entrada": s.entrada.isoformat() if s.entrada else None,
            "saida": s.saida.isoformat() if s.saida else None,
            "trabalhado_display": s.mostra_trabalhados(),
            "diferenca_display": s.mostra_diferenca()
        })
    return dados

def _upload_to_github(bolsista_token, dados):
    github_token = getattr(settings, 'GITHUB_TOKEN', '')
    github_repo = getattr(settings, 'GITHUB_REPO', '')
    
    if not github_token or not github_repo:
        return
        
    try:
        json_str = json.dumps(dados, ensure_ascii=False, indent=2)
        content_b64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        path = f"api/{bolsista_token}.json"
        url = f"https://api.github.com/repos/{github_repo}/contents/{path}"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 1. Obter o SHA do arquivo atual (se existir)
        sha = None
        r_get = requests.get(url, headers=headers, timeout=5)
        if r_get.status_code == 200:
            sha = r_get.json().get('sha')

        # 2. Fazer o PUT (commit direto no GitHub)
        payload = {
            "message": f"sync: atualiza histórico do token {bolsista_token[:6]}",
            "content": content_b64,
        }
        if sha:
            payload["sha"] = sha

        r_put = requests.put(url, headers=headers, json=payload, timeout=10)
        r_put.raise_for_status()
        
    except Exception as e:
        logger.error(f"Falha ao sincronizar JSON com o GitHub ({bolsista_token}): {e}")

def sincronizar_bolsista_bg(bolsista):
    dados = montar_dados_bolsista(bolsista)
    threading.Thread(target=_upload_to_github, args=(bolsista.token, dados), daemon=True).start()

def sincronizar_sessao_bg(sessao):
    # Como a arquitetura agora salva um único arquivo .json por bolsista,
    # atualizar uma sessão significa regerar e enviar o arquivo do bolsista dono dela.
    sincronizar_bolsista_bg(sessao.bolsista)
