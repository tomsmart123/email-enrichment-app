import streamlit as st
import pandas as pd
from email_enrichment_app import enrich_contacts

st.set_page_config(page_title="Email Enrichment Platform", layout="wide")

st.title("📬 Email Enrichment Tool")
st.markdown("Upload a CSV with columns: `Name`, `Company`, `Position`, `LinkedIn URL`, `Number`")

uploaded_file = st.file_uploader("Choose your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} contacts")
        enriched_df = enrich_contacts(df)
        st.dataframe(enriched_df)

        csv_data = enriched_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Enriched CSV", csv_data, "enriched_contacts.csv", "text/csv")
    except Exception as e:
        st.error(f"⚠️ Something went wrong: {e}")
