import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import random


class AmazonScraper:
    def __init__(self, headers=None, save_dir="data", use_proxy=True):
        self.session = requests.Session()
        self.headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
        self.session.headers.update(self.headers)
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

        # ⚙️ Proxy configuration
        self.use_proxy = use_proxy
        self.scrapeops_key = "17c499b6-4cfa-4daa-876a-9bd0ff588808"  
        self.proxy_base = f"https://proxy.scrapeops.io/v1/?api_key={self.scrapeops_key}"

    def get_proxy(self):
        if self.use_proxy:
            return {"http": self.proxy_base, "https": self.proxy_base}
        return None

    # ✅ Vérifie si la page est un CAPTCHA
    def is_captcha_page(self, html: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        if soup.find("form", action="/errors/validateCaptcha"):
            return True
        if "Enter the characters you see below" in html or "Veuillez saisir les caractères que vous voyez ci-dessous" in html:
            return True
        return False

    # ✅ Recherche du produit et récupération de l’ASIN
    def search_product(self, name: str) -> str:
        search_url = f"https://www.amazon.fr/s?k={name.replace(' ', '+')}"
        print(f"🔍 Recherche du produit : {search_url}")

        r = self.session.get(search_url, proxies=self.get_proxy(), timeout=15)
        if self.is_captcha_page(r.text):
            raise Exception("⚠️ Captcha détecté sur la recherche — essaie de réexécuter plus tard.")

        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.select_one("div[data-asin][data-component-type='s-search-result']")
        if not link:
            raise Exception("Produit non trouvé — vérifie le mot-clé ou un éventuel captcha.")
        asin = link.get("data-asin")
        if not asin:
            raise Exception("ASIN introuvable")
        print(f"✅ ASIN trouvé : {asin}")
        return asin

    # ✅ Scraping des avis
    def scrape_reviews(self, asin: str, max_pages: int = 1) -> list:
        all_reviews = []
        for page_num in range(1, max_pages + 1):
            reviews_url = f"https://www.amazon.fr/product-reviews/{asin}/?pageNumber={page_num}"
            print(f"🔍 Page {page_num} : {reviews_url}")

            try:
                resp = self.session.get(reviews_url, proxies=self.get_proxy(), timeout=20)
            except requests.RequestException as e:
                print(f"❌ Erreur proxy ou connexion : {e}")
                continue

            if resp.status_code != 200:
                print(f"❌ Page {page_num} non chargée ({resp.status_code})")
                continue

            html = resp.text

            if self.is_captcha_page(html):
                print("⚠️ Captcha détecté pendant le scraping — tentative avec un nouveau proxy...")
                time.sleep(3)
                continue

            debug_file = os.path.join(self.save_dir, f"debug_page_{page_num}.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html)

            soup = BeautifulSoup(html, "html.parser")
            reviews_divs = soup.find_all("div", {"data-hook": "review"})

            if not reviews_divs:
                print("⚠️ Aucun avis trouvé sur cette page.")
                continue

            for div in reviews_divs:
                title = div.find("a", {"data-hook": "review-title"})
                rating = div.find("i", {"data-hook": "review-star-rating"})
                body = div.find("span", {"data-hook": "review-body"})
                author = div.find("span", class_="a-profile-name")
                date = div.find("span", {"data-hook": "review-date"})

                all_reviews.append({
                    "asin": asin,
                    "title": title.text.strip() if title else "",
                    "rating": rating.text.strip().split(" ")[0] if rating else "",
                    "body": body.text.strip() if body else "",
                    "author": author.text.strip() if author else "",
                    "date": date.text.strip() if date else "",
                })

            time.sleep(random.uniform(2, 4))  # petit délai aléatoire

        print(f"✅ Total avis récupérés : {len(all_reviews)}")
        return all_reviews

    # ✅ Sauvegarde JSON
    def save_reviews(self, reviews: list, asin: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_dir, f"{asin}_reviews_{timestamp}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        print(f"💾 Avis sauvegardés dans {filename}")
        return filename

    # ✅ Fonction principale
    def full_scrape_by_name(self, product_name: str, pages=1) -> dict:
        asin = self.search_product(product_name)
        reviews = self.scrape_reviews(asin, max_pages=pages)
        file_path = self.save_reviews(reviews, asin)

        return {
            "product_name": product_name,
            "asin": asin,
            "reviews_count": len(reviews),
            "file": file_path,
            "status": "success" if reviews else "warning",
            "message": "Scraping terminé avec succès." if reviews else "Aucun avis trouvé ou captcha détecté."
        }
