import io
from pathlib import Path
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF

from parsing import parse_invoice
from core import InvoiceRow
from excel import save_row

st.set_page_config(page_title="Invoice → Excel", page_icon="📄", layout="centered")
st.title("📄→📊 Invoice to Excel")

with st.sidebar:
    excel_path_str = st.text_input(
        "Desired Excel File Path",
        value=str(Path.cwd() / "test.xlsx"),
    )
    excel_path = Path(excel_path_str)

uploaded = st.file_uploader("Drag 'N' & drop an invoice PDF", type=["pdf"])
if uploaded:
    # Preview first page
    try:
        doc = fitz.open(stream=uploaded.getvalue(), filetype="pdf")
        pix = doc[0].get_pixmap(dpi=160)
        st.image(pix.tobytes("png"), caption="Preview of page 1", use_container_width=True)
    except Exception:
        st.info("Preview not available.")

    if st.button("🔎 Parse invoice"):
        # For now, stub one row you can edit. We’ll replace next step.
        stub = {
            "invoice_no": "",
            "invoice_date": "",
            "due_date": "",
            "employee": "",
            "period": "",
            "hours": 0.0,
            "rate": 0.0,
            "amount": 0.0,
            "hst": 0.0,
            "total": 0.0,
        }
        st.session_state["parsed_df"] = pd.DataFrame([stub])
        st.toast("Parsed (stub). Edit below.", icon="✅")

if "parsed_df" in st.session_state:
    st.subheader("Review data (editable)")
    edited = st.data_editor(st.session_state["parsed_df"], num_rows="fixed", use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save to Excel"):
            from core.models import InvoiceRow
            row = InvoiceRow(**edited.iloc[0].to_dict())
            try:
                save_row(excel_path, row)
                st.success(f"Saved to '{excel_path.name}' (sheet: {row.employee}).")
                st.balloons()
            except Exception as e:
                st.error(f"Save failed: {e}")