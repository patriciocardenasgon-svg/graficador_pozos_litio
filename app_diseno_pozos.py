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
    nombre_pozo = st.text_input("Nombre / Código del Pozo:", value="LI.PC.RW-03")

    st.subheader("2. Diseño Constructivo")
    st.caption("Puedes modificar valores, agregar filas con el símbolo '+' al final de la tabla o borrar filas seleccionándolas y presionando Supr.")
    
    # Datos por defecto completos hasta los 355 metros
    default_well = pd.DataFrame({
        "From": [0, 20, 25, 28, 31, 34, 37, 40, 61, 87, 96, 102, 123, 134, 143, 161, 311, 314, 317, 320, 323, 326, 332],
        "To": [20, 25, 28, 31, 34, 37, 40, 61, 87, 96, 102, 123, 134, 143, 161, 311, 314, 317, 320, 323, 326, 332, 355],
        "Item": [
            'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"',
            'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"',
            'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Ciego 8"', 'Filtro 8"', 'Punta Lapiz 8"'
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
    )

with col_grafico:
    st.subheader("Vista Previa del Perfil")

    # Limpieza estricta de filas vacías
    df_well = df_well.dropna(subset=["From", "To", "Item"]).copy()
    df_tests = df_tests.dropna(subset=["TIPO_DE_ENSAYO", "DESDE", "HASTA", "Li_ppm", "Na_ppm"]).copy()

    if df_well.empty:
        st.warning("Ingresa al menos un tramo en la tabla de Diseño Constructivo.")
    else:
        # Asegurar orden correcto entre Desde y Hasta en ensayos
        if not df_tests.empty:
             d_min = df_tests[["DESDE", "HASTA"]].min(axis=1)
             d_max = df_tests[["DESDE", "HASTA"]].max(axis=1)
             df_tests["DESDE"] = d_min
             df_tests["HASTA"] = d_max
             df_tests["Mid_m"] = (df_tests["DESDE"] + df_tests["HASTA"]) / 2.0
             df_tests = df_tests.sort_values(by="Mid_m").reset_index(drop=True)

        # Configuración de estilos
        styles_well = {
            "Ciego": {"color": "#90CAF9", "hatch": "", "label": "Tubería Ciega"},
            "Filtro": {"color": "#FFB74D", "hatch": "///", "label": "Filtro Ranurado"},
            "Punta Lapiz": {"color": "#78909C", "hatch": "", "label": "Punta Lápiz"},
        }

        def get_test_style(tipo):
            if "doble" in str(tipo).lower():
                return {"color": "#AB47BC", "alpha": 0.18, "label": "Tramo Packer Doble"}
            return {"color": "#00897B", "alpha": 0.18, "label": "Tramo Packer Punta Libre"}

        # Creación de la figura Matplotlib con altura proporcional a los 355 metros
        fig, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(12, 18), sharey=True, gridspec_kw={"width_ratios": [1, 1.4]}
        )

        # ----------------- COLUMNA 1: DISEÑO CONSTRUCTIVO -----------------
        pipe_w = 1.0
        half_w = pipe_w / 2.0

        for _, row in df_well.iterrows():
            top, bottom, item = float(row["From"]), float(row["To"]), str(row["Item"])
            h = bottom - top

            key = next((k for k in styles_well if k in item), "Ciego")
            style = styles_well[key]

            # Limpieza automática del texto interno (quita las pulgadas para que no sature)
            item_limpio = re.sub(r'\b\d+\s*(?:"| pulgadas)?', '', item).strip()

            if "Punta Lapiz" in item:
                pencil = patches.Polygon(
                    [(-half_w, top), (half_w, top), (0.0, bottom)],
                    closed=True, linewidth=1.3, edgecolor="black", facecolor=style["color"]
                )
                ax1.add_patch(pencil)
                ax1.text(
                    -half_w - 0.15, (top + bottom) / 2.0, f"{item_limpio}\n({h:.1f} m)",
                    ha="right", va="center", fontsize=6, weight="bold"
                )
            else:
                rect = patches.Rectangle(
                    (-half_w, top), pipe_w, h,
                    linewidth=1.2, edgecolor="black", facecolor=style["color"], hatch=style["hatch"]
                )
                ax1.add_patch(rect)
                
                # Control anti-amontonamiento inteligente para tramos de pocos metros:
                # Si el tramo mide más de 4 metros, muestra nombre y longitud.
                # Si mide entre 2 y 4 metros, muestra solo el nombre.
                # Si es menor a 2 metros, no pone texto dentro para evitar manchas, la profundidad se lee al lado.
                mid_y = (top + bottom) / 2.0
                if h >= 4.0:
                    ax1.text(0, mid_y, f"{item_limpio}\n({h:.1f} m)", ha="center", va="center", fontsize=6, weight="bold", color="#0D47A1")
                elif h >= 2.0:
                    ax1.text(0, mid_y, item_limpio, ha="center", va="center", fontsize=5.5, weight="bold", color="#0D47A1")

            # Marcar la profundidad inferior en el lateral derecho de la columna
            ax1.text(
                half_w + 0.1, bottom, f"{bottom:.1f} m",
                va="center", ha="left", fontsize=7, color="#333333"
            )

        ax1.text(
            half_w + 0.1, float(df_well["From"].iloc[0]), f"{float(df_well['From'].iloc[0]):.1f} m",
            va="center", ha="left", fontsize=7, color="#333333"
        )
        ax1.axhline(0.0, color="#D32F2F", linestyle=":", linewidth=1.2)
        ax1.text(
            -half_w - 0.15, 0.0, "Terreno (0.0 m)",
            va="center", ha="right", fontsize=8, color="#D32F2F", weight="bold"
        )

        ax1.set_xlim(-2.8, 2.5)
        ax1.set_title(f"Diseño Constructivo - {nombre_pozo}\n(Diámetro general: 8 pulgadas)", fontsize=10, weight="bold", pad=25)
        ax1.set_ylabel("Profundidad (m bbp)", fontsize=10, weight="bold")
        ax1.get_xaxis().set_visible(False)
        ax1.grid(axis="y", linestyle="--", alpha=0.4)

        # ----------------- COLUMNA 2: INTERVALOS + Li Y Na -----------------
        if not df_tests.empty:
            for _, row in df_tests.iterrows():
                top, bottom = float(row["DESDE"]), float(row["HASTA"])
                ensayo_tipo = str(row["TIPO_DE_ENSAYO"])
                h = bottom - top
                cfg_t = get_test_style(ensayo_tipo)

                ax2.axhspan(top, bottom, color=cfg_t["color"], alpha=cfg_t["alpha"], edgecolor="none")
                ax2.axhline(top, color="#455A64", linestyle="--", linewidth=0.8, alpha=0.6)
                ax2.axhline(bottom, color="#455A64", linestyle="--", linewidth=0.8, alpha=0.6)

                mid = (top + bottom) / 2.0
                info_str = f"{ensayo_tipo}\n{top:.2f} - {bottom:.2f} m\n(L: {h:.2f} m)"
                ax2.text(
                    0.02, mid, info_str,
                    transform=ax2.get_yaxis_transform(),
                    ha="left", va="center", fontsize=7.5, weight="bold", color="#263238",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=cfg_t["color"], alpha=0.85)
                )

            # Curva de Litio (Eje inferior)
            ax2.plot(
                df_tests["Li_ppm"], df_tests["Mid_m"],
                marker="o", markersize=7, color="#C2185B", linewidth=2, linestyle="-"
            )
            for _, row in df_tests.iterrows():
                ax2.text(
                    row["Li_ppm"] + 0.3, row["Mid_m"] - 1.2, f"{row['Li_ppm']:.0f} ppm",
                    va="bottom", ha="left", fontsize=8, weight="bold", color="#C2185B"
                )

            ax2.set_xlabel("Li (ppm)", fontsize=10, weight="bold", color="#C2185B")
            ax2.tick_params(axis="x", labelcolor="#C2185B")
            li_min, li_max = df_tests["Li_ppm"].min(), df_tests["Li_ppm"].max()
            span_li = max(li_max - li_min, 10)
            ax2.set_xlim(li_min - span_li * 1.3, li_max + span_li * 0.6)
            ax2.grid(True, linestyle="--", alpha=0.35)

            # Curva de Sodio (Eje superior)
            ax2_na = ax2.twiny()
            ax2_na.plot(
                df_tests["Na_ppm"], df_tests["Mid_m"],
                marker="s", markersize=6, color="#0277BD", linewidth=2, linestyle="--"
            )
            for _, row in df_tests.iterrows():
                ax2_na.text(
                    row["Na_ppm"] + 150, row["Mid_m"] + 1.2, f"{row['Na_ppm']:,.0f} ppm",
                    va="top", ha="left", fontsize=8, weight="bold", color="#0277BD"
                )

            ax2_na.set_xlabel("Na (ppm)", fontsize=10, weight="bold", color="#0277BD")
            ax2_na.tick_params(axis="x", labelcolor="#0277BD")
            na_min, na_max = df_tests["Na_ppm"].min(), df_tests["Na_ppm"].max()
            span_na = max(na_max - na_min, 1000)
            ax2_na.set_xlim(na_min - span_na * 0.9, na_max + span_na * 0.35)

        max_depth = max(
            df_well["To"].max(),
            df_tests["HASTA"].max() if not df_tests.empty else 0
        )
        ax1.set_ylim(max_depth + 10, -10)

        # ----------------- LEYENDA UNIFICADA -----------------
        legend_well = [
            patches.Patch(facecolor=v["color"], hatch=v["hatch"], edgecolor="black", label=v["label"])
            for v in styles_well.values()
        ]
        legend_tests = [
            patches.Patch(facecolor="#AB47BC", alpha=0.25, edgecolor="#455A64", label="Tramo Packer Doble"),
            patches.Patch(facecolor="#00897B", alpha=0.25, edgecolor="#455A64", label="Tramo Packer Punta Libre"),
        ]
        legend_chem = [
            plt.Line2D([0], [0], color="#C2185B", marker="o", linewidth=2, label="Concentración Li (ppm)"),
            plt.Line2D([0], [0], color="#0277BD", marker="s", linewidth=2, linestyle="--", label="Concentración Na (ppm)"),
        ]

        ax2.legend(
            handles=legend_well + legend_tests + legend_chem,
            loc="upper left", bbox_to_anchor=(1.05, 1.0),
            title="Referencias", title_fontsize="10", fontsize=8.5, frameon=True
        )

        plt.subplots_adjust(top=0.88, wspace=0.15)
        st.pyplot(fig)

        # Botón para descargar la imagen en alta calidad
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        st.download_button(
            label="📥 Descargar Gráfico en Alta Resolución (PNG)",
            data=buf.getvalue(),
            file_name=f"Perfil_Pozo_{nombre_pozo}.png",
            mime="image/png",
            use_container_width=True
        )
