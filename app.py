import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

data = load_data()

def compute_Eeq(h, D, E1, E2):
    hD = h / D
    E1E2 = E1 / E2

    iso_levels = sorted(data['Eeq_over_E2'].unique())
    for low, high in zip(iso_levels, iso_levels[1:]):
        grp_low = data[data['Eeq_over_E2'] == low].sort_values('h_over_D')
        grp_high = data[data['Eeq_over_E2'] == high].sort_values('h_over_D')

        # Проверка дали h/D попада в обхвата на двете изолинии
        if not (grp_low['h_over_D'].min() <= hD <= grp_low['h_over_D'].max() and
                grp_high['h_over_D'].min() <= hD <= grp_high['h_over_D'].max()):
            continue

        # Интерполираме E1/E2 при зададеното h/D
        y_low = np.interp(hD, grp_low['h_over_D'], grp_low['E1_over_E2'])
        y_high = np.interp(hD, grp_high['h_over_D'], grp_high['E1_over_E2'])

        # Ако точката е между двете изолинии
        if y_low <= E1E2 <= y_high:
            frac = (E1E2 - y_low) / (y_high - y_low)
            eq_over_e2 = low + frac * (high - low)
            return eq_over_e2 * E2

    return None  # Извън диапазона на наличните изолинии

st.title("📐 Калкулатор: Метод на Иванов (само между изолинии)")

# Входни полета
E1 = st.number_input("E1 (MPa)", value=2600)
E2 = st.number_input("E2 (MPa)", value=3000)
h = st.number_input("h (cm)", value=20)
D = st.number_input("D (cm)", value=40)

# Показване на изходните съотношения
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

        # Графика на реалните изолинии
        fig, ax = plt.subplots(figsize=(12, 8))
        for value, group in data.groupby("Eeq_over_E2"):
            group_sorted = group.sort_values("h_over_D")
            ax.plot(group_sorted["h_over_D"], group_sorted["E1_over_E2"],
                    label=f"Eeq/E2 = {value:.2f}")

        ax.scatter([hD_point], [E1E2_point], color='red', label="Твоята точка", zorder=5)
        ax.set_xlabel("h / D")
        ax.set_ylabel("E1 / E2")
        ax.set_title("Изолинии на Eeq / E2 (реални данни)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
