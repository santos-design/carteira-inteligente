# 📊 Carteira Inteligente

> Plataforma de análise semanal de carteira de investimentos com Inteligência Artificial, dados reais da B3, Bitcoin, correlações de mercado e alertas automáticos.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41+-red?style=flat-square&logo=streamlit)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-purple?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🚀 Sobre o Projeto

**Carteira Inteligente** é uma aplicação web que gera relatórios semanais completos sobre uma carteira de investimentos da B3 com um único clique. O sistema coleta dados reais do mercado, analisa correlações macroeconômicas, avalia sentimento de notícias com IA, calcula indicadores de risco e entrega tudo em um relatório profissional em PDF — enviado automaticamente via Telegram ou e-mail.

---

## ✨ O que o sistema faz

### 📈 Cotações & Mercado
- Cotações semanais em tempo real de 6 ações da B3 + Bitcoin
- Heatmap visual da carteira (verde/vermelho por variação)
- Gráfico de variação semanal por ação e por setor
- Comparativo semana atual vs semana anterior
- Tabela com abertura, atual, máxima, mínima, volatilidade e maior queda

### 🔗 Correlações Macroeconômicas
- IBOV — performance do índice brasileiro vs carteira
- Dólar — impacto da variação cambial nos ativos
- Bitcoin — performance isolada e correlação com o mercado

### ⚡ Análise de Risco
- Volatilidade semanal classificada: 🟢 Calma / 🟡 Moderada / 🔴 Volátil
- Maior queda do período por ativo
- RSI por ativo: Sobrecomprado / Neutro / Sobrevendido

### 📊 Indicadores Fundamentalistas & Projeções
- P/L, P/VP, Dividend Yield, ROE, Market Cap
- Preço-alvo médio dos analistas com % de upside/downside
- Consenso de mercado: Buy / Hold / Sell

### 📅 Calendário de Resultados Trimestrais
- Data do próximo resultado de cada empresa
- Data do último resultado já divulgado
- Variação de Receita e Lucro vs trimestre anterior
- Avaliação da IA: impacto no **Curto / Médio / Longo Prazo**

### 💰 Dividendos
- Histórico dos últimos pagamentos de proventos de cada ativo

### 📰 Notícias & Sentimento IA
- Notícias recentes por ativo via Yahoo Finance
- Badge de sentimento: 🟢 Otimista / 🔴 Pessimista / 🟡 Neutro
- Tag de impacto: ⚡ Curto Prazo / 📅 Longo Prazo
- Score do momento por ativo (0–10)
- Score geral da carteira com diagnóstico

### 🤖 Análise por IA (Multi-Agente CrewAI)
- **Agente 1 — Analista CNPI:** panorama, altas, baixas, impacto do dólar e BTC, perspectivas
- **Agente 2 — Consultor CFP/CEA:** recomendações por perfil conservador/moderado/arrojado + cenários otimista e pessimista

### 📄 Entrega & Alertas
- Download em **PDF** formatado profissionalmente
- Download em **Markdown**
- Envio automático pelo **Telegram Bot** com PDF em anexo
- Envio automático por **E-mail Gmail** com PDF em anexo

---

## 🛠️ Tecnologias

| Tecnologia | Função |
|---|---|
| [Streamlit](https://streamlit.io) | Interface web |
| [CrewAI](https://crewai.com) | Orquestração de agentes IA |
| [Groq](https://groq.com) | LLM (LLaMA 3.3 70B) |
| [yfinance](https://pypi.org/project/yfinance/) | Dados de mercado |
| [Plotly](https://plotly.com) | Gráficos interativos |
| [ReportLab](https://www.reportlab.com) | Geração de PDF |
| [python-telegram-bot](https://python-telegram-bot.org) | Envio Telegram |
| [NumPy](https://numpy.org) | RSI e volatilidade |

---

## 📦 Instalação Local

### Pré-requisitos
- Python 3.10+
- Chave Groq API gratuita em [console.groq.com](https://console.groq.com)

```bash
# 1. Clone o repositório
git clone https://github.com/seuusuario/carteira-inteligente.git
cd carteira-inteligente

# 2. Crie o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure a chave do Groq
echo 'GROQ_API_KEY=sua_chave_aqui' > .env

# 5. Execute o app
streamlit run app_mercado_b3.py
```

Acesse em: `http://localhost:8501`

---

## ☁️ Deploy no Streamlit Cloud (gratuito)

1. Faça fork deste repositório no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte o repositório
3. Em **Advanced Settings → Secrets**, adicione:
```toml
GROQ_API_KEY = "sua_chave_aqui"
```
4. Clique em **Deploy** — link público gerado automaticamente!

---

## 📬 Configurar Telegram Bot

1. No Telegram, fale com [@BotFather](https://t.me/botfather) → `/newbot`
2. Copie o **Token** gerado
3. Fale com [@userinfobot](https://t.me/userinfobot) para obter seu **Chat ID**
4. Cole os dois na barra lateral do app e clique em **Enviar pelo Telegram**

---

## 📧 Configurar E-mail Gmail

1. Acesse [myaccount.google.com](https://myaccount.google.com) → Segurança → **Senhas de app**
2. Gere uma senha de app para "Mail"
3. Use essa senha (não a senha normal) no campo da barra lateral

---

## 🤖 Arquitetura de IA

```
Dados do Mercado (yfinance)
         ↓
  ┌─────────────────────────┐
  │  Agente 1: Analista CNPI │
  │  Panorama + Correlações  │
  │  Altas, Baixas, Setores  │
  └──────────┬──────────────┘
             ↓
  ┌──────────────────────────────┐
  │  Agente 2: Consultor CFP/CEA  │
  │  Recomendações por perfil     │
  │  Cenários otimista/pessimista │
  └──────────┬───────────────────┘
             ↓
  ┌──────────────────────────────┐
  │  Agente 3: Sentimento        │
  │  Score por notícia            │
  │  Impacto curto/longo prazo   │
  └──────────┬───────────────────┘
             ↓
  ┌──────────────────────────────┐
  │  Agente 4: Resultados        │
  │  Avaliação trimestral        │
  │  Impacto curto/médio/longo   │
  └──────────┬───────────────────┘
             ↓
    PDF + Telegram + E-mail
```

---

## 📊 Carteira Monitorada

| Ticker | Empresa | Setor |
|--------|---------|-------|
| CXSE3 | Caixa Seguridade | Seguros & Financeiro |
| RANI3 | Irani | Papel & Embalagens |
| TAEE3 | Taesa | Energia Elétrica |
| CSAN3 | Cosan | Energia & Logística |
| BBAS3 | Banco do Brasil | Financeiro |
| PETR3 | Petrobras | Petróleo & Gás |
| BTC | Bitcoin | Criptomoeda |

---

## ⚠️ Disclaimer

Projeto desenvolvido para fins **educacionais e de portfólio**. Os relatórios gerados pela IA não constituem consultoria financeira oficial. Sempre consulte um profissional certificado antes de tomar decisões de investimento.

---

<div align="center">
Desenvolvido com ❤️ usando Python, CrewAI e Groq LLaMA 3.3
</div>
