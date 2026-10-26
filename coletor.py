#!/usr/bin/env python3
"""
Radar Tributário: coleta diária de notícias, julgamentos e normas de direito tributário.

O que este script faz, em ordem:
  1. Lê as fontes listadas em fontes.txt (pesquisas no Google Notícias e feeds RSS).
  2. Descarta o que já foi coletado antes, o que é antigo e o que não trata de tributos.
  3. Se houver uma chave da API do Claude (ANTHROPIC_API_KEY), cada item recebe
     resumo didático, explicação prática, classificação e glossário.
     Sem a chave, o site funciona do mesmo jeito, só que com classificação automática simples.
  4. Grava tudo em docs/dados.json, que é o arquivo lido pelo site.

Você não precisa mexer neste arquivo. Para mudar as fontes, edite fontes.txt.
"""
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests

RAIZ = Path(__file__).parent
ARQ_DADOS = RAIZ / "docs" / "dados.json"
ARQ_FONTES = RAIZ / "fontes.txt"

CHAVE = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MODELO = os.environ.get("RADAR_MODELO", "claude-haiku-5-5")
MAX_NOVOS = int(os.environ.get("RADAR_MAX_NOVOS", "40"))   # limite de itens novos por dia
DIAS_JANELA = 3        # só aceita itens publicados nos últimos N dias
DIAS_HISTORICO = 120   # quanto tempo os itens ficam no site
FUSO = dt.timezone(dt.timedelta(hours=-3))  # horário de Brasília
AGENTE = "Mozilla/5.0 (RadarTributario; +https://github.com)"

TIPOS = ["Julgamento", "Decisão administrativa", "Norma e legislação", "Notícia e debate"]
TEMAS = [
    "Reforma Tributária", "ICMS", "PIS/Cofins", "Imposto de Renda",
    "Contribuições previdenciárias", "ISS", "Transação e dívida ativa",
    "Planejamento e compliance", "Outros temas",
]

PALAVRAS_TRIBUTARIAS = [
    "tribut", "imposto", "icms", "iss", "ipi", "irpj", "irpf", "imposto de renda", "csll",
    "pis", "cofins", "ibs", "cbs", "imposto seletivo", "carf", "receita federal", "pgfn",
    "fisco", "fiscal", "contribuinte", "contribuicao", "aliquota", "credito tributario",
    "divida ativa", "execucao fiscal", "transacao", "itcmd", "iptu", "ipva", "itbi",
    "simples nacional", "sefaz", "difal", "substituicao tributaria", "isencao", "sonegacao",
]


# ---------------------------------------------------------------- utilidades

def sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def limpar_html(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def agora() -> dt.datetime:
    return dt.datetime.now(FUSO)


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------- fontes

def ler_fontes() -> list[dict]:
    fontes = []
    for linha in ARQ_FONTES.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if linha.lower().startswith("busca:"):
            termos = linha.split(":", 1)[1].strip()
            consulta = quote_plus(f"{termos} when:2d")
            fontes.append({
                "nome": f"Google Notícias: {termos}",
                "url": f"https://news.google.com/rss/search?q={consulta}&hl=pt-BR&gl=BR&ceid=BR:pt-419",
                "busca": True,
            })
        elif "|" in linha:
            nome, url = [p.strip() for p in linha.split("|", 1)]
            fontes.append({"nome": nome, "url": url, "busca": False})
    return fontes


def baixar_feed(url: str):
    resp = requests.get(url, headers={"User-Agent": AGENTE}, timeout=30)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def data_do_item(entrada) -> dt.datetime | None:
    for campo in ("published_parsed", "updated_parsed"):
        valor = entrada.get(campo)
        if valor:
            return dt.datetime(*valor[:6], tzinfo=dt.timezone.utc).astimezone(FUSO)
    return None


def coletar(fontes: list[dict], vistos: set, titulos_vistos: set) -> list[dict]:
    limite = agora() - dt.timedelta(days=DIAS_JANELA)
    novos = []
    for fonte in fontes:
        try:
            feed = baixar_feed(fonte["url"])
        except Exception as erro:  # uma fonte fora do ar não derruba as outras
            log(f"  ! Não consegui ler {fonte['nome']}: {erro}")
            continue
        qtd = 0
        for e in feed.entries:
            link = e.get("link", "")
            titulo = limpar_html(e.get("title", ""))
            if not titulo or not link:
                continue
            veiculo = ""
            if e.get("source") and e.source.get("title"):
                veiculo = e.source.get("title")
            # O Google Notícias termina os títulos com " - Nome do veículo"
            if fonte["busca"] and " - " in titulo:
                base, fim = titulo.rsplit(" - ", 1)
                if not veiculo or sem_acento(fim) == sem_acento(veiculo):
                    titulo, veiculo = base.strip(), veiculo or fim.strip()
            veiculo = veiculo or (feed.feed.get("title") if not fonte["busca"] else "") or fonte["nome"]

            ident = hashlib.sha1(link.encode()).hexdigest()[:16]
            chave_titulo = sem_acento(re.sub(r"\W+", " ", titulo))[:70]
            if ident in vistos or chave_titulo in titulos_vistos:
                continue
            quando = data_do_item(e) or agora()
            if quando < limite:
                continue
            trecho = limpar_html(e.get("summary", ""))
            if sem_acento(trecho).startswith(sem_acento(titulo)[:40]):
                trecho = ""  # no Google Notícias o resumo costuma repetir o título
            texto_busca = sem_acento(f"{titulo} {trecho}")
            if not fonte["busca"] and not any(p in texto_busca for p in PALAVRAS_TRIBUTARIAS):
                continue  # feeds genéricos: guarda só o que fala de tributos

            vistos.add(ident)
            titulos_vistos.add(chave_titulo)
            novos.append({
                "id": ident, "titulo": titulo, "link": link, "veiculo": veiculo,
                "trecho": trecho[:1200], "data": quando.isoformat(timespec="minutes"),
            })
            qtd += 1
        log(f"  {fonte['nome']}: {qtd} novo(s)")
    novos.sort(key=lambda i: i["data"], reverse=True)
    return novos[:MAX_NOVOS]


# ---------------------------------------------------------------- classificação sem IA

REGRAS_TEMA = [
    ("Reforma Tributária", ["reforma tributaria", "ibs", "cbs", "imposto seletivo", "lc 214", "comite gestor", "split payment"]),
    ("ICMS", ["icms", "difal", "substituicao tributaria", "sefaz"]),
    ("PIS/Cofins", ["pis", "cofins"]),
    ("Imposto de Renda", ["imposto de renda", "irpj", "irpf", "csll", "dividendos", "jcp", "juros sobre capital"]),
    ("Contribuições previdenciárias", ["previdenciari", "inss", "folha de pagamento", "desoneracao", "rat", "fap"]),
    ("ISS", ["iss ", "issqn", "imposto sobre servicos"]),
    ("Transação e dívida ativa", ["transacao", "divida ativa", "execucao fiscal", "pgfn", "parcelamento", "refis", "litigio zero"]),
    ("Planejamento e compliance", ["planejamento tributario", "compliance", "obrigacao acessoria", "sped", "efd", "malha"]),
]


def orgao_de(texto: str) -> str:
    for nome, padrao in [
        ("STF", r"\bstf\b|supremo"), ("STJ", r"\bstj\b|superior tribunal de justica"),
        ("CARF", r"\bcarf\b"), ("PGFN", r"\bpgfn\b"), ("Receita Federal", r"receita federal"),
        ("Congresso", r"camara dos deputados|senado|congresso"), ("TRF", r"\btrf\d?\b"),
        ("Sefaz/Estados", r"sefaz|secretaria da fazenda|confaz"),
    ]:
        if re.search(padrao, texto):
            return nome
    return ""


def classificar_simples(item: dict) -> dict:
    t = sem_acento(f"{item['titulo']} {item['trecho']}")
    if re.search(r"julg|plenario|turma|repercussao geral|repetitivo|ministr|\btema \d|stf|stj|tribunal", t):
        tipo = "Julgamento"
    elif re.search(r"carf|solucao de consulta|delegacia de julgamento|drj", t):
        tipo = "Decisão administrativa"
    elif re.search(r"\blei\b|instrucao normativa|decreto|portaria|projeto de lei|lei complementar|regulament|medida provisoria|convenio", t):
        tipo = "Norma e legislação"
    else:
        tipo = "Notícia e debate"
    tema = next((nome for nome, chaves in REGRAS_TEMA if any(c in t for c in chaves)), "Outros temas")
    return {
        "tipo": tipo, "tema": tema, "orgao": orgao_de(t),
        "resumo": item["trecho"][:420] or "Resumo indisponível: abra a fonte para ler a íntegra.",
        "pratica": "", "termos": [], "importancia": 1, "analisado_por_ia": False,
    }


# ---------------------------------------------------------------- análise com o Claude

def perguntar_claude(prompt: str, max_tokens: int = 900) -> str:
    for tentativa in range(4):
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CHAVE, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": MODELO, "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        if resp.status_code in (429, 500, 502, 503, 529):
            time.sleep(10 * (tentativa + 1))
            continue
        resp.raise_for_status()
        return "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text")
    raise RuntimeError("API do Claude indisponível após várias tentativas")


PROMPT_ITEM = """Você é um professor de direito tributário brasileiro que prepara um boletim diário para advogados, contadores e estudantes.

Analise o item abaixo. Use SOMENTE as informações do título e do trecho; não invente números, datas, partes, placares ou fundamentos que não estejam ali. Se o trecho for curto, escreva um resumo prudente baseado no título e deixe isso claro com expressões como "segundo a manchete".

Título: {titulo}
Veículo: {veiculo}
Data: {data}
Trecho: {trecho}

Responda APENAS com um objeto JSON válido, sem texto antes ou depois, sem crases, neste formato:
{{
  "relevante": true ou false (false se não tratar de tributação, direito tributário ou finanças públicas tributárias),
  "tipo": um de {tipos},
  "tema": um de {temas},
  "orgao": órgão principal envolvido (ex.: "STF", "STJ", "CARF", "Receita Federal", "PGFN", "Congresso", "Sefaz-SP") ou "",
  "resumo": "2 a 3 frases claras e didáticas explicando o que aconteceu",
  "pratica": "1 a 2 frases sobre o que isso muda na prática para empresas, contribuintes ou profissionais; vazio se não der para dizer com segurança",
  "termos": [{{"termo": "expressão técnica citada", "explicacao": "explicação simples em uma frase"}}] (no máximo 3; lista vazia se não houver),
  "importancia": 1, 2 ou 3 (3 = decisão vinculante, mudança de lei ou impacto amplo; 1 = notícia de rotina)
}}"""


def extrair_json(texto: str):
    texto = texto.strip().replace("```json", "").replace("```", "")
    inicio, fim = texto.find("{"), texto.rfind("}")
    return json.loads(texto[inicio:fim + 1])


def analisar_com_ia(item: dict) -> dict | None:
    prompt = PROMPT_ITEM.format(
        titulo=item["titulo"], veiculo=item["veiculo"], data=item["data"][:10],
        trecho=item["trecho"] or "(sem trecho; use apenas o título)",
        tipos=json.dumps(TIPOS, ensure_ascii=False), temas=json.dumps(TEMAS, ensure_ascii=False),
    )
    r = extrair_json(perguntar_claude(prompt))
    if not r.get("relevante", True):
        return None
    return {
        "tipo": r.get("tipo") if r.get("tipo") in TIPOS else "Notícia e debate",
        "tema": r.get("tema") if r.get("tema") in TEMAS else "Outros temas",
        "orgao": str(r.get("orgao", ""))[:40],
        "resumo": str(r.get("resumo", ""))[:900],
        "pratica": str(r.get("pratica", ""))[:600],
        "termos": [t for t in r.get("termos", []) if isinstance(t, dict) and t.get("termo")][:3],
        "importancia": max(1, min(3, int(r.get("importancia", 1)))),
        "analisado_por_ia": True,
    }


def gerar_panorama(itens: list[dict]) -> str:
    lista = "\n".join(f"- [{i['tipo']} | {i['tema']}] {i['titulo']}: {i['resumo']}" for i in itens[:25])
    prompt = f"""Você escreve a abertura de um boletim diário de direito tributário brasileiro.
Com base SOMENTE nos itens abaixo, escreva um parágrafo de 80 a 130 palavras, em tom didático e sóbrio,
destacando os 2 ou 3 assuntos mais importantes do dia e por que importam. Não invente nada além do que está listado.
Responda só com o parágrafo, sem título.

{lista}"""
    return perguntar_claude(prompt, max_tokens=500).strip()


# ---------------------------------------------------------------- principal

def carregar_dados() -> dict:
    if ARQ_DADOS.exists():
        try:
            return json.loads(ARQ_DADOS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log("! dados.json estava corrompido; começando do zero")
    return {"itens": [], "panoramas": {}, "glossario": {}}


def main() -> int:
    log(f"Radar Tributário: coleta de {agora():%d/%m/%Y %H:%M}")
    log("Análise com IA: " + ("ATIVADA" if CHAVE else "desativada (sem ANTHROPIC_API_KEY)"))
    dados = carregar_dados()
    dados.setdefault("panoramas", {})
    dados.setdefault("glossario", {})

    vistos = {i["id"] for i in dados["itens"]}
    titulos = {sem_acento(re.sub(r"\W+", " ", i["titulo"]))[:70] for i in dados["itens"]}
    novos = coletar(ler_fontes(), vistos, titulos)
    log(f"Itens novos encontrados: {len(novos)}")

    aceitos = []
    for item in novos:
        analise = None
        if CHAVE:
            try:
                analise = analisar_com_ia(item)
                if analise is None:
                    log(f"  - fora do tema, descartado: {item['titulo'][:70]}")
                    continue
            except Exception as erro:
                log(f"  ! IA falhou para '{item['titulo'][:50]}': {erro}. Usando classificação simples.")
        item.update(analise or classificar_simples(item))
        for t in item.get("termos", []):
            dados["glossario"].setdefault(t["termo"].strip(), t.get("explicacao", "").strip())
        aceitos.append(item)

    hoje = agora().date().isoformat()
    if CHAVE and aceitos:
        try:
            dados["panoramas"][hoje] = gerar_panorama(sorted(aceitos, key=lambda i: -i["importancia"]))
        except Exception as erro:
            log(f"  ! Não consegui gerar o panorama: {erro}")

    corte = (agora() - dt.timedelta(days=DIAS_HISTORICO)).isoformat()
    dados["itens"] = sorted(
        [i for i in dados["itens"] + aceitos if i["data"] >= corte],
        key=lambda i: i["data"], reverse=True,
    )
    dados["panoramas"] = {d: p for d, p in dados["panoramas"].items() if d >= corte[:10]}
    dados["atualizado_em"] = agora().isoformat(timespec="minutes")
    dados["tipos"], dados["temas"] = TIPOS, TEMAS

    ARQ_DADOS.parent.mkdir(exist_ok=True)
    ARQ_DADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Concluído: {len(aceitos)} item(ns) adicionados, {len(dados['itens'])} no total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
