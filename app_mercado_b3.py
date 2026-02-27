import os
import json
import time
import logging
import warnings
import re
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
import litellm
import requests

load_dotenv()
litellm.num_retries = 5
litellm.retry_after = 15
litellm.request_timeout = 120
litellm.drop_params = True

st.set_page_config(page_title="Carteira Inteligente", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

* { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

/* Tema claro profissional estilo Bloomberg */
[data-testid="stAppViewContainer"] { background: #f4f5f7; color: #1a1d23; }
[data-testid="stMain"] { background: #f4f5f7; }
[data-testid="stSidebar"] { background: #1a1d23; border-right: 3px solid #e8b84b; }
[data-testid="stSidebar"] * { color: #e8e8e8 !important; }
[data-testid="stSidebar"] .stButton > button { background: #e8b84b !important; color: #1a1d23 !important; font-weight: 700 !important; }

/* Cards métricas */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-left: 4px solid #e8b84b;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 6px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    overflow: hidden;
    min-height: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.metric-value {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    font-weight: 800;
    color: #1a1d23;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-label {
    font-size: 0.63rem;
    color: #6b7280;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 5px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Cores */
.positive { color: #0f7b3e !important; }
.negative { color: #c0392b !important; }
.neutral  { color: #4b5563 !important; }

/* Cabeçalhos de seção */
.section-header {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    color: #6b7280;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 32px 0 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e8b84b;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Caixas de relatório */
.report-box {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    padding: 28px 32px;
    line-height: 1.8;
    color: #1a1d23;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 0.95rem;
}

/* Notícias */
.news-card {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border-left: 3px solid #e2e5ea;
    transition: border-left-color 0.2s;
}

/* Dividendos */
.div-card {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-left: 4px solid #0f7b3e;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Badges sentimento */
.badge-otimista { background: #dcfce7; color: #0f7b3e; border: 1px solid #86efac; border-radius: 4px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }
.badge-pessimista { background: #fee2e2; color: #c0392b; border: 1px solid #fca5a5; border-radius: 4px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }
.badge-neutro { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; border-radius: 4px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }
.badge-curto { background: #ede9fe; color: #5b21b6; border: 1px solid #c4b5fd; border-radius: 4px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }
.badge-longo { background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; border-radius: 4px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }

/* Score */
.score-card {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    padding: 20px;
    margin: 6px 0;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.score-value { font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 800; }
.impacto-box {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-left: 4px solid #e8b84b;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.rsi-box {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 6px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Botão principal */
.stButton > button {
    background: #1a1d23 !important;
    color: #e8b84b !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 14px 28px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
}

/* Cabeçalho hero */
.hero-wrap {
    border-bottom: 3px solid #e8b84b;
    padding-bottom: 20px;
    margin-bottom: 8px;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem;
    font-weight: 800;
    color: #1a1d23;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.hero-ticker {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    color: #e8b84b;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.hero-sub { color: #6b7280; font-size: 0.9rem; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# CARTEIRA
# ══════════════════════════════════════════════════════════════
ACOES_B3 = {
    "CXSE3.SA": "Caixa Seguridade | Seguros & Financeiro",
    "RANI3.SA":  "Irani | Papel & Embalagens",
    "TAEE3.SA":  "Taesa | Energia Elétrica",
    "CSAN3.SA":  "Cosan | Energia & Logística",
    "BBAS3.SA":  "Banco do Brasil | Financeiro",
    "PETR3.SA":  "Petrobras | Petróleo & Gás",
    "BTC-USD":   "Bitcoin | Criptomoeda",
}

# ══════════════════════════════════════════════════════════════
# COLETA DE DADOS
# ══════════════════════════════════════════════════════════════

def calcular_rsi(serie, periodo=14) -> float:
    try:
        delta = serie.diff()
        ganho = delta.where(delta > 0, 0).rolling(periodo).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
        rs    = ganho / perda
        rsi   = 100 - (100 / (1 + rs))
        return round(float(rsi.iloc[-1]), 1)
    except Exception:
        return 50.0


def buscar_cotacoes() -> list:
    resultados = []
    for ticker_str, info in ACOES_B3.items():
        try:
            ticker  = yf.Ticker(ticker_str)
            hist    = ticker.history(period="5d")
            hist_30 = ticker.history(period="1mo")
            hist_10 = ticker.history(period="10d")
            if hist.empty or len(hist) < 2:
                continue
            abertura   = round(float(hist["Close"].iloc[0]),  2)
            fechamento = round(float(hist["Close"].iloc[-1]), 2)
            maximo     = round(float(hist["High"].max()),     2)
            minimo     = round(float(hist["Low"].min()),      2)
            volume     = int(hist["Volume"].mean())
            variacao   = round(((fechamento - abertura) / abertura) * 100, 2)
            retornos   = hist["Close"].pct_change().dropna()
            volatilidade = round(float(retornos.std()) * 100, 2) if len(retornos) > 1 else 0
            maior_queda  = round(float(((hist["Low"].min() - hist["High"].max()) / hist["High"].max()) * 100), 2)
            rsi = calcular_rsi(hist_30["Close"]) if not hist_30.empty else 50.0
            var_anterior = 0
            if not hist_10.empty and len(hist_10) >= 4:
                meio = len(hist_10) // 2
                ab_ant = float(hist_10["Close"].iloc[0])
                fe_ant = float(hist_10["Close"].iloc[meio])
                var_anterior = round(((fe_ant - ab_ant) / ab_ant) * 100, 2)
            nome, setor = info.split(" | ")
            historico = [
                {"data": str(d.date()), "preco": round(float(p), 2)}
                for d, p in zip(hist.index, hist["Close"])
            ]
            resultados.append({
                "ticker":       ticker_str.replace(".SA", "").replace("-USD", ""),
                "ticker_sa":    ticker_str,
                "nome":         nome,
                "setor":        setor,
                "abertura":     abertura,
                "atual":        fechamento,
                "maxima":       maximo,
                "minima":       minimo,
                "variacao":     variacao,
                "var_anterior": var_anterior,
                "volume":       volume,
                "volatilidade": volatilidade,
                "maior_queda":  maior_queda,
                "rsi":          rsi,
                "historico":    historico,
            })
        except Exception:
            continue
    resultados.sort(key=lambda x: x["variacao"], reverse=True)
    return resultados


def buscar_fundamentals(ticker_str: str) -> dict:
    try:
        info = yf.Ticker(ticker_str).info
        dy   = (info.get("dividendYield", 0) or 0) * 100
        return {
            "pl":             round(info.get("trailingPE", 0) or 0, 2),
            "pvp":            round(info.get("priceToBook", 0) or 0, 2),
            "dy":             round(dy if dy <= 30 else 0, 2),
            "market_cap":     info.get("marketCap", 0),
            "roe":            round((info.get("returnOnEquity", 0) or 0) * 100, 2),
            "divida_pl":      round(info.get("debtToEquity", 0) or 0, 2),
            "preco_alvo":     round(info.get("targetMeanPrice", 0) or 0, 2),
            "preco_alvo_min": round(info.get("targetLowPrice", 0) or 0, 2),
            "preco_alvo_max": round(info.get("targetHighPrice", 0) or 0, 2),
            "recomendacao":   info.get("recommendationKey", "N/D"),
        }
    except Exception:
        return {"pl": 0, "pvp": 0, "dy": 0, "market_cap": 0, "roe": 0,
                "divida_pl": 0, "preco_alvo": 0, "preco_alvo_min": 0,
                "preco_alvo_max": 0, "recomendacao": "N/D"}


def buscar_dividendos() -> list:
    dividendos = []
    for ticker_str, info in ACOES_B3.items():
        try:
            hist = yf.Ticker(ticker_str).dividends
            if hist.empty:
                continue
            nome, _ = info.split(" | ")
            for data, valor in hist.tail(3).items():
                dividendos.append({
                    "ticker": ticker_str.replace(".SA", "").replace("-USD", ""),
                    "nome":   nome,
                    "data":   str(data.date()) if hasattr(data, "date") else str(data)[:10],
                    "valor":  round(float(valor), 4),
                })
        except Exception:
            continue
    return sorted(dividendos, key=lambda x: x["data"], reverse=True)


def buscar_noticias(ticker: str, nome: str) -> list:
    try:
        ticker_yf = "BTC-USD" if ticker in ("BTC", "BTC-USD") else f"{ticker}.SA"
        noticias  = []
        for n in yf.Ticker(ticker_yf).news[:5]:
            content = n.get("content", {})
            titulo  = content.get("title", "")
            if titulo:
                noticias.append({
                    "titulo": titulo,
                    "link":   content.get("canonicalUrl", {}).get("url", "#"),
                    "fonte":  content.get("provider", {}).get("displayName", "Yahoo Finance"),
                    "data":   content.get("pubDate", "")[:16],
                })
        return noticias
    except Exception:
        return []


def buscar_correlacoes() -> dict:
    dados = {}
    for nome, ticker in {"IBOV": "^BVSP", "Dólar": "USDBRL=X", "BTC": "BTC-USD"}.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if not hist.empty and len(hist) >= 2:
                ab = float(hist["Close"].iloc[0])
                fe = float(hist["Close"].iloc[-1])
                dados[nome] = {"variacao": round(((fe - ab) / ab) * 100, 2), "atual": round(fe, 2)}
        except Exception:
            continue
    return dados


# ══════════════════════════════════════════════════════════════
# CALENDÁRIO DE RESULTADOS
# ══════════════════════════════════════════════════════════════

def buscar_resultados() -> list:
    """Busca datas e dados de resultados trimestrais via yfinance."""
    resultados = []
    for ticker_str, info in ACOES_B3.items():
        if ticker_str == "BTC-USD":
            continue
        try:
            t    = yf.Ticker(ticker_str)
            nome, setor = info.split(" | ")
            cal  = t.calendar
            fins = t.quarterly_financials
            earn = t.quarterly_earnings

            # Data do próximo resultado
            proxima_data = None
            if cal is not None and not (hasattr(cal, "empty") and cal.empty):
                try:
                    if isinstance(cal, dict):
                        proxima_data = cal.get("Earnings Date", [None])[0]
                    elif hasattr(cal, "loc"):
                        proxima_data = cal.loc["Earnings Date"].iloc[0] if "Earnings Date" in cal.index else None
                except Exception:
                    pass

            # Último resultado disponível
            receita_atual = receita_anterior = lucro_atual = lucro_anterior = None
            if fins is not None and not fins.empty and "Total Revenue" in fins.index:
                rev = fins.loc["Total Revenue"].dropna()
                if len(rev) >= 2:
                    receita_atual    = float(rev.iloc[0])
                    receita_anterior = float(rev.iloc[1])
            if fins is not None and not fins.empty and "Net Income" in fins.index:
                ni = fins.loc["Net Income"].dropna()
                if len(ni) >= 2:
                    lucro_atual    = float(ni.iloc[0])
                    lucro_anterior = float(ni.iloc[1])

            var_receita = round(((receita_atual - receita_anterior) / abs(receita_anterior)) * 100, 1) if receita_atual and receita_anterior else None
            var_lucro   = round(((lucro_atual - lucro_anterior) / abs(lucro_anterior)) * 100, 1) if lucro_atual and lucro_anterior else None

            # Data do último resultado divulgado
            ultimo_resultado = "N/D"
            if fins is not None and not fins.empty:
                try:
                    ultima_col = fins.columns[0]
                    ultimo_resultado = str(ultima_col.date()) if hasattr(ultima_col, "date") else str(ultima_col)[:10]
                except Exception:
                    pass

            resultados.append({
                "ticker":           ticker_str.replace(".SA", ""),
                "nome":             nome,
                "setor":            setor,
                "proxima_data":     str(proxima_data.date()) if proxima_data and hasattr(proxima_data, "date") else "A confirmar",
                "ultimo_resultado": ultimo_resultado,
                "var_receita":      var_receita,
                "var_lucro":        var_lucro,
                "receita_atual":    receita_atual,
                "lucro_atual":      lucro_atual,
            })
        except Exception:
            continue
    return resultados


def avaliar_resultados_ia(resultados: list, api_key: str) -> str:
    """Usa IA para avaliar se os últimos resultados foram bons ou ruins por prazo."""
    if not resultados or not api_key:
        return ""
    try:
        client = Groq(api_key=api_key)
        dados  = []
        for r in resultados:
            linha = f"{r['ticker']} ({r['nome']}): receita {r['var_receita']:+.1f}% vs trim. anterior, lucro {r['var_lucro']:+.1f}%" if r["var_receita"] is not None and r["var_lucro"] is not None else f"{r['ticker']} ({r['nome']}): dados insuficientes"
            dados.append(linha)
        prompt = f"""Analise os resultados trimestrais abaixo e escreva uma avaliação concisa em português, com no máximo 250 palavras, estruturada em 3 parágrafos:

1. **Curto Prazo** — O que esses números significam para as ações nas próximas semanas?
2. **Médio Prazo** — Tendência para os próximos 2-4 trimestres?
3. **Longo Prazo** — Os fundamentos suportam crescimento sustentável?

Resultados:
{chr(10).join(dados)}

Seja direto e use linguagem acessível para investidores pessoa física."""
        resp = client.chat.completions.create(
            messages=[{{"role": "user", "content": prompt}}],
            model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
# SENTIMENTO
# ══════════════════════════════════════════════════════════════

def analisar_sentimento(noticias, ticker, nome, api_key) -> dict:
    if not noticias or not api_key:
        return {"noticias": noticias, "score": 5.0, "sentimento_geral": "Neutro", "impacto_resumo": ""}
    try:
        client  = Groq(api_key=api_key)
        titulos = [f"{i+1}. {n['titulo']}" for i, n in enumerate(noticias)]
        prompt  = f"""Analise notícias sobre {nome} ({ticker}). Responda SOMENTE em JSON:

{chr(10).join(titulos)}

{{"score": <0-10>, "sentimento_geral": "<Otimista|Pessimista|Neutro>", "impacto_resumo": "<2 frases>", "noticias": [{{"indice": 1, "sentimento": "<Otimista|Pessimista|Neutro>", "prazo": "<Curto|Longo>"}}]}}"""
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=500,
        )
        raw = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        res = json.loads(raw)
        analises = {a["indice"]: a for a in res.get("noticias", [])}
        for i, n in enumerate(noticias):
            an = analises.get(i+1, {})
            n["sentimento"] = an.get("sentimento", "Neutro")
            n["prazo"]      = an.get("prazo", "Curto")
        return {
            "noticias":         noticias,
            "score":            round(float(res.get("score", 5.0)), 1),
            "sentimento_geral": res.get("sentimento_geral", "Neutro"),
            "impacto_resumo":   res.get("impacto_resumo", ""),
        }
    except Exception:
        for n in noticias:
            n["sentimento"] = "Neutro"
            n["prazo"]      = "Curto"
        return {"noticias": noticias, "score": 5.0, "sentimento_geral": "Neutro", "impacto_resumo": ""}


# ══════════════════════════════════════════════════════════════
# IA
# ══════════════════════════════════════════════════════════════

def gerar_relatorio_ia(cotacoes, correlacoes, api_key):
    llm = LLM(model="groq/llama-3.3-70b-versatile", api_key=api_key, temperature=0.3, max_retries=5, timeout=120)

    analista = Agent(role="Analista de Mercado Sênior (CNPI)", goal="Analisar carteira da B3 e correlações.",
                     backstory="Analista CNPI com 15 anos na B3.", llm=llm, verbose=False, allow_delegation=False, max_iter=3)
    tarefa_analise = Task(
        description=(f"Carteira: {json.dumps(cotacoes, ensure_ascii=False)}\n\n"
                     f"Correlações (IBOV/Dólar/BTC): {json.dumps(correlacoes, ensure_ascii=False)}\n\n"
                     "Escreva análise com: 1.Panorama geral 2.Maiores altas 3.Maiores baixas "
                     "4.Impacto do dólar e BTC na carteira 5.Perspectivas. Máximo 400 palavras."),
        expected_output="Análise em Markdown, 5 seções, máximo 400 palavras.", agent=analista,
    )
    resultado_analise = str(Crew(agents=[analista], tasks=[tarefa_analise], verbose=False).kickoff())
    time.sleep(20)

    consultor = Agent(role="Consultor de Investimentos (CFP/CEA)", goal="Recomendações e cenários para a carteira.",
                      backstory="Consultor CFP/CEA especialista em carteiras brasileiras.", llm=llm, verbose=False, allow_delegation=False, max_iter=3)
    tarefa_rec = Task(
        description=(f"Análise: {resultado_analise}\n\n"
                     "Crie recomendações: 1.Disclaimer 2.Resumo executivo 3.Perfil Conservador "
                     "4.Perfil Moderado 5.Perfil Arrojado 6.Top 3 ativos "
                     "7.Cenário otimista e pessimista. Máximo 450 palavras."),
        expected_output="Recomendações em Markdown, 7 seções, máximo 450 palavras.", agent=consultor,
    )
    resultado_rec = str(Crew(agents=[consultor], tasks=[tarefa_rec], verbose=False).kickoff())
    return {"analise": resultado_analise, "recomendacoes": resultado_rec,
            "gerado_em": datetime.now().strftime("%d/%m/%Y às %H:%M")}


# ══════════════════════════════════════════════════════════════
# PDF
# ══════════════════════════════════════════════════════════════

def gerar_pdf(cotacoes, relatorio, correlacoes) -> bytes:
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    stl  = getSampleStyleSheet()
    h1   = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#1a56db"), spaceAfter=6)
    h2   = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14, textColor=colors.HexColor("#1a56db"), spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", fontSize=10, leading=16, spaceAfter=6)
    sm   = ParagraphStyle("sm",   fontSize=8,  textColor=colors.HexColor("#666"))
    story = []
    story.append(Paragraph("Carteira Inteligente", h1))
    story.append(Paragraph(f"Relatório Semanal — {relatorio['gerado_em']}", sm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a56db")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Resumo da Carteira", h2))
    rows = [["Ticker","Empresa","Atual","Variação","Sem. Anterior","Volatilidade","RSI"]]
    for c in cotacoes:
        pref = "US$" if c["ticker_sa"] == "BTC-USD" else "R$"
        rows.append([c["ticker"], c["nome"], f"{pref} {c['atual']:,.2f}",
                     f"{c['variacao']:+.2f}%", f"{c['var_anterior']:+.2f}%",
                     f"{c['volatilidade']:.2f}%", f"{c['rsi']:.0f}"])
    t = Table(rows, colWidths=[2*cm,4.5*cm,2.5*cm,2*cm,2.5*cm,2.5*cm,1.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a56db")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f8f9fa"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#ddd")),
        ("ALIGN",(2,0),(-1,-1),"CENTER"),
        ("PADDING",(0,0),(-1,-1),4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))
    if correlacoes:
        story.append(Paragraph("Correlações do Mercado", h2))
        for nome, dados in correlacoes.items():
            s = "▲" if dados["variacao"] > 0 else "▼"
            story.append(Paragraph(f"{nome}: {s} {dados['variacao']:+.2f}% (atual: {dados['atual']:,.2f})", body))
    story.append(Paragraph("Análise de Mercado — IA", h2))
    for linha in re.sub(r'[#*`]','', relatorio["analise"]).split("\n"):
        if linha.strip(): story.append(Paragraph(linha.strip(), body))
    story.append(Paragraph("Recomendações — IA", h2))
    for linha in re.sub(r'[#*`]','', relatorio["recomendacoes"]).split("\n"):
        if linha.strip(): story.append(Paragraph(linha.strip(), body))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ccc")))
    story.append(Paragraph("⚠️ Relatório informativo. Não é consultoria financeira oficial.", sm))
    story.append(Paragraph("Dados: Yahoo Finance · IA: Groq LLaMA 3.3 70B", sm))
    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# ENVIOS
# ══════════════════════════════════════════════════════════════

def enviar_telegram(token, chat_id, cotacoes, relatorio, pdf_bytes):
    try:
        base  = f"https://api.telegram.org/bot{token}"
        emoji = lambda v: "🟢" if v > 0 else "🔴"
        linhas = [f"📈 *Analista B3 — {relatorio['gerado_em']}*\n"]
        for c in cotacoes:
            linhas.append(f"{emoji(c['variacao'])} *{c['ticker']}* {c['variacao']:+.2f}%")
        linhas.append(f"\n📊 *Análise:*\n{relatorio['analise'][:500]}...")
        requests.post(f"{base}/sendMessage", json={"chat_id": chat_id, "text": "\n".join(linhas), "parse_mode": "Markdown"}, timeout=15)
        requests.post(f"{base}/sendDocument",
                      files={"document": (f"relatorio_b3_{datetime.now().strftime('%Y%m%d')}.pdf", pdf_bytes, "application/pdf")},
                      data={"chat_id": chat_id, "caption": "📄 Relatório completo em PDF"}, timeout=30)
        return True
    except Exception as e:
        return str(e)


def enviar_email(remetente, senha, destinatario, cotacoes, relatorio, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg["From"]    = remetente
        msg["To"]      = destinatario
        msg["Subject"] = f"📊 Carteira Inteligente — Relatório Semanal — {relatorio['gerado_em']}"
        emoji = lambda v: "🟢" if v > 0 else "🔴"
        html = [f"<h2>📊 Carteira Inteligente — {relatorio['gerado_em']}</h2><hr>"]
        for c in cotacoes:
            cor = "#22c55e" if c["variacao"] > 0 else "#ef4444"
            html.append(f'<p>{emoji(c["variacao"])} <b>{c["ticker"]}</b>: <span style="color:{cor}">{c["variacao"]:+.2f}%</span></p>')
        html.append(f"<hr><h3>Análise</h3><p>{relatorio['analise'][:800]}...</p>")
        html.append("<p style='color:#666;font-size:12px'>⚠️ Relatório informativo. Não é consultoria financeira.</p>")
        msg.attach(MIMEText("\n".join(html), "html"))
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=relatorio_b3_{datetime.now().strftime('%Y%m%d')}.pdf")
        msg.attach(part)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        return True
    except Exception as e:
        return str(e)


# ══════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════

def grafico_barras(cotacoes):
    df = pd.DataFrame(cotacoes)
    fig = go.Figure(go.Bar(
        x=df["ticker"], y=df["variacao"],
        marker_color=["#0f7b3e" if v > 0 else "#c0392b" for v in df["variacao"]],
        text=[f"{v:+.1f}%" for v in df["variacao"]],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=12, color="white", family="IBM Plex Sans"),
        width=0.6,
    ))
    fig.update_layout(title=dict(text="Variação Semanal (%)", font=dict(family="Syne", size=16, color="#7eb8f7")),
                      plot_bgcolor="#ffffff", paper_bgcolor="#f4f5f7", font=dict(color="#1a1d23"),
                      xaxis=dict(gridcolor="#e5e7eb"), yaxis=dict(gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#9ca3af"),
                      margin=dict(t=50, b=10, l=10, r=10), height=360)
    return fig


def grafico_setores(cotacoes):
    setores = {}
    for c in cotacoes:
        setores.setdefault(c["setor"], []).append(c["variacao"])
    dados = sorted([{"setor": s, "media": round(sum(v)/len(v), 2)} for s, v in setores.items()], key=lambda x: x["media"], reverse=True)
    df = pd.DataFrame(dados)
    fig = go.Figure(go.Bar(y=df["setor"], x=df["media"], orientation="h",
                           marker_color=["#22c55e" if v > 0 else "#ef4444" for v in df["media"]],
                           text=[f"{v:+.2f}%" for v in df["media"]], textposition="outside",
                           textfont=dict(size=11, color="#1a1d23")))
    fig.update_layout(title=dict(text="Desempenho por Setor (%)", font=dict(family="Syne", size=16, color="#7eb8f7")),
                      plot_bgcolor="#ffffff", paper_bgcolor="#f4f5f7", font=dict(color="#1a1d23"),
                      xaxis=dict(gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#9ca3af"),
                      yaxis=dict(gridcolor="rgba(0,0,0,0)"), margin=dict(t=50, b=10, l=10, r=80), height=360)
    return fig


def grafico_linha(historico, ticker):
    df  = pd.DataFrame(historico)
    cor = "#22c55e" if df["preco"].iloc[-1] >= df["preco"].iloc[0] else "#ef4444"
    fig = go.Figure(go.Scatter(x=df["data"], y=df["preco"], mode="lines+markers",
                               line=dict(color=cor, width=2.5), marker=dict(size=6, color=cor)))
    fig.update_layout(title=dict(text=f"Evolução — {ticker}", font=dict(family="Syne", size=14, color="#7eb8f7")),
                      plot_bgcolor="#ffffff", paper_bgcolor="#f4f5f7", font=dict(color="#1a1d23"),
                      xaxis=dict(gridcolor="#e5e7eb"), yaxis=dict(gridcolor="#e5e7eb"),
                      margin=dict(t=40, b=10, l=10, r=10), height=260, showlegend=False)
    return fig


def grafico_heatmap(cotacoes):
    tickers = [c["ticker"] for c in cotacoes]
    valores = [c["variacao"] for c in cotacoes]
    fig = go.Figure(go.Treemap(
        labels=[f"{t}<br>{v:+.2f}%" for t, v in zip(tickers, valores)],
        parents=[""] * len(tickers),
        values=[abs(v) + 0.5 for v in valores],
        marker=dict(colors=valores, colorscale=[[0,"#ef4444"],[0.5,"#1e3a5f"],[1,"#22c55e"]], cmid=0, showscale=False),
        textfont=dict(size=13, color="white", family="IBM Plex Sans"),
    ))
    fig.update_layout(title=dict(text="Heatmap da Carteira", font=dict(family="Syne", size=16, color="#7eb8f7")),
                      paper_bgcolor="#f4f5f7", margin=dict(t=50, b=10, l=10, r=10), height=320)
    return fig


def grafico_comparativo(cotacoes):
    df = pd.DataFrame(cotacoes)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Esta Semana", x=df["ticker"], y=df["variacao"],
                         marker_color=["#22c55e" if v > 0 else "#ef4444" for v in df["variacao"]]))
    fig.add_trace(go.Bar(name="Semana Anterior", x=df["ticker"], y=df["var_anterior"],
                         marker_color=["#1a56db" if v > 0 else "#7c3aed" for v in df["var_anterior"]], opacity=0.7))
    fig.update_layout(title=dict(text="Semana Atual vs Anterior (%)", font=dict(family="Syne", size=16, color="#7eb8f7")),
                      plot_bgcolor="#ffffff", paper_bgcolor="#f4f5f7", font=dict(color="#1a1d23"),
                      barmode="group", xaxis=dict(gridcolor="#e5e7eb"),
                      yaxis=dict(gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#9ca3af"),
                      margin=dict(t=50, b=10, l=10, r=10), height=360,
                      legend=dict(bgcolor="#ffffff", bordercolor="#e2e5ea"))
    return fig


def grafico_correlacao(correlacoes):
    nomes  = list(correlacoes.keys())
    variac = [correlacoes[n]["variacao"] for n in nomes]
    fig = go.Figure(go.Bar(
        x=nomes, y=variac,
        marker_color=["#0f7b3e" if v > 0 else "#c0392b" for v in variac],
        text=[f"{v:+.2f}%" for v in variac],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=14, color="white", family="IBM Plex Sans"),
        width=0.5,
    ))
    fig.update_layout(
        title=dict(text="IBOV · Dólar · BTC na Semana (%)", font=dict(family="Playfair Display", size=16, color="#1a1d23")),
        plot_bgcolor="#ffffff", paper_bgcolor="#f4f5f7", font=dict(color="#1a1d23"),
        xaxis=dict(gridcolor="#e5e7eb", tickfont=dict(size=13, color="#1a1d23")),
        yaxis=dict(gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#374151", zerolinewidth=2),
        margin=dict(t=50, b=10, l=10, r=10), height=320,
    )
    return fig


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
groq_key = os.getenv("GROQ_API_KEY", "")

with st.sidebar:
    st.markdown("## 📊 Carteira Inteligente")
    st.markdown("Painel semanal gerado por IA.")
    gerar = st.button("🚀 Gerar Relatório Completo")
    st.markdown("---")
    st.markdown("### 📬 Enviar Relatório")
    with st.expander("📨 Telegram"):
        tg_token   = st.text_input("Token do Bot", type="password", key="tg_token", placeholder="123456:ABC...")
        tg_chat_id = st.text_input("Chat ID", key="tg_chat", placeholder="-100123456")
        enviar_tg  = st.button("Enviar pelo Telegram")
    with st.expander("📧 E-mail (Gmail)"):
        email_rem  = st.text_input("Seu Gmail", key="email_rem", placeholder="seu@gmail.com")
        email_sen  = st.text_input("Senha de App", type="password", key="email_sen")
        email_dest = st.text_input("Destinatário", key="email_dest", placeholder="cliente@email.com")
        enviar_em  = st.button("Enviar por E-mail")
    st.markdown("""
    <div style='font-size:0.75rem; color:#3a5070; margin-top:16px; line-height:1.7'>
    ⚠️ Relatório informativo.<br>
    📊 Yahoo Finance · 🤖 Groq LLaMA 3.3
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PRINCIPAL
# ══════════════════════════════════════════════════════════════
st.markdown('''<div class="hero-wrap">
    <div class="hero-ticker">▪ PAINEL DE INVESTIMENTOS ▪ DADOS EM TEMPO REAL ▪ IA GENERATIVA</div>
    <div class="hero-title">Carteira Inteligente</div>
    <div class="hero-sub">Relatório semanal completo — cotações, sentimento, risco, correlações e análise por IA</div>
</div>''', unsafe_allow_html=True)

for key in ["cotacoes","relatorio","dividendos","correlacoes","pdf_bytes","resultados_trim","avaliacao_resultados"]:
    if key not in st.session_state: st.session_state[key] = None
if "sentimentos" not in st.session_state: st.session_state.sentimentos = {}

if not gerar and st.session_state.cotacoes is None:
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown('<div class="metric-card"><div class="metric-value">7</div><div class="metric-label">Ativos monitorados</div></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="metric-card"><div class="metric-value">📰</div><div class="metric-label">Sentimento IA</div></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="metric-card"><div class="metric-value">📊</div><div class="metric-label">Análise de Risco</div></div>', unsafe_allow_html=True)
    with col4: st.markdown('<div class="metric-card"><div class="metric-value">🔗</div><div class="metric-label">Correlações</div></div>', unsafe_allow_html=True)
    st.info("👈 Clique em **Gerar Relatório Completo** para começar.")

if gerar:
    if not groq_key:
        st.error("❌ Chave do Groq não configurada.")
        st.stop()
    with st.status("📊 Coletando dados completos...", expanded=True) as status:
        st.write("📈 Buscando cotações, RSI e volatilidade...")
        cotacoes = buscar_cotacoes()
        if not cotacoes:
            st.error("❌ Nenhuma cotação retornada.")
            st.stop()
        st.session_state.cotacoes = cotacoes
        st.write(f"✅ {len(cotacoes)} ativos coletados!")
        st.write("🔗 Buscando correlações...")
        correlacoes = buscar_correlacoes()
        st.session_state.correlacoes = correlacoes
        st.write("✅ Correlações coletadas!")
        st.write("💰 Buscando dividendos...")
        dividendos = buscar_dividendos()
        st.session_state.dividendos = dividendos
        st.write(f"✅ {len(dividendos)} registros de dividendos!")
        st.write("🤖 Gerando análise com IA (aguarde ~2 minutos)...")
        relatorio = gerar_relatorio_ia(cotacoes, correlacoes, groq_key)
        st.session_state.relatorio = relatorio
        st.write("📄 Gerando PDF...")
        pdf_bytes = gerar_pdf(cotacoes, relatorio, correlacoes)
        st.session_state.pdf_bytes = pdf_bytes
        st.write("📅 Buscando calendário de resultados...")
        resultados_trim = buscar_resultados()
        st.session_state.resultados_trim = resultados_trim
        st.write(f"✅ {len(resultados_trim)} empresas com dados de resultados!")
        st.write("📊 Avaliando resultados com IA...")
        avaliacao = avaliar_resultados_ia(resultados_trim, groq_key)
        st.session_state.avaliacao_resultados = avaliacao
        st.session_state.sentimentos = {}
        status.update(label="✅ Relatório completo gerado!", state="complete")

# ══════════════════════════════════════════════════════════════
# EXIBIÇÃO
# ══════════════════════════════════════════════════════════════
if st.session_state.cotacoes:
    cotacoes           = st.session_state.cotacoes
    relatorio          = st.session_state.relatorio
    dividendos         = st.session_state.dividendos or []
    correlacoes        = st.session_state.correlacoes or {}
    pdf_bytes          = st.session_state.pdf_bytes
    resultados_trim    = st.session_state.resultados_trim or []
    avaliacao_resultados = st.session_state.avaliacao_resultados or ""

    positivas  = sum(1 for c in cotacoes if c["variacao"] > 0)
    negativas  = sum(1 for c in cotacoes if c["variacao"] < 0)
    media      = round(sum(c["variacao"] for c in cotacoes) / len(cotacoes), 2)
    melhor     = max(cotacoes, key=lambda x: x["variacao"])
    pior       = min(cotacoes, key=lambda x: x["variacao"])
    vol_media  = round(sum(c["volatilidade"] for c in cotacoes) / len(cotacoes), 2)
    vol_label  = "🟢 Calma" if vol_media < 1 else ("🟡 Moderada" if vol_media < 2.5 else "🔴 Volátil")

    # Métricas
    st.markdown('<div class="section-header">Resumo da Semana</div>', unsafe_allow_html=True)
    col1,col2,col3,col4,col5,col6 = st.columns(6)
    cor = "positive" if media > 0 else "negative"
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-value {cor}">{media:+.2f}%</div><div class="metric-label">Variação média</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-value positive">{positivas}</div><div class="metric-label">Em alta</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-value negative">{negativas}</div><div class="metric-label">Em baixa</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div class="metric-value positive">+{melhor["variacao"]:.2f}%</div><div class="metric-label">Maior alta · {melhor["ticker"]}</div></div>', unsafe_allow_html=True)
    with col5: st.markdown(f'<div class="metric-card"><div class="metric-value negative">{pior["variacao"]:.2f}%</div><div class="metric-label">Maior queda · {pior["ticker"]}</div></div>', unsafe_allow_html=True)
    with col6: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1a1d23">{vol_label}</div><div class="metric-label">Volatilidade geral</div></div>', unsafe_allow_html=True)

    # Heatmap
    st.markdown('<div class="section-header">🟥 Heatmap da Carteira</div>', unsafe_allow_html=True)
    st.plotly_chart(grafico_heatmap(cotacoes), use_container_width=True)

    # Gráficos
    st.markdown('<div class="section-header">Gráficos de Desempenho</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: st.plotly_chart(grafico_barras(cotacoes), use_container_width=True)
    with c2: st.plotly_chart(grafico_setores(cotacoes), use_container_width=True)

    # Comparativo
    st.markdown('<div class="section-header">📅 Semana Atual vs Anterior</div>', unsafe_allow_html=True)
    st.plotly_chart(grafico_comparativo(cotacoes), use_container_width=True)

    # Correlações
    if correlacoes:
        st.markdown('<div class="section-header">🔗 Correlações do Mercado</div>', unsafe_allow_html=True)
        st.plotly_chart(grafico_correlacao(correlacoes), use_container_width=True)
        cols = st.columns(3)
        for i, (nome, dados) in enumerate(correlacoes.items()):
            cor = "positive" if dados["variacao"] > 0 else "negative"
            emoji = "📈" if dados["variacao"] > 0 else "📉"
            with cols[i]: st.markdown(f'<div class="metric-card"><div class="metric-value {cor}">{dados["variacao"]:+.2f}%</div><div class="metric-label">{emoji} {nome} na semana</div></div>', unsafe_allow_html=True)

    # Tabela
    st.markdown('<div class="section-header">Cotações Detalhadas</div>', unsafe_allow_html=True)
    def fmt(c, campo):
        v = c[campo]
        return f"US$ {v:,.0f}" if c["ticker_sa"] == "BTC-USD" else f"R$ {v:.2f}"

    df_tab = pd.DataFrame([{
        "Ticker": c["ticker"], "Empresa": c["nome"], "Setor": c["setor"],
        "Atual": fmt(c,"atual"), "Variação": f"{c['variacao']:+.2f}%",
        "Sem. Ant.": f"{c['var_anterior']:+.2f}%", "Volatilidade": f"{c['volatilidade']:.2f}%",
        "Maior Queda": f"{c['maior_queda']:.2f}%", "RSI": f"{c['rsi']:.0f}",
    } for c in cotacoes])
    st.dataframe(df_tab, use_container_width=True, hide_index=True)

    # RSI
    st.markdown('<div class="section-header">⚡ RSI — Momento dos Ativos</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    for i, c in enumerate(cotacoes):
        rsi = c["rsi"]
        if rsi >= 70:   status_rsi, cor_rsi = "🔴 Sobrecomprado", "#ef4444"
        elif rsi <= 30: status_rsi, cor_rsi = "🟢 Sobrevendido",  "#22c55e"
        else:           status_rsi, cor_rsi = "🟡 Neutro",        "#eab308"
        card = f'<div class="rsi-box"><strong style="color:#1a1d23; font-size:0.95rem">{c["ticker"]}</strong> <span style="color:#6b7280">— {c["nome"]}</span><br><span style="color:{cor_rsi}; font-size:1.1rem; font-weight:700">RSI {rsi}</span> &nbsp;·&nbsp; <span style="color:#94a3b8">{status_rsi}</span></div>'
        with (c1 if i % 2 == 0 else c2): st.markdown(card, unsafe_allow_html=True)

    # Fundamentalistas + Preço-Alvo
    st.markdown('<div class="section-header">📊 Indicadores Fundamentalistas & Preço-Alvo</div>', unsafe_allow_html=True)
    ticker_fund = st.selectbox("Selecione o ativo:", [c["ticker"] for c in cotacoes], key="fund")
    acao_fund   = next(c for c in cotacoes if c["ticker"] == ticker_fund)
    with st.spinner("Buscando indicadores..."):
        fund = buscar_fundamentals(acao_fund["ticker_sa"]) if acao_fund["ticker_sa"] != "BTC-USD" else {"pl":0,"pvp":0,"dy":0,"market_cap":0,"roe":0,"divida_pl":0,"preco_alvo":0,"preco_alvo_min":0,"preco_alvo_max":0,"recomendacao":"N/D"}

    col1,col2,col3,col4,col5,col6 = st.columns(6)
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1a1d23">{fund["pl"]:.1f}x</div><div class="metric-label">P/L</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1a1d23">{fund["pvp"]:.1f}x</div><div class="metric-label">P/VP</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-value positive">{fund["dy"]:.1f}%</div><div class="metric-label">Div. Yield</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1a1d23">{fund["roe"]:.1f}%</div><div class="metric-label">ROE</div></div>', unsafe_allow_html=True)
    with col5:
        pa     = fund["preco_alvo"]
        atual  = acao_fund["atual"]
        upside = round(((pa - atual) / atual) * 100, 1) if pa > 0 and atual > 0 else 0
        cor_pa = "positive" if upside > 0 else "negative"
        pa_str = f"R$ {pa:.2f}" if pa > 0 else "N/D"
        st.markdown(f'<div class="metric-card"><div class="metric-value {cor_pa}">{pa_str}</div><div class="metric-label">Preço-Alvo · {upside:+.1f}%</div></div>', unsafe_allow_html=True)
    with col6:
        rec = fund["recomendacao"].upper()
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1a1d23">{rec}</div><div class="metric-label">Consenso Analistas</div></div>', unsafe_allow_html=True)

    # Linha individual
    st.markdown('<div class="section-header">Evolução de Preço Individual</div>', unsafe_allow_html=True)
    ticker_sel = st.selectbox("Selecione o ativo:", [c["ticker"] for c in cotacoes], key="linha")
    acao_sel   = next(c for c in cotacoes if c["ticker"] == ticker_sel)
    if acao_sel.get("historico"):
        st.plotly_chart(grafico_linha(acao_sel["historico"], ticker_sel), use_container_width=True)

    # Calendário de Resultados
    st.markdown('<div class="section-header">📅 Calendário de Resultados Trimestrais</div>', unsafe_allow_html=True)
    if resultados_trim:
        col1, col2 = st.columns(2)
        for i, r in enumerate(resultados_trim):
            cor_rec  = "#0f7b3e" if r["var_receita"] and r["var_receita"] > 0 else ("#c0392b" if r["var_receita"] and r["var_receita"] < 0 else "#6b7280")
            cor_luc  = "#0f7b3e" if r["var_lucro"] and r["var_lucro"] > 0 else ("#c0392b" if r["var_lucro"] and r["var_lucro"] < 0 else "#6b7280")
            rec_str  = f"{r['var_receita']:+.1f}%" if r["var_receita"] is not None else "N/D"
            luc_str  = f"{r['var_lucro']:+.1f}%" if r["var_lucro"] is not None else "N/D"
            card = f'''<div style="background:#fff;border:1px solid #e2e5ea;border-left:4px solid #e8b84b;border-radius:8px;padding:14px 18px;margin:8px 0;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <strong style="color:#1a1d23;font-size:0.95rem">{r["ticker"]}</strong>
                    <span style="background:#eff6ff;color:#1e40af;border-radius:4px;padding:2px 8px;font-size:0.72rem;font-weight:600">🔜 Próximo: {r["proxima_data"]}</span>
                </div>
                <div style="color:#6b7280;font-size:0.8rem;margin-bottom:8px">{r["nome"]} · {r["setor"]}</div>
                <div style="display:flex;gap:16px;margin-bottom:6px">
                    <span style="font-size:0.82rem">Receita: <strong style="color:{cor_rec}">{rec_str}</strong></span>
                    <span style="font-size:0.82rem">Lucro: <strong style="color:{cor_luc}">{luc_str}</strong></span>
                </div>
                <div style="color:#9ca3af;font-size:0.72rem">📋 Último resultado: {r["ultimo_resultado"]}</div>
            </div>'''
            with (col1 if i % 2 == 0 else col2):
                st.markdown(card, unsafe_allow_html=True)

        if avaliacao_resultados:
            st.markdown('<div style="margin-top:16px"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-box"><strong style="font-size:1rem;color:#1a1d23">🤖 Avaliação dos Resultados por Prazo</strong><hr style="border:none;border-top:1px solid #e2e5ea;margin:12px 0">{avaliacao_resultados}</div>', unsafe_allow_html=True)
    else:
        st.info("Dados de resultados não disponíveis para esta semana.")

    # Dividendos
    st.markdown('<div class="section-header">💰 Histórico de Dividendos</div>', unsafe_allow_html=True)
    if dividendos:
        c1,c2 = st.columns(2)
        for i, div in enumerate(dividendos[:10]):
            card = f'<div class="div-card"><strong style="color:#22c55e">{div["ticker"]}</strong> — {div["nome"]}<br><span style="color:#7eb8f7; font-size:1.1rem; font-weight:700">R$ {div["valor"]:.4f}</span> &nbsp;·&nbsp; <span style="color:#4a6080; font-size:0.8rem">{div["data"]}</span></div>'
            with (c1 if i % 2 == 0 else c2): st.markdown(card, unsafe_allow_html=True)
    else:
        st.info("Nenhum dividendo encontrado.")

    # Notícias + Sentimento
    st.markdown('<div class="section-header">📰 Notícias & Análise de Sentimento</div>', unsafe_allow_html=True)
    ticker_news = st.selectbox("Selecione o ativo:", [c["ticker"] for c in cotacoes], key="news")
    acao_news   = next(c for c in cotacoes if c["ticker"] == ticker_news)
    cache_key   = acao_news["ticker"]
    badge_map   = {"Otimista":"badge-otimista","Pessimista":"badge-pessimista","Neutro":"badge-neutro"}
    emoji_map   = {"Otimista":"🟢","Pessimista":"🔴","Neutro":"🟡"}

    if cache_key not in st.session_state.sentimentos:
        with st.spinner("Buscando notícias e analisando sentimento..."):
            noticias_raw = buscar_noticias(acao_news["ticker_sa"].replace(".SA",""), acao_news["nome"])
            resultado    = analisar_sentimento(noticias_raw, acao_news["ticker"], acao_news["nome"], groq_key) if noticias_raw else {"noticias":[],"score":5.0,"sentimento_geral":"Neutro","impacto_resumo":""}
        st.session_state.sentimentos[cache_key] = resultado
    else:
        resultado = st.session_state.sentimentos[cache_key]

    noticias = resultado["noticias"]
    if noticias:
        score     = resultado["score"]
        sent_g    = resultado["sentimento_geral"]
        cor_score = "#22c55e" if score >= 7 else ("#ef4444" if score <= 4 else "#eab308")
        c1,c2 = st.columns([1,3])
        with c1:
            st.markdown(f'''<div class="score-card">
                <div class="metric-label">Score do Momento</div>
                <div class="score-value" style="color:{cor_score}">{score}/10</div>
                <div style="margin-top:8px"><span class="{badge_map.get(sent_g,'badge-neutro')}">{emoji_map.get(sent_g,'🟡')} {sent_g}</span></div>
            </div>''', unsafe_allow_html=True)
        with c2:
            if resultado["impacto_resumo"]:
                st.markdown(f'''<div class="impacto-box">
                    <div class="metric-label" style="margin-bottom:8px">📋 Resumo do Impacto</div>
                    <div style="color:#374151; line-height:1.7">{resultado["impacto_resumo"]}</div>
                </div>''', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for n in noticias:
            sent  = n.get("sentimento","Neutro")
            prazo = n.get("prazo","Curto")
            p_cls = "badge-curto" if prazo == "Curto" else "badge-longo"
            p_emo = "⚡" if prazo == "Curto" else "📅"
            st.markdown(f'''<div class="news-card">
                <div style="margin-bottom:6px">
                    <span class="{badge_map.get(sent,'badge-neutro')}">{emoji_map.get(sent,'🟡')} {sent}</span>
                    &nbsp;<span class="{p_cls}">{p_emo} {prazo} Prazo</span>
                </div>
                <div style="font-weight:600; font-size:0.9rem"><a href="{n['link']}" target="_blank" style="color:#1e40af; text-decoration:none">{n['titulo']}</a></div>
                <div style="font-size:0.75rem; color:#4a6080; margin-top:4px">📰 {n['fonte']} · {n['data']}</div>
            </div>''', unsafe_allow_html=True)

        # Score da carteira
        if len(st.session_state.sentimentos) > 1:
            scores = [v["score"] for v in st.session_state.sentimentos.values()]
            sc     = round(sum(scores)/len(scores), 1)
            cor_c  = "#22c55e" if sc >= 7 else ("#ef4444" if sc <= 4 else "#eab308")
            momento = "Momento Positivo 🚀" if sc >= 6 else "Momento de Cautela ⚠️"
            st.markdown('<div class="section-header">🏆 Score Geral da Carteira</div>', unsafe_allow_html=True)
            st.markdown(f'''<div class="score-card" style="max-width:300px">
                <div class="metric-label">Score da Carteira</div>
                <div class="score-value" style="color:{cor_c}">{sc}/10</div>
                <div style="margin-top:8px; color:#374151; font-weight:600">{momento}</div>
                <div style="margin-top:4px; color:#9ca3af; font-size:0.75rem">Baseado em {len(scores)} ativo(s)</div>
            </div>''', unsafe_allow_html=True)
    else:
        st.info("Nenhuma notícia encontrada para este ativo.")

    # Análise IA
    if relatorio:
        st.markdown('<div class="section-header">🤖 Análise de Mercado — IA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-box">{relatorio["analise"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">💼 Recomendações & Cenários — IA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-box">{relatorio["recomendacoes"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:right;color:#9ca3af;font-size:0.78rem;margin-top:16px">Gerado em {relatorio["gerado_em"]} · Yahoo Finance · Groq LLaMA 3.3</div>', unsafe_allow_html=True)

        # Downloads
        st.markdown('<div class="section-header">⬇️ Downloads & Envios</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            md = f"# Relatório Semanal B3\n**Gerado em:** {relatorio['gerado_em']}\n\n---\n\n## Análise\n{relatorio['analise']}\n\n---\n\n## Recomendações\n{relatorio['recomendacoes']}\n\n---\n*Relatório gerado por IA. Não é consultoria financeira.*"
            st.download_button("⬇️ Baixar em Markdown", data=md, file_name=f"relatorio_b3_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")
        with c2:
            if pdf_bytes:
                st.download_button("📄 Baixar em PDF", data=pdf_bytes, file_name=f"relatorio_b3_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")

    # Telegram
    if enviar_tg and relatorio and pdf_bytes:
        if tg_token and tg_chat_id:
            with st.spinner("Enviando pelo Telegram..."):
                res = enviar_telegram(tg_token, tg_chat_id, cotacoes, relatorio, pdf_bytes)
            st.success("✅ Enviado pelo Telegram!") if res is True else st.error(f"❌ Erro: {res}")
        else:
            st.warning("Configure o Token e Chat ID na barra lateral.")

    # E-mail
    if enviar_em and relatorio and pdf_bytes:
        if email_rem and email_sen and email_dest:
            with st.spinner("Enviando e-mail..."):
                res = enviar_email(email_rem, email_sen, email_dest, cotacoes, relatorio, pdf_bytes)
            st.success("✅ E-mail enviado!") if res is True else st.error(f"❌ Erro: {res}")
        else:
            st.warning("Preencha Gmail, senha de app e destinatário.")
