import pandas as pd
import requests
from serpapi import GoogleSearch
from openai import OpenAI
import re

# === API KEYS ===
openai_key = "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"
hunter_key = "aba3888d517de289eed46386ccd5d10f20b66d72"
serpapi_key = "b39cfb0f232ecfef22c89b326e6123cb5fc08e5919504e37c7880b88f3689ce9"
client = OpenAI(api_key=openai_key)

# === Nickname Map ===
nicknames_map = {
    "robert": ["bob", "rob"], "william": ["bill", "will"],
    "richard": ["rick", "rich"], "james": ["jim", "jamie"],
    "john": ["jack", "johnny"], "stephen": ["steve", "stevie"],
    "michael": ["mike"], "christopher": ["chris"], "edward": ["ed", "eddie"]
}

def normalize_domain(domain):
    return re.sub(r"^(www\.|beta\.)", "", domain)

def get_domain_serpapi(company):
    search = GoogleSearch({"q": f"{company} official site", "api_key": serpapi_key})
    results = search.get_dict()
    for r in results.get("organic_results", []):
        if "link" in r:
            return normalize_domain(r["link"].split("/")[2])
    return None

def enrich_email_with_ai(name, company, domain, position, linkedin):
    prompt = (
        f"Generate the most likely professional email for '{name}' at '{company}' (domain: {domain}), "
        f"role: {position}, LinkedIn: {linkedin}. Only give the email."
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=30
    )
    return response.choices[0].message.content.strip()

def verify_email_hunter(email):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={hunter_key}"
    data = requests.get(url).json().get("data", {})
    return {
        "email": email,
        "status": data.get("status"),
        "result": data.get("result"),
        "smtp_check": data.get("smtp_check"),
        "score": data.get("score"),
        "catch_all": data.get("catch_all")
    }

def generate_possible_emails(first, last, domain, nicknames=None):
    base = [
        f"{first}@{domain}", f"{last}@{domain}", f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}", f"{first}{last}@{domain}", f"{first}_{last}@{domain}",
        f"{last}{first}@{domain}", f"{first[0]}.{last}@{domain}", f"{first}-{last}@{domain}",
        f"{last}.{first}@{domain}", f"{first[0]}{last[0]}@{domain}", f"{first[:2]}{last[:2]}@{domain}",
        f"{first}.{last[0]}@{domain}", f"{last}.{first[0]}@{domain}", f"{first[0]}_{last}@{domain}"
    ]
    if nicknames:
        for nn in nicknames:
            base += [
                f"{nn}@{domain}", f"{nn}.{last}@{domain}", f"{nn[0]}{last}@{domain}"
            ]
    return list(set(base))

def enrich_contacts(df):
    results = []
    for _, row in df.iterrows():
        full_name = str(row["Name"]).strip()
        first_name, last_name = (full_name.split(" ", 1) + [""])[:2]
        company = str(row.get("Company", ""))
        phone = str(row.get("Number", ""))
        position = str(row.get("Position", ""))
        linkedin = str(row.get("LinkedIn URL", ""))
        name = f"{first_name} {last_name}"

        domain = get_domain_serpapi(company)
        if not domain:
            results.append({
                "Name": name, "Company": company, "Phone": phone, "Position": position, "LinkedIn URL": linkedin,
                "AI Email": "", "Verified Email": "", "Status": "No Domain", "Email Status": "", "Email Result": "",
                "SMTP Check": "", "Score": "", "Catch-All": "", "Email Patterns": ""
            })
            continue

        ai_email = enrich_email_with_ai(name, company, domain, position, linkedin)
        nicknames = nicknames_map.get(first_name.lower(), [])
        email_patterns = generate_possible_emails(first_name.lower(), last_name.lower(), domain, nicknames)

        verified_email = None
        verification_data = {}
        for email in email_patterns:
            verification = verify_email_hunter(email)
            if verification["result"] in ["deliverable", "risky"]:
                verified_email = verification["email"]
                verification_data = verification
                break

        if not verified_email:
            verification_data = {"status": "", "result": "", "smtp_check": "", "score": "", "catch_all": ""}

        results.append({
            "Name": name, "Company": company, "Phone": phone, "Position": position, "LinkedIn URL": linkedin,
            "AI Email": ai_email, "Verified Email": verified_email or "", "Status": "Matched" if verified_email else "No Match",
            "Email Status": verification_data["status"], "Email Result": verification_data["result"],
            "SMTP Check": verification_data["smtp_check"], "Score": verification_data["score"],
            "Catch-All": verification_data["catch_all"], "Email Patterns": "\n".join(email_patterns)
        })

    return pd.DataFrame(results)
