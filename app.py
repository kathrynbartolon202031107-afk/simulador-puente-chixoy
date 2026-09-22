import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="Simulador Puente de los Mártires de Chixoy", layout="wide")

st.title("🌉 Simulador Estructural - Puente de los Mártires de Chixoy")
st.markdown("Análisis 3D y distribución de cargas en tiempo real (Voladizos sucesivos y Aisladores sísmicos).")

# Parámetros fijos del puente (Presentación)
LONGITUD_TOTAL = 272.75  # metros
ANCHO_TOTAL = 10.30      # metros
POS_APOYOS = [0.0, 70.0, 202.75, 272.75]
W_MUERTA = 120.0        # kN/m

# Barra lateral para configurar los vehículos (Libro Azul / AASHTO)
st.sidebar.header("⚙️ Configuración de Simulación")

simular_animacion = st.sidebar.checkbox("▶️ Activar animación dinámica de tránsito", value=False)

st.sidebar.subheader("🚚 Camión 1 (Carril Izquierdo)")
tipo_c1 = st.sidebar.selectbox("Tipo de Vehículo 1", ["HL-93", "C3-S2"], index=0)
pos_c1 = st.sidebar.slider("Posición Camión 1 (m)", -20.0, LONGITUD_TOTAL + 10.0, 45.0)

st.sidebar.subheader("🚛 Camión 2 (Carril Derecho)")
tipo_c2 = st.sidebar.selectbox("Tipo de Vehículo 2", ["HL-93", "C3-S2"], index=1)
pos_c2 = st.sidebar.slider("Posición Camión 2 (m)", -20.0, LONGITUD_TOTAL + 10.0, 135.0)

# Datos de cargas
CAMIONES_CONFIG = {
    'HL-93': {'ejes': [35.0, 145.0, 145.0], 'distancias': [0.0, 4.3, 9.0]},
    'C3-S2': {'ejes': [50.0, 120.0, 120.0, 110.0, 110.0], 'distancias': [0.0, 3.0, 4.2, 9.0, 10.3]}
}

def calcular_estado(p1, p2, t1, t2):
    x = np.linspace(0, LONGITUD_TOTAL, 300)
    cargas = []
    
    for peso, dist in zip(CAMIONES_CONFIG[t1]['ejes'], CAMIONES_CONFIG[t1]['distancias']):
        pos = p1 + dist
        if 0 <= pos <= LONGITUD_TOTAL:
            cargas.append((pos, peso))
            
    for peso, dist in zip(CAMIONES_CONFIG[t2]['ejes'], CAMIONES_CONFIG[t2]['distancias']):
        pos = p2 + dist
        if 0 <= pos <= LONGITUD_TOTAL:
            cargas.append((pos, peso))
            
    fuerza_total = W_MUERTA * LONGITUD_TOTAL + sum(p[1] for p in cargas)
    R = np.array([fuerza_total * 0.15, fuerza_total * 0.35, fuerza_total * 0.35, fuerza_total * 0.15])
    
    V = np.zeros_like(x)
    for i, xi in enumerate(x):
        V[i] = -W_MUERTA * xi
        for pos_p, peso in cargas:
            if xi >= pos_p:
                V[i] -= peso
        for pos_r, reacc in zip(POS_APOYOS, R):
            if xi >= pos_r:
                V[i] += reacc

    dx = x[1] - x[0]
    M = np.cumsum(V) * dx
    return x, V, M, R

# Generación del gráfico
x, V, M, R = calcular_estado(pos_c1, pos_c2, tipo_c1, tipo_c2)

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=(
        "Modelo 3D: Viga Cajón, Aisladores Sísmicos y Vehículos",
        "Diagrama de Esfuerzo Cortante V(x) [kN]",
        "Diagrama de Momento Flector M(x) [kN·m]"
    ),
    specs=[[{"type": "scene"}], [{"type": "xy"}], [{"type": "xy"}]]
)

# Tablero
y_tab = np.array([-ANCHO_TOTAL/2, ANCHO_TOTAL/2])
X_tab, Y_tab = np.meshgrid(np.linspace(0, LONGITUD_TOTAL, 30), y_tab)
Z_tab = np.zeros_like(X_tab)

fig.add_trace(go.Surface(x=X_tab, y=Y_tab, z=Z_tab, colorscale=[[0, 'gray'], [1, 'gray']], showscale=False), row=1, col=1)

# Pilares y Aisladores
for i, pos_pilar in enumerate(POS_APOYOS):
    fig.add_trace(go.Mesh3d(
        x=[pos_pilar-2, pos_pilar+2, pos_pilar+2, pos_pilar-2, pos_pilar-2, pos_pilar+2, pos_pilar+2, pos_pilar-2],
        y=[-3, -3, 3, 3, -3, -3, 3, 3], z=[-20, -20, -20, -20, -2, -2, -2, -2],
        color='darkgray', opacity=0.8
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter3d(
        x=[pos_pilar], y=[0], z=[-1], mode='markers+text',
        marker=dict(size=8, color='red', symbol='diamond'),
        text=[f"Aislador<br>R={R[i]:.0f}kN"], textposition="top center"
    ), row=1, col=1)

# Camiones
fig.add_trace(go.Scatter3d(
    x=[pos_c1], y=[-2.0], z=[1.5], mode='markers+text',
    marker=dict(size=10, color='blue', symbol='square'), text=[f"Camión 1 ({tipo_c1})"]
), row=1, col=1)

fig.add_trace(go.Scatter3d(
    x=[pos_c2], y=[2.0], z=[1.5], mode='markers+text',
    marker=dict(size=10, color='darkblue', symbol='square'), text=[f"Camión 2 ({tipo_c2})"]
), row=1, col=1)

# Diagramas
fig.add_trace(go.Scatter(x=x, y=V, mode='lines', fill='tozeroy', line=dict(color='orange', width=2)), row=2, col=1)
fig.add_trace(go.Scatter(x=x, y=M, mode='lines', fill='tozeroy', line=dict(color='green', width=2)), row=3, col=1)

fig.update_layout(
    height=850,
    scene=dict(xaxis_title="Longitud (m)", yaxis_title="Ancho (m)", zaxis_title="Altura (m)", aspectratio=dict(x=3, y=0.5, z=0.5)),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)
