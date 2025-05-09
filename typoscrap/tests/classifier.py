from transformers import pipeline
import requests
import csv
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typoscrap.heuristics_keywords import HEURISTIC_KEYWORDS

load_dotenv()

classifier_toxic = pipeline("text-classification", model="unitary/toxic-bert")
classifier_spam = pipeline("text-classification", model="mrm8488/bert-tiny-finetuned-sms-spam-detection")
classifier_legal = pipeline("text-classification", model="oliverguhr/german-legal-bert")

SHOW_AI_CONFIDENCE = True

# Classify domain content using AI and heuristics
def classify_domain_content(domain):
    try:
        response = requests.get(f"http://{domain}", timeout=5)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        if len(text) > 5000:
            text = text[:5000]

        lowered = text.lower()

        for category, keywords in HEURISTIC_KEYWORDS.items():
            if any(kw in lowered for kw in keywords):
                return category, text, 0.0, 0.0, 0.0

        toxic = classifier_toxic(lowered)[0]
        spam = classifier_spam(lowered)[0]
        legal = classifier_legal(lowered)[0]

        if SHOW_AI_CONFIDENCE:
            print(f"[AI] TOXIC: {toxic['label']} ({toxic['score']:.2f}) | SPAM: {spam['label']} ({spam['score']:.2f}) | LEGAL: {legal['label']} ({legal['score']:.2f})")

        if toxic["label"].lower() == "toxic" and toxic["score"] > 0.8:
            return "Scam", text, toxic["score"], spam["score"], legal["score"]
        elif spam["label"].lower() == "spam" and spam["score"] > 0.8:
            return "Affiliate abuse", text, toxic["score"], spam["score"], legal["score"]
        elif "legal" in legal["label"].lower() or legal["score"] > 0.85:
            return "Authoritative", text, toxic["score"], spam["score"], legal["score"]

        return "Other", text, toxic["score"], spam["score"], legal["score"]
    except Exception as e:
        print(f"[ERROR] Failed to classify {domain}: {e}")
        return "Crawl error", "", 0.0, 0.0, 0.0

# Full scan and CSV export for typo domains

def scan_and_classify_domains(domain_list):
    csv_file = "../results/scan_results.csv"
    file_exists = False

    for domain in domain_list:
        print(f"[SCAN] Processing {domain}...")
        label, content, t_score, s_score, l_score = classify_domain_content(domain)

        write_header = not file_exists and not os.path.exists(csv_file)
        with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["Domain", "Category", "Toxic Score", "Spam Score", "Legal Score", "Scraped Content"])
            writer.writerow([domain, label, f"{t_score:.2f}", f"{s_score:.2f}", f"{l_score:.2f}", content])
        file_exists = True
        print(f"[DONE] {domain} => {label}\n")

# Run test
if __name__ == "__main__":
    test_domains = ["pw.edu.pl"]
    scan_and_classify_domains(test_domains)
