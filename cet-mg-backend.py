import json
import re

CPF_RE = re.compile(r"^\d{11}$")
DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

def _resp(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False)
    }

def _parse_json(body_str: str):
    try:
        return json.loads(body_str or "{}")
    except Exception:
        return {}

def _err_422(msg: str, field: str = None):
    errors = {}
    if field:
        errors[field] = {"_required": msg}
    else:
        errors["input"] = {"_invalid": msg}
    return _resp(422, {"message": "Ocorreu um erro na validação dos dados", "code": 422, "errors": errors})

# --------- validações simples ---------
def _require(payload, field, pattern: re.Pattern = None, fmt_desc: str = ""):
    v = payload.get(field)
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError(f'O campo "{field}" é obrigatório')
    if pattern and isinstance(v, str) and not pattern.match(v):
        raise ValueError(f'Campo "{field}" inválido. {fmt_desc}'.strip())
    return v

def _validate_confirmar(payload):
    _require(payload, "cpf", CPF_RE, "Use 11 dígitos numéricos")
    _require(payload, "nome_condutor")
    _require(payload, "data_nascimento", DATE_RE, "Formato DD/MM/AAAA")
    _require(payload, "nome_mae")

def _validate_emitir_guia(payload):
    # se vier flow_id, assumimos que o backend real preencherá o resto;
    # aqui apenas garantimos mínimos para o mock ficar útil
    if not payload.get("flow_id"):
        _require(payload, "cpf", CPF_RE, "Use 11 dígitos numéricos")
        _require(payload, "nome_condutor")
        _require(payload, "data_nascimento", DATE_RE, "Formato DD/MM/AAAA")
        _require(payload, "nome_mae")
        _require(payload, "codigo_taxa")
        _require(payload, "codigo_servico")
        _require(payload, "numero_cnh")
    _require(payload, "codigo_municipio_condutor")
    _require(payload, "ddd_celular")
    _require(payload, "numero_celular")
    _require(payload, "email")
    _require(payload, "numero_ip_micro")

def _validate_exibir_dados(payload):
    _require(payload, "cpf", CPF_RE, "Use 11 dígitos numéricos")
    _require(payload, "data_nascimento", DATE_RE, "Formato DD/MM/AAAA")

# --------- handlers ---------
def _from_agent_properties(payload: dict) -> dict:
    """
    Converte payload no formato:
    {"content":{"application/json":{"properties":[{"name":...,"value":...},...]}}}
    para {"name": "value", ...}
    """
    try:
        props = payload["content"]["application/json"]["properties"]
        if isinstance(props, list):
            flat = {}
            for item in props:
                k = item.get("name")
                v = item.get("value")
                if k is not None:
                    flat[k] = v
            return flat
    except Exception:
        pass
    return payload

def _normalize_keys(payload: dict) -> dict:
    # aceita sinônimos vindos do Agent
    if "nome" in payload and "nome_condutor" not in payload:
        payload["nome_condutor"] = payload["nome"]
    if "mae" in payload and "nome_mae" not in payload:
        payload["nome_mae"] = payload["mae"]
    if "nascimento" in payload and "data_nascimento" not in payload:
        payload["data_nascimento"] = payload["nascimento"]
    # limpa espaços
    for k, v in list(payload.items()):
        if isinstance(v, str):
            payload[k] = v.strip()
    return payload

def confirmar_dados(payload: dict):
    try:
        _validate_confirmar(payload)
    except ValueError as e:
        # 422 pedindo só o que falta/errado
        msg = str(e)
        # tenta extrair o nome do campo da msg
        field = None
        if '"' in msg:
            try:
                field = msg.split('"')[1]
            except Exception:
                field = None
        return _err_422(msg, field)

    cpf = payload.get("cpf")
    out = {
      "flow_id":"0a84e30c-3c9c-4f1c-9a5c-5d9a3b2d7f1a",
      "retornoNSDGXS02":{
        "codigo_retorno":0,"mensagem_retorno":"OK","cpf":cpf,
        "numero_cnh":"12345678900","numero_pgu":"99887766",
        "numero_identidade":"MG1234567","orgao_expedidor_identidade":"SSP","uf_identidade":"MG",
        "endereco_condutor":"Av. Afonso Pena","numero_endereco_condutor":"1000",
        "complemento_endereco_condutor":"Sala 101","bairro_endereco_condutor":"Centro",
        "codigo_municipio_condutor":4123,"nome_municipio_condutor":"BELO HORIZONTE","sigla_uf_municipio_condutor":"MG",
        "numero_cep_endereco_condutor":"30130008","data_primeira_habilitacao":"2010-06-15","data_validade_exame":"2027-05-23",
        "codigo_servico":123,"codigo_taxa":25,"flag_escolhe_entrega":1,"flag_tipo_autorizacao":"CNH",
        "ddd_celular":31,"numero_celular":999999999,"email":"condutor@example.com"
      }
    }
    return _resp(200, out)

def exibir_opcoes_pagamento(payload: dict):
    try:
        _validate_emitir_guia(payload)
    except ValueError as e:
        msg = str(e)
        field = None
        if '"' in msg:
            try:
                field = msg.split('"')[1]
            except Exception:
                field = None
        return _err_422(msg, field)

    cpf = payload.get("cpf", "00000000000")
    out = {
      "retornoNsdgxS2A":{"codigo_retorno":0,"mensagem_retorno":"OK"},
      "retornoNsdgx414":{
        "codigo_erro":0,"mensagem_erro":"",
        "codigo_tipo_contribuinte":"04","codigo_municipio_ibge":"062","descricao_municipio":"BELO HORIZONTE",
        "mes_ano_dae":"12/2024","data_vencimento":"31/12/2024",
        "linha_digitavel":"85610000001 2 26710213241 7 23112252400 3 02194270789 0",
        "codigo_barras":"856100000012267102132417231122524003021942707890",
        "nosso_numero":"2524000219427","nome_contribuinte":"CONDUTOR TESTE","valor_taxa":"126,71","quantidade_taxa":1,
        "data_emissao":"20/12/2024","cpf_contribuinte":cpf,"numero_identificao_contribuinte":"12345678900",
        "sigla_uf_origem_contribuinte":"MG",
        "campo_mensagem_1":"EXPEDICAO DA 2a VIA DA HABILITACAO",
        "campo_mensagem_2":"NUM. CNH: 12345678900",
        "campo_mensagem_3":"Solicitação Segunda Via de CNH / PPD",
        "campo_mensagem_4":"",                 # ADICIONADO
        "campo_mensagem_5":"- A segunda via da CNH sera emitida apos a confirmacao de pagamento",
        "campo_mensagem_6":"do DAE e enviada para o endereco do condutor atraves do correio.",
        "campo_mensagem_7":"Acompanhe a sua solicitacao atraves do site www.detran.mg.gov.br",
        "campo_mensagem_8":"",                 # ADICIONADO
        "campo_mensagem_9":"",                 # ADICIONADO
        "campo_mensagem_10":"",                # ADICIONADO
        "campo_mensagem_11":"",                # ADICIONADO
        "campo_mensagem_12":"",                # ADICIONADO
        "campo_mensagem_13":"Sr. Caixa,",
        "campo_mensagem_14":"Este documento deve ser recebido exclusivamente pela",
        "campo_mensagem_15":"leitura do codigo de barra ou linha digitavel",
        "campo_mensagem_16":"",                # ADICIONADO
        "campo_mensagem_17":"Data Emissao: 20/12/2024",
        "campo_mensagem_18":"",                # ADICIONADO
        "codigo_taxa":25,"codigo_municipio":"4123"
      },
      "codigoBarras":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB..."  # base64 ilustrativo
    }
    return _resp(200, out)

def exibir_dados(payload: dict):
    try:
        _validate_exibir_dados(payload)
    except ValueError as e:
        msg = str(e)
        field = None
        if '"' in msg:
            try:
                field = msg.split('"')[1]
            except Exception:
                field = None
        return _err_422(msg, field)

    cpf = payload.get("cpf")
    out = {
      "cpf":cpf,"numero_renach":"MG-123456789","nome_condutor":"CONDUTOR TESTE","numero_formulario_renach":"FORM-0001",
      "codigo_etapa":4,"descricao_etapa":"Emissão concluída","prazo":0,"titulo_entrega":"Postado nos Correios",
      "data_entrega_lote":"2025-09-18","titulo_hora_entrega":"Até 18h","hora_entrega_lote":"18:00:00",
      "data_hora_status":"2025-09-18T12:10:00Z","texto_ar_correio":"AR: 123456789BR","numero_ar_correio":"123456789BR",
      "data_ar_correio":"2025-09-18","situacao_cnh":"Emitida","descricao_situacao_entrega":"Em trânsito",
      "codigo_retorno_binco":0,"descricao_retorno_binco":"Sem restrições","data_retorno_binco":"2024-12-19",
      "descricao_situacao_cnh":"Regular","texto_livre_rejeicao":"","titulo_motivo_devolucao":"","titulo_motivo_baixa":"",
      "titulo_motivo_rejeicao":"","quantidade_motivo_rejeicao":0,"codigo_rejeicao":[],"motivo_rejeicao":[],
      "descricao_acao":"Acompanhar entrega pelo AR"
    }
    return _resp(200, out)

ROUTES = {
    ("/confirmar-dados","POST"): confirmar_dados,
    ("/exibir-opcoes-pagamento","POST"): exibir_opcoes_pagamento,
    ("/exibir-dados","POST"): exibir_dados
}

def lambda_handler(event, context):
    print(event)
    path = event.get("path") or event.get("resource") or "/"
    method = event.get("httpMethod","POST").upper()
    body = event.get("body") or "{}"
    payload = _parse_json(body)
    payload = _from_agent_properties(payload)
    payload = _normalize_keys(payload)
    handler = ROUTES.get((path,method))
    if not handler:
        return _resp(404, {"message":"Rota não encontrada"})
    return handler(payload)
