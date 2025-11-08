from flask import Flask, request, jsonify

from amazon_scraper import AmazonScraper

app = Flask(__name__)
scraper = AmazonScraper()  # Crée l'objet scraper

@app.route("/run", methods=["POST"])
def run_function():
    try:
        # Récupère les données JSON envoyées
        data = request.get_json(force=True)
        if not data:
            data = request.form.to_dict()  # accepte aussi form-data

        product_name = data.get("product_name")
        pages = int(data.get("pages", 1))

        # Vérification
        if not product_name:
            return jsonify({"error": "Missing 'product_name' field"}), 400

        # Forcer pages à être un entier
        try:
            pages = int(pages)
        except ValueError:
            return jsonify({"error": "'pages' must be an integer"}), 400

        # Appel du scraper
        result = scraper.full_scrape_by_name(product_name,pages)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # debug=True pour voir les erreurs et rechargement automatique
    app.run(host="0.0.0.0", port=5000, debug=True)
