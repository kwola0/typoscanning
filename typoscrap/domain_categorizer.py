from transformers import pipeline
import requests
import csv
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from heuristics_keywords import HEURISTIC_KEYWORDS
from domain_generator import (
    generate_typo_domains,
    load_tlds,
    load_subdomains,
    load_keyboard_proximity,
    load_prefixes_and_suffixes,
    load_similar_chars
)
from dns_check import check_domain_exists
from urllib.parse import quote_plus
import os

load_dotenv()

classifier_toxic = pipeline("text-classification", model="unitary/toxic-bert")
classifier_spam = pipeline("text-classification", model="mrm8488/bert-tiny-finetuned-sms-spam-detection")
classifier_formality = pipeline("text-classification", model="s-nlp/xlmr_formality_classifier")

SHOW_AI_CONFIDENCE = True

# DeepL with Google Translate fallback
def translate_with_deepl(text, target_lang="EN"):
    api_key = os.getenv("DEEPL_API_KEY")
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": api_key,
        "text": text,
        "target_lang": target_lang
    }
    try:
        response = requests.post(url, data=data)
        result = response.json()
        return result["translations"][0]["text"]
    except Exception as e:
        print(f"[DeepL Error] {e} → trying fallback")
        try:
            g_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={quote_plus(text)}"
            g_resp = requests.get(g_url)
            g_result = g_resp.json()
            return " ".join([part[0] for part in g_result[0]])
        except Exception as g_e:
            print(f"[Google Translate Fallback Error] {g_e}")
            return text

# Classify domain content using AI and heuristics
def classify_domain_content(domain):
    try:
        response = requests.get(f"http://{domain}", timeout=5)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        if len(text) > 5000:
            text = text[:5000]

        if not text.strip():
            print(f"[SKIP] Empty or invalid content on {domain}")
            return "No content", text, 0.0, 0.0, 0.0

        translated = translate_with_deepl(text).lower()

        # AI-based classification
        toxic = classifier_toxic(translated)[0]
        spam = classifier_spam(translated)[0]
        formality = classifier_formality(translated)[0]

        if SHOW_AI_CONFIDENCE:
            print(f"[AI] TOXIC: {toxic['label']} ({toxic['score']:.2f}) | SPAM: {spam['label']} ({spam['score']:.2f}) | FORMALITY: {formality['label']} ({formality['score']:.2f})")

        if toxic["label"].lower() == "toxic" and toxic["score"] > 0.8:
            return "Scam", text, toxic["score"], spam["score"], formality["score"]
        elif spam["label"].lower() == "spam" and spam["score"] > 0.8:
            return "Affiliate abuse", text, toxic["score"], spam["score"], formality["score"]
        elif formality["label"].lower() == "formal" and formality["score"] > 0.85:
            return "Authoritative", text, toxic["score"], spam["score"], formality["score"]

        # Fallback to heuristics only if AI returns "Other"
        for category, keywords in HEURISTIC_KEYWORDS.items():
            if any(kw in translated for kw in keywords):
                return category, text, toxic["score"], spam["score"], formality["score"]

        return "Other", text, toxic["score"], spam["score"], formality["score"]

        toxic = classifier_toxic(translated)[0]
        spam = classifier_spam(translated)[0]
        formality = classifier_formality(translated)[0]

        if SHOW_AI_CONFIDENCE:
            print(f"[AI] TOXIC: {toxic['label']} ({toxic['score']:.2f}) | SPAM: {spam['label']} ({spam['score']:.2f}) | FORMALITY: {formality['label']} ({formality['score']:.2f})")

        if toxic["label"].lower() == "toxic" and toxic["score"] > 0.8:
            return "Scam", text, toxic["score"], spam["score"], formality["score"]
        elif spam["label"].lower() == "spam" and spam["score"] > 0.8:
            return "Affiliate abuse", text, toxic["score"], spam["score"], formality["score"]
        elif formality["label"].lower() == "formal" and formality["score"] > 0.85:
            return "Authoritative", text, toxic["score"], spam["score"], formality["score"]

        return "Other", text, toxic["score"], spam["score"], formality["score"]
    except Exception as e:
        print(f"[ERROR] Failed to classify {domain}: {e}")
        return "Crawl error", "", 0.0, 0.0, 0.0

# Full scanner using typo generation + classification + export

def scan_and_classify_typo_domains(domain_name, writer):
    base_dir = os.path.join(os.path.dirname(__file__), "lists")
    tlds = load_tlds(os.path.join(base_dir, "tlds_100.txt"))
    subdomains = load_subdomains(os.path.join(base_dir, "subdomains.txt"))
    keyboard_map = load_keyboard_proximity(os.path.join(base_dir, "keyboard_proximity.txt"))
    entries = load_prefixes_and_suffixes(os.path.join(base_dir, "prefixes_suffixes.txt"))
    similar_chars = load_similar_chars(os.path.join(base_dir, "similar_chars.txt"))

    typo_domains = generate_typo_domains(domain_name, tlds, similar_chars, keyboard_map, subdomains, entries)

    for typo in typo_domains:
        if check_domain_exists(typo):
            if "-" in typo:
                squatting_type = "prefix/suffix"
            elif any(c in typo for c in ["0", "1", "@"]):
                squatting_type = "visual"
            elif any(c in typo for c in ["a", "s", "d", "f"]):
                squatting_type = "keyboard"
            else:
                squatting_type = "unknown"

            label, content, t_score, s_score, f_score = classify_domain_content(typo)
            writer.writerow([domain_name, typo, squatting_type, label, f"{t_score:.2f}", f"{s_score:.2f}", f"{f_score:.2f}", content])
            print(f"[FOUND] {typo} => {label}")

# Run from file list
def load_domains_from_file(file_path):
    domains = []
    ext = os.path.splitext(file_path)[1].lower()
    with open(file_path, newline='', encoding='utf-8') as file:
        if ext == ".csv":
            reader = csv.reader(file)
            for row in reader:
                if row:
                    domains.append(row[0].strip())
        elif ext == ".txt":
            for line in file:
                clean = line.strip()
                if clean:
                    domains.append(clean)
    return domains

if __name__ == "__main__":
    input_file = "domains/domains_part3.csv"
    output_file = "results/scan_results_3.csv"
    domain_list = load_domains_from_file(input_file)

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Original Domain", "Typo Variant", "Squatting Type", "Category", "Toxic Score", "Spam Score", "Formality Score", "Scraped Content"])
        for domain in domain_list:
            print(f"\n--- Scanning {domain} ---")
            scan_and_classify_typo_domains(domain, writer)
