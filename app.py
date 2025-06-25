import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

@st.cache_data
def load_data():
    df = pd.read_csv("combined_data.csv")
    df = df.rename(columns={
        "E1_over_E2": "Ed_over_Ei",
        "Eeq_over_E2": "Ee_over_Ei"
    })
    return df

data = load_data()

def interpolate_EdEi_for_EeEi(Ee, Ei):
    ee_over_ei = Ee / Ei
    tol = 1e-4

    # Намери две изолинии между които е ee_over_ei
    iso_levels = sorted(data['Ee_over_Ei'].unique())

    low_iso = None
    high_iso = None
    for low, high in zip(iso_levels, iso_levels[1:]):
        if low - tol <= ee_over_ei <= high + tol:
            low_iso = low
            high_iso = high
            break

    if low_iso is None or high_iso is None:
        return None  # извън диапазона

    # Вземи данните за двете изолинии
    grp_low = data[data['Ee_over_Ei'] == low_iso].sort_values('h_over_D')
    grp_high = data[data['Ee_over_Ei'] == high_iso].sort_values('h_over_D')

    # Общ интервал на h/D за двете групи
    h_min = max(grp_low['h_over_D'].min(), grp_high['h_over_D'].min())
    h_max = min(grp_low['h_over_D'].max(), grp_high['h_over_D'].max())

    # Филтрирай точките в общия интервал
    grp_low = grp_low[(grp_low['h_over_D'] >= h_min) & (grp_low['h_over_D'] <= h_max)]
    grp_high = grp_high[(grp_high['h_over_D'] >= h_min) & (grp_high['h_over_D'] <= h_max)]

    h_values = grp_low['h_over_D'].values

    ed_values = []
    for hD in h_values:
        y_low = np.interp(hD, grp_low['h_over_D'], grp_low['Ed_over_Ei'])
        y_high = np.interp(hD, grp_high['h_over_D'], grp_high['Ed_over_Ei'])
        frac = 0 if np.isclose(high_iso, low_iso) else (ee_over_ei - low_iso) / (high_iso - low_iso)
        ed_val = y_low + frac * (y_high - y_low)
        ed_values.append(ed_val)

    return h_values, np.array(ed_values), low_iso, high_iso

st.title("📐 Калкулатор: Изчисляване на Ed / Ei от Ee и Ei")

Ee = st.number_input("Ee (MPa)", value=2700.0, min_value=0.0)
Ei = st.number_input("Ei (MPa)", value=3000.0, min_value=0.1)

if st.button("Изчисли"):
    res = interpolate_EdEi_for_EeEi(Ee, Ei)
    if res is None:
        st.warning("❗ Стойността Ee/Ei е извън обхвата на изолиниите в данните.")
    else:
        h_values, ed_values, low_iso, high_iso = res
        ee_over_ei = Ee / Ei

        st.success(f"✅ Изчислени стойности на Ed / Ei за Ee / Ei между {low_iso:.3f} и {high_iso:.3f}")
        st.write(pd.DataFrame({
            "h / D": h_values,
            "Ed / Ei": np.round(ed_values, 4)
        }))

        fig = go.Figure()

        # Показваме двете изолинии, между които се интерполира
        for iso in [low_iso, high_iso]:
            group = data[data['Ee_over_Ei'] == iso].sort_values('h_over_D')
            fig.add_trace(go.Scatter(
                x=group['h_over_D'],
                y=group['Ed_over_Ei'],
                mode='lines',
                name=f"Изолиния Ee/Ei = {iso:.3f}",
                line=dict(dash='dot')
            ))

        # Интерполираната крива
        fig.add_trace(go.Scatter(
            x=h_values,
            y=ed_values,
            mode='lines+markers',
            name=f"Интерполирана Ed/Ei за Ee/Ei = {ee_over_ei:.3f}",
            line=dict(width=3, color='red'),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title="Ed / Ei срещу h / D",
            xaxis_title="h / D",
            yaxis_title="Ed / Ei",
            height=600,
            legend=dict(orientation="h", y=-0.3)
        )

        st.plotly_chart(fig, use_container_width=True)
