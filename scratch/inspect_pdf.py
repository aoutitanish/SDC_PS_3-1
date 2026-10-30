import pypdf
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = "data/raw/market/real_des_historical/Time-Series-3rd-AE-2025-26-English.pdf"
reader = pypdf.PdfReader(pdf_path)

print(f"Total Pages in PDF: {len(reader.pages)}")

# Print text for first 5 pages and search for price/month keywords
keywords = ["price", "wholesale", "msp", "month", "january", "february", "march", "quintal", "harvest"]

price_pages = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    lines = text.split("\n")
    print(f"\n--- PAGE {i+1} (Total Lines: {len(lines)}) ---")
    for line in lines[:12]:
        print(" ", line)
        
    has_kw = [kw for kw in keywords if kw in text.lower()]
    if has_kw:
        price_pages.append((i+1, has_kw))

print("\n================ SEARCH SUMMARY ================")
print(f"Pages containing keywords ({keywords}):")
for p_num, kws in price_pages:
    print(f"  Page {p_num}: {kws}")
