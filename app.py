import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

@st.cache_data
def load_data():
    df = pd.read_csv("combined_data.csv")
    # Ако все още имаш старите имена, замени ги тук
    df = df.rename(columns={
        "E1_over_E2": "Ed_over_Ei",
        "Eeq_over_E2": "Ee_over_Ei"
    })
    return df

data = load_data()

def compute_Ed(h, D, Ee, Ei):
    hD = h / D
    EeEi = Ee / Ei
    tol = 1e-4
    iso_levels = sorted(data['Ee_over_Ei'].unique())

    # Търсим между кои две изолинии се намира EeEi
    for low, high in zip(iso_levels, iso_levels[1:]):
        if not (low - tol <= EeEi <= high + tol):
            continue

        grp_low = data[data['Ee_over_Ei'] == low].sort_values('h_over_D')
        grp_high = data[data['Ee_over_Ei'] == high].sort_values('h_over_D')

        h_min = max(grp_low['h_over_D'].min(), grp_high['h_over_D'].min())
        h_max = min(grp_low['h_over_D'].max(), grp_high['h_over_D'].max())
        if not (h_min - tol <= hD <= h_max + tol):
            continue

        # Интерполация за Ed_over_Ei в двете изолинии при даденото h/D
        y_low = np.interp(hD, grp_low['h_over_D'], grp_low['Ed_over_Ei'])
        y_high = np.interp(hD, grp_high['h_over_D'], grp_high['Ed_over_Ei'])

        # Сега интерполиране на Ed_over_Ei между двете изолинии, според къде попада EeEi
        frac = 0 if np.isclose(high, low) else (EeEi - low) / (high - low)
        ed_over_ei = y_low + frac * (y_high - y_low)

        st.write("📌 Интерполация между Ee/Ei:", f"{low:.3f} → {high:.3f}")
        return ed_over_ei * Ei, hD, y_low, y_high

    return None, None, None, None

st.title("📐 Калкулатор: Метод на Иванов (интерактивна версия)")

# Входове
Ee = st.number_input("Ee (MPa)", value=2700.0)
Ei = st.number_input("Ei (MPa)", value=3000.0)
h = st.number_input("h (cm)", value=20.0)
D = st.number_input("D (cm)", value=40.0)

if Ei == 0 or D == 0:
    st.error("Ei и D не могат да бъдат 0.")
    st.stop()

EeEi = Ee / Ei

st.subheader("📊 Въведени параметри:")
st.write(pd.DataFrame({
    "Параметър": ["Ee", "Ei", "h", "D", "Ee / Ei", "h / D"],
    "Стойност": [
        Ee,
        Ei,
        h,
        D,
        round(EeEi, 3),
        round(h / D, 3)
    ]
}))

if st.button("Изчисли"):
    result, hD_point, y_low, y_high = compute_Ed(h, D, Ee, Ei)

    if result is None:
        st.warning("❗ Точката е извън обхвата на наличните изолинии.")
    else:
        EdEi_point = result / Ei
        st.success(f"✅ Изчислено Ed = {result:.2f} MPa (Ed / Ei = {EdEi_point:.3f})")

        fig = go.Figure()

        for value, group in data.groupby("Ee_over_Ei"):
            group_sorted = group.sort_values("h_over_D")
            fig.add_trace(go.Scatter(
                x=group_sorted["h_over_D"],
                y=group_sorted["Ed_over_Ei"],
                mode='lines',
                name=f"Ee / Ei = {value:.2f}",
                line=dict(width=1)
            ))

        # Показваме точката (h/D, Ed/Ei)
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
