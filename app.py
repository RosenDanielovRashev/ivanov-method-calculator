import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

data = load_data()

def compute_Eeq(h, D, E1, E2):
    hD = h / D
    E1E2 = E1 / E2
    tol = 1e-4
    iso_levels = sorted(data['Eeq_over_E2'].unique())
    debug_info = []

    for low, high in zip(iso_levels, iso_levels[1:]):
        grp_low = data[data['Eeq_over_E2'] == low].sort_values('h_over_D')
        grp_high = data[data['Eeq_over_E2'] == high].sort_values('h_over_D')

        h_min = max(grp_low['h_over_D'].min(), grp_high['h_over_D'].min())
        h_max = min(grp_low['h_over_D'].max(), grp_high['h_over_D'].max())
        if not (h_min - tol <= hD <= h_max + tol):
            continue

        try:
            y_low = np.interp(hD, grp_low['h_over_D'], grp_low['E1_over_E2'])
            y_high = np.interp(hD, grp_high['h_over_D'], grp_high['E1_over_E2'])
        except:
            continue

        debug_info.append({
            'Изолинии': f"{low:.2f}-{high:.2f}",
            'y_low': y_low,
            'y_high': y_high,
            'E1/E2': E1E2
        })

        if not (min(y_low, y_high) - tol <= E1E2 <= max(y_low, y_high) + tol):
            continue

        frac = 0 if np.isclose(y_high, y_low) else (E1E2 - y_low) / (y_high - y_low)
        eq_over_e2 = low + frac * (high - low)

        st.write("📌 Интерполация между:", f"{low:.2f} → {high:.2f}")
        st.write(f"🔹 y_low = {y_low:.4f}, y_high = {y_high:.4f}, E1/E2 = {E1E2:.4f}")
        st.write(f"🔹 frac = {frac:.4f}, Eeq/E2 = {eq_over_e2:.4f}")
        return eq_over_e2 * E2

    st.info("🔎 Диагностика на интерполация (няма съвпадение):")
    st.write(pd.DataFrame(debug_info))
    return None

st.title("📐 Калкулатор: Метод на Иванов (интерактивна версия)")

# Вход
E1 = st.number_input("E1 (MPa)", value=2600)
E2 = st.number_input("E2 (MPa)", value=3000)
h = st.number_input("h (cm)", value=20)
D = st.number_input("D (cm)", value=40)

# Показване на съотношенията
st.subheader("📊 Въведени параметри:")
st.write(pd.DataFrame({
    "Параметър": ["E1", "E2", "h", "D", "E1 / E2", "h / D"],
    "Стойност": [E1, E2, h, D, round(E1 / E2, 3), round(h / D, 3)]
}))

# Изчисление
if st.button("Изчисли"):
    result = compute_Eeq(h, D, E1, E2)
    hD_point = h / D
    E1E2_point = E1 / E2

    if result is None:
        st.warning("❗ Точката е извън обхвата на наличните изолинии.")
    else:
        st.success(f"✅ Eeq = {result:.2f} MPa")
        st.info(f"Eeq / E2 = {result / E2:.3f}")

        # Интерактивна графика с Plotly
        fig = go.Figure()

        for value, group in data.groupby("Eeq_over_E2"):
            group_sorted = group.sort_values("h_over_D")
            fig.add_trace(go.Scatter(
                x=group_sorted["h_over_D"],
                y=group_sorted["E1_over_E2"],
                mode='lines',
                name=f"Eeq/E2 = {value:.2f}",
                line=dict(width=1)
            ))

        # Добавяне на точката
        fig.add_trace(go.Scatter(
            x=[hD_point],
            y=[E1E2_point],
            mode='markers',
            name="Твоята точка",
            marker=dict(size=8, color='red', symbol='circle')
        ))

        fig.update_layout(
            title="Интерактивна диаграма на изолинии (Eeq / E2)",
            xaxis_title="h / D",
            yaxis_title="E1 / E2",
            xaxis=dict(dtick=0.1),
            yaxis=dict(dtick=0.05),
            legend=dict(orientation="h", y=-0.3),
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)
