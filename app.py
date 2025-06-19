import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

data = load_data()

def compute_Eeq(h, D, E1, E2):
    hD = h / D
    E1E2 = E1 / E2

    # Групиране по изолинии
    iso_levels = sorted(data['Eeq_over_E2'].unique())
    for i in range(len(iso_levels) - 1):
        low = iso_levels[i]
        high = iso_levels[i + 1]

        group_low = data[data["Eeq_over_E2"] == low]
        group_high = data[data["Eeq_over_E2"] == high]

        # Комбинирани точки и стойности
        points = pd.concat([group_low, group_high])[['h_over_D', 'E1_over_E2']].values
        values = np.array([low]*len(group_low) + [high]*len(group_high))

        # Интерполация само между тези две изолинии
        result = griddata(points, values, (hD, E1E2), method='linear')

        if not np.isnan(result):
            return result * E2

    # Извън обхвата
    return None

st.title("📐 Калкулатор: Метод на Иванов (с реални изолинии)")

# Входни полета
E1 = st.number_input("E1 (MPa)", value=2600)
E2 = st.number_input("E2 (MPa)", value=3000)
h = st.number_input("h (cm)", value=20)
D = st.number_input("D (cm)", value=40)

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
        st.warning("Точката е извън обхвата на наличните изолинии.")
    else:
        st.success(f"Eeq = {result:.2f} MPa")
        st.info(f"Eeq / E2 = {result / E2:.3f}")

        # Графика само с оригиналните изолинии
        fig, ax = plt.subplots(figsize=(12, 8))
        for value, group in data.groupby("Eeq_over_E2"):
            group_sorted = group.sort_values("h_over_D")
            ax.plot(group_sorted["h_over_D"], group_sorted["E1_over_E2"],
                    label=f"Eeq/E2 = {value:.2f}")

        ax.scatter([hD_point], [E1E2_point], color='red', label="Твоята точка", zorder=5)
        ax.set_xlabel("h / D")
        ax.set_ylabel("E1 / E2")
        ax.set_title("Изолинии на Eeq / E2 (от реални данни)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
