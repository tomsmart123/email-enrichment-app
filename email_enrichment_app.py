import pandas as pd
import requests
from serpapi import GoogleSearch
from openai import OpenAI
import re

# === API KEYS ===
openai_key = "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"
hunter_key = "aebcc2eb6d8b639149532b7c74fdadb5b00c8e2c"
serpapi_key = "b39cfb0f232ecfef22c89b326e6123cb5fc08e5919504e37c7880b88f3689ce9"
client = OpenAI(api_key=openai_key)

# === Nickname Map ===
nicknames_map = {
    "robert": ["bob", "rob"],
    "william": ["bill", "will"],
    "richard": ["rick", "rich"],
    "james": ["jim", "jamie"],
    "john": ["jack", "johnny"],
    "stephen": ["steve", "stevie"],
    "michael": ["mike"],
    "christopher": ["chris"],
    "edward": ["ed", "eddie"],
}

def normalize_domain(domain):
    return re.sub(r"^(www\.|beta\.)", "", domain)

def get_domain_serpapi(company):
    search = GoogleSearch({
        "q": f"{company} official site",
        "api_key": serpapi_key
    })
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
