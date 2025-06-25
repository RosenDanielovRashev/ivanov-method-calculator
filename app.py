import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

@st.cache_data
def load_data():
    df = pd.read_csv("combined_data.csv")
    # Ако колоните са със стари имена, преименувай ги тук
    df = df.rename(columns={
        "E1_over_E2": "Ed_over_Ei",
        "Eeq_over_E2": "Ee_over_Ei"
    })
    return df

data = load_data()

def compute_EdEi(h, D, ee_over_ei):
    hD = h / D
    tol = 1e-4

    # Филтрираме данните по избраната изолиния
    group = data[data['Ee_over_Ei'] == ee_over_ei].sort_values('h_over_D')

    if group.empty:
        return None, None

    h_min = group['h_over_D'].min()
    h_max = group['h_over_D'].max()

    if not (h_min - tol <= hD <= h_max + tol):
        return None, None  # h/D извън обхвата

    try:
        ed_over_ei = np.interp(hD, group['h_over_D'], group['Ed_over_Ei'])
        return ed_over_ei, hD
    except Exception as e:
        return None, None

st.title("📐 Калкулатор: Метод на Иванов (обратна задача)")

# Вход - потребител избира изолиния Ee/Ei и задава h и D
ee_over_ei_list = sorted(data['Ee_over_Ei'].unique())
Ee_over_Ei = st.selectbox("Избери Ee / Ei (изолиния)", ee_over_ei_list)

h = st.number_input("h (cm)", value=20.0, min_value=0.0)
D = st.number_input("D (cm)", value=40.0, min_value=0.1)  # D не може да е 0

if st.button("Изчисли"):
    Ed_over_Ei, hD = compute_EdEi(h, D, Ee_over_Ei)

    if Ed_over_Ei is None:
        st.warning("❗ h / D е извън обхвата за избраната изолиния.")
    else:
        st.success(f"✅ Ed / Ei = {Ed_over_Ei:.3f}")
        st.info(f"h / D = {hD:.3f}")

        # Визуализация на изолинията и точката
        group = data[data['Ee_over_Ei'] == Ee_over_Ei].sort_values('h_over_D')

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=group['h_over_D'],
            y=group['Ed_over_Ei'],
            mode='lines',
            name=f"Ee/Ei = {Ee_over_Ei:.3f}",
            line=dict(width=2)
        ))

        fig.add_trace(go.Scatter(
            x=[hD],
            y=[Ed_over_Ei],
            mode='markers',
            name="Твоята точка",
            marker=dict(size=10, color='red', symbol='circle')
        ))

        fig.update_layout(
            title="Ed / Ei при зададени Ee / Ei и h / D",
            xaxis_title="h / D",
            yaxis_title="Ed / Ei",
            xaxis=dict(dtick=0.05),
            yaxis=dict(dtick=0.05),
            legend=dict(orientation="h", y=-0.3),
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)
