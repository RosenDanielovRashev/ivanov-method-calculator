import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Зареждане на данни с кеширане
@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

data = load_data()

# Основна функция за изчисление на Ee
def compute_Ee(h, D, Ed, Ei):
    hD = h / D
    EdEi = Ed / Ei
    tol = 1e-4
    iso_levels = sorted(data['Ee_over_Ei'].unique())

    for low, high in zip(iso_levels, iso_levels[1:]):
        grp_low = data[data['Ee_over_Ei'] == low].sort_values('h_over_D')
        grp_high = data[data['Ee_over_Ei'] == high].sort_values('h_over_D')

        h_min = max(grp_low['h_over_D'].min(), grp_high['h_over_D'].min())
        h_max = min(grp_low['h_over_D'].max(), grp_high['h_over_D'].max())
        if not (h_min - tol <= hD <= h_max + tol):
            continue

        try:
            y_low = np.interp(hD, grp_low['h_over_D'], grp_low['Ed_over_Ei'])
            y_high = np.interp(hD, grp_high['h_over_D'], grp_high['Ed_over_Ei'])
        except:
            continue

        if not (min(y_low, y_high) - tol <= EdEi <= max(y_low, y_high) + tol):
            continue

        frac = 0 if np.isclose(y_high, y_low) else (EdEi - y_low) / (y_high - y_low)
        ee_over_ei = low + frac * (high - low)

        st.write("📌 Интерполация между:", f"{low:.2f} → {high:.2f}")
        return ee_over_ei * Ei, hD, y_low, y_high

    return None, None, None, None

# Заглавие
st.title("📐 Калкулатор: Метод на Иванов (интерактивна версия)")

# Входни параметри
Ed = st.number_input("Ed (MPa)", value=2600)
Ei = st.number_input("Ei (MPa)", value=3000)
h = st.number_input("h (cm)", value=20)
D = st.number_input("D (cm)", value=40)

# Проверка за деление на нула
if Ei == 0 or D == 0:
    st.error("❌ Ei и D не трябва да са нула.")
    st.stop()

# Показване на параметрите
st.subheader("📊 Въведени параметри:")
st.write(pd.DataFrame({
    "Параметър": ["Ed", "Ei", "h", "D", "Ed / Ei", "h / D"],
    "Стойност": [Ed, Ei, h, D, round(Ed / Ei, 3), round(h / D, 3)]
}))

# Изчисление при натискане на бутон
if st.button("Изчисли"):
    result, hD_point, y_low, y_high = compute_Ee(h, D, Ed, Ei)
    EdEi_point = Ed / Ei

    if result is None:
        st.warning("❗ Точката е извън обхвата на наличните изолинии.")
    else:
        st.success(f"✅ Ee = {result:.2f} MPa")
        st.info(f"Ee / Ei = {result / Ei:.3f}")

        # Диаграма
        fig = go.Figure()

        for value, group in data.groupby("Ee_over_Ei"):
            group_sorted = group.sort_values("h_over_D")
            fig.add_trace(go.Scatter(
                x=group_sorted["h_over_D"],
                y=group_sorted["Ed_over_Ei"],
                mode='lines',
                name=f"Ee/Ei = {value:.2f}",
                line=dict(width=1)
            ))

        # Твоята точка
        fig.add_trace(go.Scatter(
            x=[hD_point],
            y=[EdEi_point],
            mode='markers',
            name="Твоята точка",
            marker=dict(size=8, color='red', symbol='circle')
        ))

        # Линия на интерполация
        if y_low is not None and y_high is not None:
            fig.add_trace(go.Scatter(
                x=[hD_point, hD_point],
                y=[y_low, y_high],
                mode='lines',
                line=dict(color='green', width=2, dash='dot'),
                name="Интерполационна линия"
            ))

        fig.update_layout(
            title="Интерактивна диаграма на изолинии (Ee / Ei)",
            xaxis_title="h / D",
            yaxis_title="Ed / Ei",
            xaxis=dict(dtick=0.1),
            yaxis=dict(dtick=0.05),
            legend=dict(orientation="h", y=-0.3),
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)
