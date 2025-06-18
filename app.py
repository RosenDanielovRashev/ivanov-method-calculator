import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

data = load_data()
points = data[['h_over_D', 'E1_over_E2']].values
values = data['Eeq_over_E2'].values

def compute_Eeq(h, D, E1, E2):
    hD = h / D
    E1E2 = E1 / E2
    ratio = griddata(points, values, (hD, E1E2), method='linear')
    if np.isnan(ratio):
        return None
    return ratio * E2

st.title("📐 Калкулатор: Метод на Иванов")

# Входни полета
E1 = st.number_input("E1 (MPa)", value=3000)
E2 = st.number_input("E2 (MPa)", value=200)
h = st.number_input("h (cm)", value=20)
D = st.number_input("D (cm)", value=30)

# Автоматично показване на изчислени съотношения
st.subheader("📊 Въведени параметри:")
st.write(pd.DataFrame({
    "Параметър": ["E1", "E2", "h", "D", "E1 / E2", "h / D"],
    "Стойност": [E1, E2, h, D, round(E1 / E2, 3), round(h / D, 3)]
}))

# Бутон за изчисление
if st.button("Изчисли"):
    result = compute_Eeq(h, D, E1, E2)
    hD_point = h / D
    E1E2_point = E1 / E2

    if result is None:
        st.warning("Извън обхвата на таблицата. Добави още изолинии.")
    else:
        st.success(f"Eeq = {result:.2f} MPa")
        st.info(f"Eeq / E2 = {result / E2:.3f}")

        # Подготовка на графика
        hD_vals = np.linspace(0.01, 0.75, 100)
        Eeq_vals = []
        hD_clean = []

        for hd in hD_vals:
            val = compute_Eeq(hd * D, D, E1, E2)
            if val is not None:
                Eeq_vals.append(val / E2)
                hD_clean.append(hd)

        fig, ax = plt.subplots()
        ax.plot(hD_clean, Eeq_vals, label="Eeq/E2", color='blue')
        ax.scatter([hD_point], [result / E2], color='red', label="Твоята точка", zorder=5)
        ax.set_xlabel("h/D")
        ax.set_ylabel("Eeq/E2")
        ax.set_title("Графика: Eeq/E2 спрямо h/D")
        ax.legend()
        st.pyplot(fig)