import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# Кеширано зареждане на данни
@st.cache_data
def load_data():
    return pd.read_csv("combined_data.csv")

# Зареждане на данните
data = load_data()
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

# Показване на параметрите
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
    interp_point = np.array([hD_point, E1E2_point])

    if result is None:
        st.warning("Извън обхвата на таблицата. Добави още изолинии.")
        triangle_vertices = None
    else:
        st.success(f"Eeq = {result:.2f} MPa")
        st.info(f"Eeq / E2 = {result / E2:.3f}")

        # --- Намери триъгълника за интерполация ---
        tri = Delaunay(points)
        simp_index = tri.find_simplex(interp_point)

        if simp_index == -1:
            st.warning("Точката е извън триангулацията – не може да се покаже триъгълник.")
            triangle_vertices = None
        else:
            vert_indices = tri.simplices[simp_index]
            triangle_vertices = points[vert_indices]

        # --- Визуализация ---
        fig, ax = plt.subplots(figsize=(12, 8))

        # Изолинии от данните
        for value, group in data.groupby("Eeq_over_E2"):
            group_sorted = group.sort_values("h_over_D")
            ax.plot(group_sorted["h_over_D"], group_sorted["E1_over_E2"],
                    label=f"Eeq/E2 = {value:.2f}")

        # Червена точка – въведена от потребителя
        ax.scatter([hD_point], [E1E2_point], color='red', label="Твоята точка", zorder=5)

        # Интерполационен триъгълник
        if triangle_vertices is not None:
            triangle = Polygon(triangle_vertices, color='orange', alpha=0.3, label="Интерполационен триъгълник")
            ax.add_patch(triangle)
            ax.plot(*zip(*triangle_vertices, triangle_vertices[0]), color='orange')

        ax.set_xlabel("h / D")
        ax.set_ylabel("E1 / E2")
        ax.set_title("Изолинии на Eeq / E2 (от реални данни)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
