import streamlit as st
import io
from dataclasses import dataclass
from typing import List, Dict
from datetime import date
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Metal Débit", layout="wide")

PASSWORD = "metaldebit123"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("Accès sécurisé")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    st.stop()

# =========================
# MODELE
# =========================

@dataclass
class Bar:
    pieces: List[int]
    used: int
    leftover: int

# =========================
# ALGO SIMPLE
# =========================

def optimize(pieces: List[int], bar_length: int):
    bars = []
    pieces = sorted(pieces, reverse=True)

    for p in pieces:
        placed = False
        for b in bars:
            if b.used + p <= bar_length:
                b.pieces.append(p)
                b.used += p
                b.leftover = bar_length - b.used
                placed = True
                break
        if not placed:
            bars.append(Bar([p], p, bar_length - p))

    return bars

# =========================
# UI
# =========================

st.title("🧰 Metal Débit Web")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Projet")
    project = st.text_input("Nom projet")
    client = st.text_input("Client")
    bar_length = st.number_input("Longueur barre (mm)", value=6000)

    st.subheader("Pièces")
    pieces_input = st.text_area("Entrer les longueurs séparées par des virgules (ex: 1830,790,790,450)")

if st.button("Calculer"):
    if pieces_input:
        pieces = [int(x.strip()) for x in pieces_input.split(",") if x.strip().isdigit()]
        result = optimize(pieces, bar_length)

        st.subheader("Résultat")

        for i, b in enumerate(result, 1):
            st.write(f"Barre {i} : {b.pieces} | Chute : {b.leftover} mm")

        # =========================
        # EXPORT EXCEL
        # =========================

        wb = Workbook()
        ws = wb.active
        ws.append(["Barre", "Pièces", "Chute"])

        for i, b in enumerate(result, 1):
            ws.append([i, str(b.pieces), b.leftover])

        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)

        st.download_button(
            label="Télécharger Excel",
            data=excel_buffer.getvalue(),
            file_name="metal_debit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # =========================
        # EXPORT PDF
        # =========================

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Bon de débit", styles["Title"]))
        elements.append(Spacer(1, 10))

        data = [["Barre", "Découpes", "Chute"]]
        for i, b in enumerate(result, 1):
            data.append([str(i), ", ".join(map(str, b.pieces)), str(b.leftover)])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))

        elements.append(table)
        doc.build(elements)

        st.download_button(
            label="Télécharger PDF",
            data=pdf_buffer.getvalue(),
            file_name="metal_debit.pdf",
            mime="application/pdf"
        )
