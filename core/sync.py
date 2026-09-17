import threading
import requests
import logging
import base64
import json
from django.conf import settings

logger = logging.getLogger(__name__)


def montar_dados_bolsista(bolsista):
    """
    Monta o dicionário completo do bolsista para upload.
    Roda de forma síncrona (antes da thread), garantindo acesso seguro ao banco.
    """
    sessoes = bolsista.sessaotrabalho_set.all().order_by('-entrada')
    dados = {
        "bolsista": {
            "nome": bolsista.nome,
            "pendencia_display": bolsista.pendencia_display()
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
        msg = "GITHUB_TOKEN ou GITHUB_REPO não configurados no .env — sincronização ignorada."
        logger.warning(msg)
        return False, msg

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
        elif r_get.status_code not in (404,):
            msg = f"Erro ao consultar arquivo no GitHub ({r_get.status_code}): {r_get.text}"
            logger.error(msg)
            return False, msg

        # 2. Fazer o PUT (commit direto no GitHub)
        payload = {
            "message": f"sync: atualiza histórico do token {bolsista_token[:6]}",
            "content": content_b64,
        }
        if sha:
            payload["sha"] = sha

        r_put = requests.put(url, headers=headers, json=payload, timeout=10)
        r_put.raise_for_status()
        logger.info(f"Sincronização com GitHub concluída: {path}")
        return True, None

    except Exception as e:
        msg = f"Falha ao sincronizar JSON com o GitHub (token={bolsista_token[:6]}): {e}"
        logger.error(msg)
        return False, msg


def sincronizar_historico_bolsista(bolsista):
    """
    Sincronização síncrona.
    Retorna uma tupla (sucesso: bool, mensagem_erro: str|None).
    """
    dados = montar_dados_bolsista(bolsista)
    return _upload_to_github(bolsista.token, dados)


def sincronizar_historico_bolsista_bg(bolsista):
    """
    Ponto de entrada para sincronização em background.
    Monta os dados no banco (síncrono) e dispara o upload em thread separada.
    """
    dados = montar_dados_bolsista(bolsista)
    threading.Thread(
        target=_upload_to_github,
        args=(bolsista.token, dados),
        daemon=True
    ).start()
