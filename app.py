import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt

# Кеширано зареждане на CSV
@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

data = load_data()

# Извличане на координати и стойности
points = data[['h_over_D', 'E1_over_E2']].values
values = data['Eeq_over_E2'].values

# Функция за изчисление
def compute_Eeq(h, D, E1, E2):
    hD = h / D
    E1E2 = E1 / E2
    ratio = griddata(points, values, (hD, E1E2), method='linear')
    if np.isnan(ratio):
        return None
    return ratio * E2

# Заглавие
st.title("📐 Калкулатор: Метод на Иванов (с реални изолинии)")

# Входни полета
E1 = st.number_input("E1 (MPa)", value=2600)
E2 = st.number_input("E2 (MPa)", value=3000)
h = st.number_input("h (cm)", value=20)
D = st.number_input("D (cm)", value=40)

# Показване на въведени стойности
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
    interp_ratio = result / E2 if result else None

    if result is None:
        st.warning("Извън обхвата на таблицата. Добави още изолинии.")
    else:
        st.success(f"Eeq = {result:.2f} MPa")
        st.info(f"Eeq / E2 = {interp_ratio:.3f}")

        # ---- Намиране на две съседни изолинии ----
        iso_levels = sorted(data["Eeq_over_E2"].unique())
        lower, upper = None, None

        for i in range(len(iso_levels) - 1):
            if iso_levels[i] <= interp_ratio <= iso_levels[i + 1]:
                lower = iso_levels[i]
                upper = iso_levels[i + 1]
                break

        if lower is not None and upper is not None:
            st.info(f"📈 Точката е между изолинии Eeq/E2 = {lower:.2f} и {upper:.2f}")
        else:
            st.warning("Точката съвпада с изолиния или е извън обхвата.")

        # ---- Графика ----
        fig, ax = plt.subplots(figsize=(12, 8))

        for value, group in data.groupby("Eeq_over_E2"):
            group_sorted = group.sort_values("h_over_D")

            if value == lower or value == upper:
                ax.plot(group_sorted["h_over_D"], group_sorted["E1_over_E2"],
                        linewidth=3, linestyle='--', color='blue',
                        label=f"★ Eeq/E2 = {value:.2f}")
            else:
                ax.plot(group_sorted["h_over_D"], group_sorted["E1_over_E2"],
                        linewidth=1, alpha=0.5, label=f"Eeq/E2 = {value:.2f}")

        # Добавяне на точката
        ax.scatter([hD_point], [E1E2_point], color='red', s=100, zorder=5, label="Твоята точка")

        ax.set_xlabel("h / D")
        ax.set_ylabel("E1 / E2")
        ax.set_title("Изолинии на Eeq / E2 (от реални данни)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
