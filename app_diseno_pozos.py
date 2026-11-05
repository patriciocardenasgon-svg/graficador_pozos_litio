import io
import re
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuración de la página
st.set_page_config(
    page_title="Graficador de Diseño de Pozos e Hidroquímica",
    layout="wide"
)

st.title("Generador de Perfiles de Pozo e Hidroquímica (Li / Na)")
st.markdown(
    "Edita las tablas a la izquierda o pega datos desde Excel. "
    "El gráfico se actualizará automáticamente a la derecha."
)

# Columnas principales de la interfaz
col_datos, col_grafico = st.columns([1.15, 1.35], gap="large")

with col_datos:
    st.subheader("1. Identificación del Pozo")
    nombre_pozo = st.text_input("Nombre / Código del Pozo:", value="LI.PC.RW-08")

    st.subheader("2. Diseño Constructivo")
    st.caption("Puedes modificar valores, agregar filas con el símbolo '+' al final de la tabla o borrar filas seleccionándolas y presionando Supr.")
    
    # Datos por defecto iniciales
    default_well = pd.DataFrame({
        "From": [-0.5, 45.5, 63.5, 71.5, 95.5, 101.5, 125.5, 131.5, 206.5],
        "To": [45.5, 63.5, 71.5, 95.5, 101.5, 125.5, 131.5, 206.5, 213.5],
        "Item": [
            'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"',
            'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Punta Lapiz 8"'
        ]
    })

    df_well = st.data_editor(
        default_well,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "From": st.column_config.NumberColumn("Desde (m)", format="%.2f", required=True),
            "To": st.column_config.NumberColumn("Hasta (m)", format="%.2f", required=True),
            "Item": st.column_config.SelectboxColumn(
                "Elemento Constructivo",
                options=['Ciego 8"', 'Filtro 8"', 'Punta Lapiz 8"', 'Ciego 6"', 'Filtro 6"', 'Punta Lapiz 6"'],
                required=True
            )
        },
        key="editor_well"
    )

    st.subheader("3. Intervalos de Ensayo y Química (Li / Na)")
    
    # Menú rápido para personalizar los colores de los ensayos de Packer
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        color_doble = st.color_picker("Color Packer Doble", value="#AB47BC")
    with col_c2:
        color_libre = st.color_picker("Color Packer Punta Libre", value="#00897B")

    default_tests = pd.DataFrame({
        "TIPO_DE_ENSAYO": [
            "Packer Doble-03",
            "Packer Doble-02",
            "Packer Doble-01",
            "Packer Punta Libre"
        ],
        "DESDE": [44.04, 64.47, 95.32, 158.48],
        "HASTA": [64.47, 96.52, 129.60, 204.51],
        "Li_ppm": [118.0, 125.0, 124.0, 127.0],
        "Na_ppm": [114281.0, 113390.0, 112627.0, 107054.0]
    })

    df_tests = st.data_editor(
        default_tests,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "TIPO_DE_ENSAYO": st.column_config.TextColumn("Nombre / Tipo de Ensayo", required=True),
            "DESDE": st.column_config.NumberColumn("Desde (m)", format="%.2f", required=True),
            "HASTA": st.column_config.NumberColumn("Hasta (m)", format="%.2f", required=True),
            "Li_ppm": st.column_config.NumberColumn("Li (ppm)", format="%.1f", required=True),
            "Na_ppm": st.column_config.NumberColumn("Na (ppm)", format="%.0f", required=True),
        },
        key="editor_tests"
