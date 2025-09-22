import os
import json
import httpx
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_BASE = os.environ.get("API_BASE")  # ex: https://<api-id>.execute-api.us-east-1.amazonaws.com/v1
TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "10"))

def _pick(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return default

def _guess_operation(event):
    op = event.get("operationId")
    if op:
        return op
    path = _pick(event, "path", "apiPath", default="") or ""
    if "/confirmar-dados" in path: return "confirmar-dados"
    if "/exibir-opcoes-pagamento" in path: return "exibir-opcoes-pagamento"
    if "/exibir-dados" in path: return "exibir-dados"
    return "desconhecido"

def _extract_session(op, status_code, content_type, raw_body):
    """
    Lê a resposta JSON do backend e promove campos úteis para sessionAttributes.
    Importante: Bedrock exige string->string.
    """
    sess = {}
    if not (isinstance(content_type, str) and content_type.startswith("application/json")):
        return sess
    try:
        data = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except Exception:
        return sess
    if status_code != 200:
        # ainda assim podemos salvar algo de erro, se quiser
        return sess

    if op == "confirmar-dados":
        s02 = (data.get("retornoNSDGXS02") or {})
        sess.update({
            "flow_id": data.get("flow_id"),
            "cpf": s02.get("cpf"),
            "codigo_taxa": s02.get("codigo_taxa"),
            "codigo_servico": s02.get("codigo_servico"),
            "numero_cnh": s02.get("numero_cnh"),
            "ddd_celular": s02.get("ddd_celular"),
            "numero_celular": s02.get("numero_celular"),
            "email": s02.get("email"),
            "codigo_municipio_condutor": s02.get("codigo_municipio_condutor"),
            "nome_municipio_condutor": s02.get("nome_municipio_condutor"),
            "sigla_uf_municipio_condutor": s02.get("sigla_uf_municipio_condutor"),
        })
    elif op == "exibir-opcoes-pagamento":
        r414 = (data.get("retornoNsdgx414") or {})
        sess.update({
            "dae_linha_digitavel": r414.get("linha_digitavel"),
            "dae_codigo_barras_44": r414.get("codigo_barras"),
            "dae_valor": r414.get("valor_taxa"),
            "dae_vencimento": r414.get("data_vencimento"),
            "dae_municipio_desc": r414.get("descricao_municipio"),
            "dae_municipio_ibge": r414.get("codigo_municipio_ibge"),
            "dae_mes_ano": r414.get("mes_ano_dae"),
        })
    elif op == "exibir-dados":
        sess.update({
            "status_descricao_etapa": data.get("descricao_etapa"),
            "status_situacao_cnh": data.get("situacao_cnh"),
            "status_data_hora": data.get("data_hora_status"),
        })

    # Bedrock: somente strings
    return {k: str(v) for k, v in sess.items() if v is not None}

def lambda_handler(event, context):
    method = (_pick(event, "httpMethod", "method", default="POST") or "POST").upper()
    path   = _pick(event, "path", "apiPath", default="/") or "/"
    body   = _pick(event, "requestBody", "body", default=None)
    qs     = _pick(event, "queryStringParameters", "query", default=None)
    hdrs   = (_pick(event, "headers", default={}) or {}).copy()
    op     = _guess_operation(event)

    if not API_BASE:
        return _error_envelope(event, 500, {"message":"API_BASE não configurado"})

    url = f"{API_BASE}{path}"
    hdrs.setdefault("Content-Type", "application/json")

    try:
        # se for dict/list, manda como JSON; se vier string, vai como content
        json_body = body if isinstance(body, (dict, list)) else None
        content_body = None if isinstance(body, (dict, list)) else body

        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.request(
                method, url,
                params=qs,
                headers=hdrs,
                json=json_body,
                content=content_body
            )

        ctype = resp.headers.get("content-type", "application/json").split(";")[0].strip() or "application/json"

        # preservar corpo como string JSON (ou texto)
        try:
            parsed = resp.json()
            payload_str = json.dumps(parsed, ensure_ascii=False)
            payload_raw = parsed
        except Exception:
            payload_str = resp.text
            payload_raw = payload_str

        session_attrs = _extract_session(op, resp.status_code, ctype, payload_raw)

        # === Envelope no formato solicitado ===
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup") or "",
                "apiPath": event.get("apiPath") or path,
                "httpMethod": method,
                "httpStatusCode": resp.status_code,
                "responseBody": {
                    "application/json": {
                        "body": payload_str
                    }
                }
            },
            "sessionAttributes": session_attrs
        }

    except Exception as e:
        logging.exception("Erro na invocação HTTP")
        return _error_envelope(event, 502, {"message": f"Falha ao chamar backend: {e}"})

def _error_envelope(event, status_code: int, body: dict):
    """Mantém o mesmo formato também para erros (útil no Test chat)."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup") or "",
            "apiPath": event.get("apiPath") or _pick(event, "path", "apiPath", default="/"),
            "httpMethod": _pick(event, "httpMethod", "method", default="POST"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body, ensure_ascii=False)
                }
            }
        },
        "sessionAttributes": {
            "last_error": str(body.get("message", "")),
            "last_error_code": str(status_code)
        }
    }
