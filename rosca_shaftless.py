import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Rosca Shaftless · Dimensionamento",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CSS CUSTOMIZADO
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
  }

  /* Fundo geral */
  .stApp {
    background: #0d1117;
    color: #e6edf3;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
  }

  /* Título principal */
  .main-title {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #f0b429;
    letter-spacing: -1px;
    margin-bottom: 0;
  }
  .main-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #8b949e;
    margin-bottom: 2rem;
    font-weight: 300;
  }

  /* Cards de resultado */
  .result-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
  }
  .result-card.highlight {
    border-color: #f0b429;
    background: #1c2027;
  }
  .card-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #8b949e;
    font-family: 'Space Mono', monospace;
  }
  .card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f0b429;
    font-family: 'Space Mono', monospace;
    line-height: 1.2;
  }
  .card-unit {
    font-size: 0.9rem;
    color: #8b949e;
    margin-left: 4px;
  }
  .card-sub {
    font-size: 0.8rem;
    color: #6e7681;
    margin-top: 2px;
  }

  /* Badge de alerta */
  .badge-ok   { color: #3fb950; font-weight: 600; }
  .badge-warn { color: #d29922; font-weight: 600; }
  .badge-err  { color: #f85149; font-weight: 600; }

  /* Seção */
  .section-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #8b949e;
    border-bottom: 1px solid #30363d;
    padding-bottom: 6px;
    margin: 1.5rem 0 1rem;
  }

  /* Slider label */
  .stSlider > label { color: #c9d1d9 !important; font-size: 0.85rem; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #161b22;
    border-radius: 8px;
    padding: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
    color: #8b949e;
    background: transparent;
    border-radius: 6px;
    padding: 6px 16px;
  }
  .stTabs [aria-selected="true"] {
    background: #f0b429 !important;
    color: #0d1117 !important;
    font-weight: 700;
  }

  /* Divider */
  hr { border-color: #30363d; }

  /* Metric override */
  [data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 0.8rem 1rem;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FUNÇÕES DE CÁLCULO
# ─────────────────────────────────────────────

def calcular_velocidade_critica(D_m):
    """Velocidade crítica em rpm (D em metros)."""
    return 45 / math.sqrt(D_m)

def calcular_vazao(D_m, P_m, n_rpm, lamb, rho_t_m3):
    """Vazão em t/h."""
    area = math.pi * D_m**2 / 4
    Q = area * P_m * n_rpm * lamb * rho_t_m3 * 60
    return Q

def calcular_potencia(Q_t_h, L_m, H_m, Cf):
    """Potência em kW (horizontal + inclinação)."""
    P_hor = (Q_t_h * L_m * Cf) / 367
    P_inc = (Q_t_h * H_m) / 367
    return P_hor, P_inc, P_hor + P_inc

def calcular_torque(P_kw, n_rpm):
    """Torque em N·m."""
    if n_rpm == 0:
        return 0
    return (P_kw * 1000 * 60) / (2 * math.pi * n_rpm)

def motor_recomendado(P_total):
    """Seleciona potência padrão de motor (kW)."""
    serie = [0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5,
             11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160]
    margem = P_total * 1.25
    for p in serie:
        if p >= margem:
            return p
    return serie[-1]

def fator_inclinacao(angulo_graus):
    """Fator de correção para inclinação."""
    ang = angulo_graus
    if ang <= 5:   return 1.0
    elif ang <= 10: return 1.06
    elif ang <= 15: return 1.15
    elif ang <= 20: return 1.28
    elif ang <= 25: return 1.38
    elif ang <= 30: return 1.45
    else:           return 1.6

def verificar_deflexao(D_m, L_m, espessura_fita_mm=10):
    """Estimativa simples de deflexão do espiral shaftless (mm)."""
    # Simplificado: espiral como viga contínua com carga distribuída
    # Retorna status qualitativo
    relacao = L_m / D_m
    if relacao <= 15:   return "✅ OK", "ok"
    elif relacao <= 25: return "⚠️ Verificar", "warn"
    else:               return "❌ Suporte intermediário necessário", "err"

def calcular_barras_desgaste(D_m, L_m, esp_barra_mm, largura_barra_mm, material_barra):
    """Calcula parâmetros das barras de desgaste de aco."""
    perimetro_calha = math.pi * D_m
    espac_tipico    = largura_barra_mm / 1000 * 1.5
    n_barras_circ   = max(1, int(perimetro_calha / espac_tipico))
    n_barras_axial  = max(1, int(L_m / espac_tipico))
    n_barras        = n_barras_circ * n_barras_axial
    dens = 7.85
    vol_barra = (esp_barra_mm/1000) * (largura_barra_mm/1000) * espac_tipico
    peso_total = n_barras * vol_barra * dens * 1000
    folga_diametral = esp_barra_mm * 2
    vida_base = {"SAE 1045": 2000, "SAE 4140": 3500, "Hardox 400": 6000, "Hardox 500": 10000}
    vida_estimada = vida_base.get(material_barra, 4000)
    return n_barras, peso_total, folga_diametral, vida_estimada

def cf_corrigido_barras(Cf_base, material_barra):
    """Barras de aco tem atrito maior que liner polimerico - corrige Cf."""
    fatores = {"SAE 1045": 1.15, "SAE 4140": 1.12, "Hardox 400": 1.10, "Hardox 500": 1.08}
    return Cf_base * fatores.get(material_barra, 1.12)


# ─────────────────────────────────────────────
#  SIDEBAR — PARÂMETROS DE ENTRADA
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-title">⚙️ Parâmetros</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Material</div>', unsafe_allow_html=True)

    material_preset = st.selectbox(
        "Preset de material",
        ["Personalizado", "Lodo desidratado", "Biomassa / Bagaço", "Grãos secos", "Farinha / Pó", "Resíduo sólido urbano"]
    )

    presets = {
        "Lodo desidratado":       {"rho": 1.0, "Cf": 3.5, "lamb": 0.30},
        "Biomassa / Bagaço":      {"rho": 0.3, "Cf": 2.5, "lamb": 0.35},
        "Grãos secos":            {"rho": 0.7, "Cf": 1.4, "lamb": 0.40},
        "Farinha / Pó":           {"rho": 0.5, "Cf": 1.8, "lamb": 0.32},
        "Resíduo sólido urbano":  {"rho": 0.4, "Cf": 4.0, "lamb": 0.25},
    }

    if material_preset != "Personalizado":
        p = presets[material_preset]
        def_rho, def_Cf, def_lamb = p["rho"], p["Cf"], p["lamb"]
    else:
        def_rho, def_Cf, def_lamb = 0.8, 2.5, 0.35

    rho = st.slider("Densidade aparente (t/m³)", 0.1, 2.0, def_rho, 0.05)
    Cf  = st.slider("Fator de resistência Cf", 1.0, 5.0, def_Cf, 0.1,
                    help="1.2–2.0 = material seco leve | 2.5–4.0 = lodo/pastoso | 4.0+ = abrasivo pesado")
    lamb = st.slider("Fator de enchimento λ", 0.15, 0.50, def_lamb, 0.01,
                     help="Shaftless: tipicamente 0.25–0.40")

    st.markdown('<div class="section-header">Geometria</div>', unsafe_allow_html=True)

    D_mm = st.select_slider(
        "Diâmetro do espiral D (mm)",
        options=[150, 200, 250, 300, 350, 400, 450, 500, 600],
        value=300
    )
    D_m = D_mm / 1000

    passo_rel = st.slider("Relação passo/diâmetro (P/D)", 0.5, 1.2, 0.8, 0.05,
                          help="Recomendado: 0.8 para shaftless")
    P_m = passo_rel * D_m

    st.markdown('<div class="section-header">Instalação</div>', unsafe_allow_html=True)

    L_m    = st.slider("Comprimento total L (m)", 1.0, 50.0, 10.0, 0.5)
    angulo = st.slider("Inclinação (°)", 0, 45, 0, 1)
    H_m    = L_m * math.sin(math.radians(angulo))

    st.markdown('<div class="section-header">Operação</div>', unsafe_allow_html=True)

    n_critica = calcular_velocidade_critica(D_m)
    n_max_rec = 0.65 * n_critica

    n_rpm = st.slider(
        f"Rotação n (rpm)  — crítica: {n_critica:.1f} rpm",
        min_value=5.0, max_value=float(int(n_critica * 0.9)),
        value=min(float(int(n_max_rec)), float(int(n_critica * 0.9))),
        step=1.0
    )

    perc_critica = (n_rpm / n_critica) * 100

    st.markdown('<div class="section-header">Barras de Desgaste</div>', unsafe_allow_html=True)
    material_barra = st.selectbox(
        "Material das barras",
        ["SAE 1045", "SAE 4140", "Hardox 400", "Hardox 500"],
        index=2,
        help="Hardox 400/500 = alta resistência ao desgaste | SAE 4140 = boa tenacidade | SAE 1045 = uso geral"
    )
    esp_barra_mm    = st.slider("Espessura das barras (mm)", 6, 30, 12, 2,
                                help="Espessura inicial. O limite de troca costuma ser ~50% da espessura original.")
    largura_barra_mm = st.slider("Largura das barras (mm)", 20, 80, 40, 5)
    esp_troca_mm    = st.slider("Espessura mínima p/ troca (mm)", 2, 15, 6, 1,
                                help="Espessura residual que aciona a manutenção.")

# ─────────────────────────────────────────────
#  CÁLCULOS PRINCIPAIS
# ─────────────────────────────────────────────
Q_t_h   = calcular_vazao(D_m, P_m, n_rpm, lamb, rho)
f_inc   = fator_inclinacao(angulo)
Cf_efetivo = cf_corrigido_barras(Cf, material_barra)
P_hor, P_inc, P_total_bruto = calcular_potencia(Q_t_h, L_m, H_m, Cf_efetivo)
P_total = P_total_bruto * f_inc
P_motor = motor_recomendado(P_total)
T_nm    = calcular_torque(P_total, n_rpm)
defl_txt, defl_status = verificar_deflexao(D_m, L_m)
n_barras, peso_barras, folga_mm, vida_h = calcular_barras_desgaste(D_m, L_m, esp_barra_mm, largura_barra_mm, material_barra)
# Vida útil considerando espessura disponível vs taxa de desgaste proporcional
frac_util = (esp_barra_mm - esp_troca_mm) / esp_barra_mm if esp_barra_mm > 0 else 1.0
vida_real_h = vida_h * frac_util

# ─────────────────────────────────────────────
#  CABEÇALHO
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">Rosca Transportadora Shaftless</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Dimensionamento técnico · Cálculo numérico interativo</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS PRINCIPAIS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 RESULTADOS", "📈 SENSIBILIDADE", "🔍 DETALHAMENTO", "📋 MEMORIAL"])

# ══════════════════════════════════════════════
#  TAB 1 — RESULTADOS
# ══════════════════════════════════════════════
with tab1:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="result-card highlight">
          <div class="card-label">Vazão</div>
          <div class="card-value">{Q_t_h:.2f}<span class="card-unit">t/h</span></div>
          <div class="card-sub">{Q_t_h/rho:.2f} m³/h</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="result-card highlight">
          <div class="card-label">Potência total</div>
          <div class="card-value">{P_total:.2f}<span class="card-unit">kW</span></div>
          <div class="card-sub">Motor: {P_motor} kW</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="result-card">
          <div class="card-label">Torque no eixo</div>
          <div class="card-value">{T_nm:.0f}<span class="card-unit">N·m</span></div>
          <div class="card-sub">n = {n_rpm:.0f} rpm</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        badge_class = "badge-ok" if perc_critica <= 65 else ("badge-warn" if perc_critica <= 80 else "badge-err")
        st.markdown(f"""
        <div class="result-card">
          <div class="card-label">Vel. / Vel. crítica</div>
          <div class="card-value">{perc_critica:.0f}<span class="card-unit">%</span></div>
          <div class="card-sub"><span class="{badge_class}">{"✅ Seguro" if perc_critica<=65 else ("⚠️ Atenção" if perc_critica<=80 else "❌ Reduzir")}</span></div>
        </div>""", unsafe_allow_html=True)

    # ── Gráfico gauge + barras de potência
    col_g, col_b = st.columns([1, 1])

    with col_g:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=perc_critica,
            title={"text": "% da velocidade crítica", "font": {"color": "#8b949e", "size": 13}},
            delta={"reference": 65, "increasing": {"color": "#f85149"}, "decreasing": {"color": "#3fb950"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#30363d"},
                "bar": {"color": "#f0b429"},
                "bgcolor": "#161b22",
                "bordercolor": "#30363d",
                "steps": [
                    {"range": [0, 65],  "color": "#0d2818"},
                    {"range": [65, 80], "color": "#2d1f00"},
                    {"range": [80, 100],"color": "#2d0a0a"},
                ],
                "threshold": {"line": {"color": "#f0b429", "width": 3}, "value": 65},
            },
            number={"suffix": "%", "font": {"color": "#f0b429", "size": 36}},
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#0d1117", font_color="#c9d1d9",
            height=280, margin=dict(t=40, b=0, l=20, r=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_b:
        fig_pot = go.Figure()
        categorias = ["Horizontal", "Inclinação", "Total (c/ fator)", "Motor selecionado"]
        valores    = [P_hor * f_inc, P_inc * f_inc, P_total, P_motor]
        cores      = ["#388bfd", "#bc8cff", "#f0b429", "#3fb950"]

        fig_pot.add_trace(go.Bar(
            x=categorias, y=valores,
            marker_color=cores,
            text=[f"{v:.2f} kW" for v in valores],
            textposition="outside",
            textfont=dict(color="#c9d1d9", size=11),
        ))
        fig_pot.update_layout(
            title=dict(text="Balanço de Potência (kW)", font=dict(color="#8b949e", size=13)),
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font_color="#c9d1d9", height=280,
            margin=dict(t=50, b=20, l=10, r=10),
            yaxis=dict(gridcolor="#21262d", zeroline=False),
            xaxis=dict(tickfont=dict(size=11)),
            showlegend=False,
        )
        st.plotly_chart(fig_pot, use_container_width=True)

    # ── Verificações
    st.markdown('<div class="section-header">Verificações de projeto</div>', unsafe_allow_html=True)
    vc1, vc2, vc3 = st.columns(3)
    with vc1:
        status_n = "✅ OK" if perc_critica <= 65 else ("⚠️ Atenção" if perc_critica <= 80 else "❌ Reduzir n")
        cor_n    = "badge-ok" if perc_critica <= 65 else ("badge-warn" if perc_critica <= 80 else "badge-err")
        st.markdown(f"""<div class="result-card">
          <div class="card-label">Velocidade crítica</div>
          <div style="font-size:1.1rem; margin-top:6px;"><span class="{cor_n}">{status_n}</span></div>
          <div class="card-sub">{n_rpm:.1f} / {n_critica:.1f} rpm</div>
        </div>""", unsafe_allow_html=True)

    with vc2:
        cor_d = "badge-ok" if defl_status=="ok" else ("badge-warn" if defl_status=="warn" else "badge-err")
        st.markdown(f"""<div class="result-card">
          <div class="card-label">Deflexão do espiral</div>
          <div style="font-size:1.1rem; margin-top:6px;"><span class="{cor_d}">{defl_txt}</span></div>
          <div class="card-sub">L/D = {L_m/D_m:.1f}</div>
        </div>""", unsafe_allow_html=True)

    with vc3:
        margem = (P_motor / P_total - 1) * 100
        cor_m  = "badge-ok" if 20 <= margem <= 50 else "badge-warn"
        st.markdown(f"""<div class="result-card">
          <div class="card-label">Margem do motor</div>
          <div style="font-size:1.1rem; margin-top:6px;"><span class="{cor_m}">+{margem:.0f}%</span></div>
          <div class="card-sub">{P_total:.2f} kW calc. → {P_motor} kW motor</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 2 — ANÁLISE DE SENSIBILIDADE
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Curvas de resposta — variação de parâmetros</div>', unsafe_allow_html=True)

    sens_param = st.selectbox(
        "Parâmetro do eixo X",
        ["Rotação n (rpm)", "Diâmetro D (mm)", "Comprimento L (m)", "Inclinação (°)", "Fator de enchimento λ"]
    )

    fig_sens = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Vazão (t/h)", "Potência total (kW)"),
    )

    if sens_param == "Rotação n (rpm)":
        x_vals = np.linspace(5, n_critica * 0.9, 80)
        y_vazao = [calcular_vazao(D_m, P_m, n, lamb, rho) for n in x_vals]
        y_pot   = [calcular_potencia(calcular_vazao(D_m, P_m, n, lamb, rho), L_m, H_m, Cf)[2] * f_inc for n in x_vals]
        x_label = "n (rpm)"
        x_mark  = n_rpm

    elif sens_param == "Diâmetro D (mm)":
        x_vals  = np.linspace(150, 600, 80)
        y_vazao = [calcular_vazao(d/1000, passo_rel*(d/1000), n_rpm, lamb, rho) for d in x_vals]
        y_pot   = [calcular_potencia(calcular_vazao(d/1000, passo_rel*(d/1000), n_rpm, lamb, rho), L_m, H_m, Cf)[2]*f_inc for d in x_vals]
        x_label = "D (mm)"
        x_mark  = D_mm

    elif sens_param == "Comprimento L (m)":
        x_vals  = np.linspace(1, 50, 80)
        y_vazao = [Q_t_h] * 80  # vazão não muda com L
        y_pot   = [calcular_potencia(Q_t_h, l, l*math.sin(math.radians(angulo)), Cf)[2]*fator_inclinacao(angulo) for l in x_vals]
        x_label = "L (m)"
        x_mark  = L_m

    elif sens_param == "Inclinação (°)":
        x_vals  = np.linspace(0, 45, 80)
        y_vazao = [Q_t_h] * 80
        y_pot   = [calcular_potencia(Q_t_h, L_m, L_m*math.sin(math.radians(a)), Cf)[2]*fator_inclinacao(a) for a in x_vals]
        x_label = "Inclinação (°)"
        x_mark  = angulo

    else:  # lambda
        x_vals  = np.linspace(0.15, 0.50, 80)
        y_vazao = [calcular_vazao(D_m, P_m, n_rpm, l, rho) for l in x_vals]
        y_pot   = [calcular_potencia(calcular_vazao(D_m, P_m, n_rpm, l, rho), L_m, H_m, Cf)[2]*f_inc for l in x_vals]
        x_label = "λ"
        x_mark  = lamb

    for col_idx, (y_vals, cor, nome) in enumerate([
        (y_vazao, "#f0b429", "Vazão"),
        (y_pot,   "#388bfd", "Potência"),
    ], start=1):
        fig_sens.add_trace(go.Scatter(
            x=x_vals, y=y_vals, mode="lines",
            line=dict(color=cor, width=2.5),
            name=nome,
        ), row=1, col=col_idx)
        # Marca ponto atual
        fig_sens.add_trace(go.Scatter(
            x=[x_mark],
            y=[y_vazao[np.argmin(np.abs(x_vals - x_mark))] if col_idx==1
               else y_pot[np.argmin(np.abs(x_vals - x_mark))]],
            mode="markers",
            marker=dict(color="#ffffff", size=10, line=dict(color=cor, width=2)),
            name="Atual",
            showlegend=(col_idx == 1),
        ), row=1, col=col_idx)

    fig_sens.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        font_color="#c9d1d9", height=380,
        legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
        margin=dict(t=50, b=30, l=30, r=30),
    )
    fig_sens.update_xaxes(title_text=x_label, gridcolor="#21262d", zeroline=False)
    fig_sens.update_yaxes(gridcolor="#21262d", zeroline=False)
    for ann in fig_sens.layout.annotations:
        ann.font.color = "#8b949e"
        ann.font.size  = 12

    st.plotly_chart(fig_sens, use_container_width=True)

    # Mapa de calor n × D
    st.markdown('<div class="section-header">Mapa de calor — Vazão (t/h) por Rotação × Diâmetro</div>', unsafe_allow_html=True)
    ns  = np.linspace(5, 60, 30)
    Ds  = [150, 200, 250, 300, 350, 400, 450, 500, 600]
    Z   = [[calcular_vazao(d/1000, passo_rel*(d/1000), n, lamb, rho) for n in ns] for d in Ds]

    fig_hm = go.Figure(go.Heatmap(
        z=Z, x=np.round(ns, 1), y=Ds,
        colorscale="YlOrRd",
        colorbar=dict(
            title=dict(text="t/h", font=dict(color="#8b949e")),
            tickfont=dict(color="#c9d1d9"),
        ),
        hovertemplate="n=%{x} rpm<br>D=%{y} mm<br>Q=%{z:.2f} t/h<extra></extra>",
    ))
    fig_hm.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        font_color="#c9d1d9", height=320,
        xaxis=dict(title="n (rpm)", gridcolor="#21262d"),
        yaxis=dict(title="D (mm)", gridcolor="#21262d"),
        margin=dict(t=20, b=40, l=60, r=20),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

# ══════════════════════════════════════════════
#  TAB 3 — DETALHAMENTO
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Parâmetros geométricos calculados</div>', unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dados_geo = {
            "Diâmetro externo D": f"{D_mm} mm",
            "Passo P": f"{P_m*1000:.1f} mm",
            "Relação P/D": f"{passo_rel:.2f}",
            "Comprimento total": f"{L_m:.1f} m",
            "Altura total (H)": f"{H_m:.2f} m",
            "Inclinação": f"{angulo}°",
            "N° de espiras (aprox.)": f"{L_m/P_m:.1f}",
        }
        for k, v in dados_geo.items():
            st.markdown(f"""<div style="display:flex;justify-content:space-between;
                padding:8px 0;border-bottom:1px solid #21262d;font-size:0.9rem;">
                <span style="color:#8b949e;">{k}</span>
                <span style="color:#f0b429;font-family:'Space Mono',monospace;">{v}</span>
            </div>""", unsafe_allow_html=True)

    with col_d2:
        dados_op = {
            "Rotação n": f"{n_rpm:.1f} rpm",
            "Velocidade crítica": f"{n_critica:.1f} rpm",
            "% da crítica": f"{perc_critica:.1f}%",
            "Fator de enchimento λ": f"{lamb:.2f}",
            "Densidade do material": f"{rho:.2f} t/m³",
            "Fator de resistência Cf": f"{Cf:.1f}",
            "Fator de inclinação": f"{f_inc:.3f}",
        }
        for k, v in dados_op.items():
            st.markdown(f"""<div style="display:flex;justify-content:space-between;
                padding:8px 0;border-bottom:1px solid #21262d;font-size:0.9rem;">
                <span style="color:#8b949e;">{k}</span>
                <span style="color:#388bfd;font-family:'Space Mono',monospace;">{v}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Barras de Desgaste de Aço</div>', unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        dados_barras = {
            "Material selecionado":  material_barra,
            "Espessura inicial":     f"{esp_barra_mm} mm",
            "Espessura de troca":    f"{esp_troca_mm} mm",
            "Espessura utilizável":  f"{esp_barra_mm - esp_troca_mm} mm",
            "Largura das barras":    f"{largura_barra_mm} mm",
            "Folga diametral":       f"{folga_mm:.0f} mm",
        }
        for k, v in dados_barras.items():
            st.markdown(f"""<div style="display:flex;justify-content:space-between;
                padding:8px 0;border-bottom:1px solid #21262d;font-size:0.9rem;">
                <span style="color:#8b949e;">{k}</span>
                <span style="color:#f0b429;font-family:'Space Mono',monospace;">{v}</span>
            </div>""", unsafe_allow_html=True)

    with col_b2:
        dados_barras2 = {
            "Qtd. estimada de barras": f"{n_barras} un",
            "Peso total das barras":   f"{peso_barras:.1f} kg",
            "Vida base (material)":    f"{vida_h:,} h",
            "Fração utilizável":       f"{frac_util*100:.0f}%",
            "Vida útil real estimada": f"{vida_real_h:,.0f} h",
            "Cf base":                 f"{Cf:.2f}",
            "Cf efetivo c/ barras":    f"{Cf_efetivo:.2f}",
        }
        for k, v in dados_barras2.items():
            cor = "#3fb950" if "Cf efetivo" in k else "#388bfd"
            st.markdown(f"""<div style="display:flex;justify-content:space-between;
                padding:8px 0;border-bottom:1px solid #21262d;font-size:0.9rem;">
                <span style="color:#8b949e;">{k}</span>
                <span style="color:{cor};font-family:'Space Mono',monospace;">{v}</span>
            </div>""", unsafe_allow_html=True)

    # Gráfico de desgaste ao longo do tempo
    st.markdown('<div class="section-header">Curva de desgaste das barras</div>', unsafe_allow_html=True)
    horas_deg = [0, vida_h*0.25, vida_h*0.5, vida_h*0.75, vida_h, vida_h*1.1]
    esp_deg   = [esp_barra_mm,
                 esp_barra_mm * 0.82,
                 esp_barra_mm * 0.65,
                 esp_barra_mm * 0.50,
                 esp_barra_mm * (1 - frac_util),
                 esp_barra_mm * (1 - frac_util) * 0.9]
    fig_deg = go.Figure()
    fig_deg.add_trace(go.Scatter(
        x=horas_deg, y=esp_deg, mode="lines+markers",
        line=dict(color="#f0b429", width=2.5),
        marker=dict(size=7, color="#f0b429"),
        name="Espessura restante",
    ))
    fig_deg.add_hline(
        y=esp_troca_mm, line_dash="dash", line_color="#f85149",
        annotation_text=f"  Limite de troca: {esp_troca_mm} mm",
        annotation_font_color="#f85149",
    )
    fig_deg.add_vline(
        x=vida_real_h, line_dash="dot", line_color="#3fb950",
        annotation_text=f"  Troca: ~{vida_real_h:,.0f} h",
        annotation_font_color="#3fb950",
    )
    fig_deg.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        font_color="#c9d1d9", height=280,
        xaxis=dict(title="Horas de operação (h)", gridcolor="#21262d"),
        yaxis=dict(title="Espessura (mm)", gridcolor="#21262d"),
        margin=dict(t=20, b=40, l=50, r=20),
        showlegend=False,
    )
    st.plotly_chart(fig_deg, use_container_width=True)

    # Tabela comparativa de materiais
    st.markdown('<div class="section-header">Comparativo de materiais para barras</div>', unsafe_allow_html=True)
    mat_dados = [
        ("SAE 1045",   "~200 HB",  "2.000 h",  "Baixo",   "Uso geral, baixo custo"),
        ("SAE 4140",   "~280 HB",  "3.500 h",  "Médio",   "Boa tenacidade, impacto moderado"),
        ("Hardox 400", "~400 HB",  "6.000 h",  "Alto",    "Alta resistência ao desgaste"),
        ("Hardox 500", "~500 HB", "10.000 h",  "Muito alto", "Máxima vida útil, material abrasivo"),
    ]
    for mat, dureza, vida, custo, desc in mat_dados:
        selecionado = mat == material_barra
        bg = "background:#1c2027;border-color:#f0b429;" if selecionado else ""
        icone = "⭐" if selecionado else "·"
        st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 80px 90px 90px 2fr;
            gap:8px;align-items:center;padding:8px 12px;border-radius:6px;
            border:1px solid #30363d;{bg}margin-bottom:4px;font-size:0.82rem;">
            <span style="color:#f0b429;font-weight:600;">{icone} {mat}</span>
            <span style="color:#8b949e;">{dureza}</span>
            <span style="color:#3fb950;">{vida}</span>
            <span style="color:#bc8cff;">{custo}</span>
            <span style="color:#6e7681;">{desc}</span>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 4 — MEMORIAL DE CÁLCULO
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Memorial de cálculo — passo a passo</div>', unsafe_allow_html=True)

    passos = [
        ("1. Velocidade crítica",
         f"n_crítica = 45 / √D = 45 / √{D_m:.3f} = **{n_critica:.2f} rpm**"),
        ("2. Passo do espiral",
         f"P = {passo_rel} × D = {passo_rel} × {D_mm} mm = **{P_m*1000:.1f} mm**"),
        ("3. Área transversal",
         f"A = π × D² / 4 = π × {D_m:.3f}² / 4 = **{math.pi*D_m**2/4:.5f} m²**"),
        ("4. Vazão volumétrica",
         f"Q_vol = A × P × n × λ × 60 = {math.pi*D_m**2/4:.5f} × {P_m:.4f} × {n_rpm:.1f} × {lamb} × 60 = **{Q_t_h/rho:.3f} m³/h**"),
        ("5. Vazão mássica",
         f"Q = Q_vol × ρ = {Q_t_h/rho:.3f} × {rho} = **{Q_t_h:.3f} t/h**"),
        ("6. Cf efetivo com barras de aço",
         f"Cf_efetivo = Cf_base × fator_material = {Cf:.2f} × {Cf_efetivo/Cf:.2f} = **{Cf_efetivo:.3f}**"),
        ("7. Potência horizontal",
         f"P_hor = (Q × L × Cf) / 367 = ({Q_t_h:.3f} × {L_m} × {Cf}) / 367 = **{P_hor:.3f} kW**"),
        ("8. Potência de inclinação",
         f"P_inc = (Q × H) / 367 = ({Q_t_h:.3f} × {H_m:.3f}) / 367 = **{P_inc:.4f} kW**"),
        ("9. Potência total (com fator de inclinação)",
         f"P_total = (P_hor + P_inc) × f_inc = ({P_hor:.3f} + {P_inc:.4f}) × {f_inc:.3f} = **{P_total:.3f} kW**"),
        ("10. Motor com margem de 25%",
         f"P_motor_min = {P_total:.3f} × 1.25 = {P_total*1.25:.3f} kW → Motor padrão: **{P_motor} kW**"),
        ("11. Torque no eixo de acionamento",
         f"T = (P × 1000 × 60) / (2π × n) = ({P_total:.3f} × 1000 × 60) / (2π × {n_rpm:.1f}) = **{T_nm:.1f} N·m**"),
    ]

    for titulo, formula in passos:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;
             padding:12px 16px;margin-bottom:8px;">
          <div style="font-family:'Space Mono',monospace;font-size:0.75rem;
               color:#8b949e;margin-bottom:4px;">{titulo}</div>
          <div style="font-size:0.9rem;color:#c9d1d9;">{formula}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.8rem;color:#6e7681;margin-top:1rem;">
    <strong style="color:#8b949e;">Referências:</strong> CEMA (Conveyor Equipment Manufacturers Association) · 
    ISO 7119 · DIN 15262 · Martin Engineering Handbook · 
    Formulações adaptadas para roscas shaftless (sem eixo central).
    </div>""", unsafe_allow_html=True)
