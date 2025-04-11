import streamlit as st
import pandas as pd
from email_enrichment_app import (
    enrich_email_with_ai,
    get_domain_serpapi,
    generate_possible_emails,
    verify_email_hunter,
    nicknames_map
)

st.set_page_config(page_title="Email Enrichment", layout="wide")
st.title("📧 Contact Email Enrichment (Gold Script - Web Version)")

uploaded_file = st.file_uploader("📁 Upload your contacts CSV", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)
st.success(f"✅ Loaded {len(df)} contacts")

results = []
with st.spinner("🔍 Enriching emails..."):
    for _, row in df.iterrows():
        full_name = str(row.get("Name", "")).strip()
        first_name, last_name = (full_name.split(" ", 1) + [""])[:2]
        company = str(row.get("Company", "")).strip()
        phone = str(row.get("Number", "")).strip()
        position = str(row.get("Position", "")).strip()
        linkedin = str(row.get("LinkedIn URL", "")).strip()
        name = f"{first_name} {last_name}"

        domain = get_domain_serpapi(company)
        if not domain:
            results.append({
                "Name": name,
                "Company": company,
                "Phone": phone,
                "Position": position,
                "LinkedIn URL": linkedin,
                "AI Email": "N/A",
                "Verified Email": "",
                "Status": "No Match",
                "Email Patterns": ""
            })
            continue

        ai_email = enrich_email_with_ai(name, company, domain, position, linkedin)
        nicknames = nicknames_map.get(first_name.lower(), [])
        email_patterns = generate_possible_emails(first_name.lower(), last_name.lower(), domain, nicknames)

        verified_email = None
        verification_data = {}
        status_note = "No Match"

        for email in email_patterns:
            verification = verify_email_hunter(email)
            if verification["result"] in ["deliverable", "risky"]:
                verified_email = verification["email"]
                verification_data = verification
                status_note = "Matched"
                break

        if not verified_email:
            verification_data = {
                "status": "", "result": "", "smtp_check": "",
                "score": "", "catch_all": ""
            }

        results.append({
            "Name": name,
            "Company": company,
            "Phone": phone,
            "Position": position,
            "LinkedIn URL": linkedin,
            "AI Email": ai_email,
            "Verified Email": verified_email or "",
            "Status": status_note,
            "Email Status": verification_data["status"],
            "Email Result": verification_data["result"],
            "SMTP Check": verification_data["smtp_check"],
            "Score": verification_data["score"],
            "Catch-All": verification_data["catch_all"],
            "Email Patterns": "\n".join(email_patterns)
        })

output_df = pd.DataFrame(results)
st.subheader("✅ Enrichment Results")
st.dataframe(output_df)

csv = output_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", csv, "enriched_results.csv", "text/csv")
