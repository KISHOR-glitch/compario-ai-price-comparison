# ---------------------------
# IMPORTS
# ---------------------------
import os
import uuid
import traceback
from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from PIL import Image

# Database & Models
from models import db
from models.database_models import (
    User, Cart, CartItem,
    SearchHistory, SearchResult,
    Favorite
)

# ML / OCR
try:
    import recognition_mobilenet as recognition
    HAS_MOBILENET = True
except:
    HAS_MOBILENET = False

try:
    from recognition_easyocr import extract_text as easyocr_extract_text
    HAS_EASYOCR = True
except:
    HAS_EASYOCR = False

# Selenium
try:
    from scrapers.selenium_scrap import get_browser, scrape_amazon, scrape_flipkart, scrape_myntra
except:
    get_browser = scrape_amazon = scrape_flipkart = scrape_myntra = None

# ---------------------------
# FLASK SETUP
# ---------------------------
app = Flask(__name__, template_folder="templates")
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///compario.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from models import db
db.init_app(app)

bcrypt = Bcrypt(app)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from models.database_models import User, Cart, CartItem, SearchHistory, SearchResult, Favorite


with app.app_context():
    db.create_all()


# ---------------------------
# HELPERS
# ---------------------------
def save_upload_file(file_storage):
    ext = os.path.splitext(file_storage.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(path)
    return path


def extract_text_from_image(path):
    if HAS_EASYOCR:
        try:
            return easyocr_extract_text(path)
        except:
            pass

    try:
        import pytesseract
        return pytesseract.image_to_string(Image.open(path))
    except:
        return ""


def predict_labels(path, top_k=3):
    if HAS_MOBILENET:
        try:
            return recognition.predict_product(path)[:top_k]
        except:
            pass

    return [{"name": "unknown", "confidence": 0.0}]


def normalize_selenium(site, res):
    if not res:
        return None
    return {
        "site": site,
        "title": res.get("Name", "Unknown"),
        "price": res.get("Price", "0"),
        "link": res.get("Link", "#"),
        "image": res.get("Image")
    }


def save_history(user_id, query, ocr_text, top_prediction, scraped):
    if not user_id:
        return None

    user_id = int(user_id)

    history = SearchHistory(
        user_id=user_id,
        query=query,
        ocr_text=ocr_text,
        top_prediction=top_prediction
    )
    db.session.add(history)
    db.session.commit()

    for item in scraped:
        result = SearchResult(
            history_id=history.id,
            site=item["site"],
            title=item["title"],
            price=item["price"],
            link=item["link"],
            image=item.get("image")
        )
        db.session.add(result)

    db.session.commit()
    return history.id


# ---------------------------
# PAGE ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login-page")
def login_page():
    return render_template("login.html")


@app.route("/signup-page")
def signup_page():
    return render_template("signup.html")


@app.route("/cart-page")
def cart_page():
    return render_template("cart.html")


@app.route("/favorites-page")
def favorites_page():
    return render_template("favorites.html")


@app.route("/history-page")
def history_page():
    return render_template("history.html")


# ---------------------------
# AUTH API
# ---------------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data["email"]
    password = data["password"]
    name = data.get("name", "")

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed = bcrypt.generate_password_hash(password).decode()
    user = User(name=name, email=email, password=hashed)
    db.session.add(user)
    db.session.commit()

    db.session.add(Cart(user_id=user.id))
    db.session.commit()

    return jsonify({"message": "Signup successful", "user_id": user.id})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email"}), 400

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid password"}), 400

    return jsonify({"message": "Login successful", "user_id": user.id})


@app.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logged out successfully"})


# ---------------------------
# UPLOAD API
# ---------------------------
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["image"]
        user_id = request.form.get("user_id")

        if user_id:
            user_id = int(user_id)

        saved_path = save_upload_file(file)
        ocr_text = extract_text_from_image(saved_path)
        preds = predict_labels(saved_path)
        top = preds[0]["name"]
        query = ocr_text if len(ocr_text) > 3 else top

        scraped = []
        if get_browser:
            browser = get_browser()
            try:
                scraped.append(normalize_selenium("Amazon", scrape_amazon(browser, query)))
                scraped.append(normalize_selenium("Flipkart", scrape_flipkart(browser, query)))
                scraped.append(normalize_selenium("Myntra", scrape_myntra(browser, query)))
            except:
                pass
            browser.quit()

        scraped = [s for s in scraped if s]

        history_id = save_history(user_id, query, ocr_text, top, scraped) if user_id else None

        return jsonify({
            "top_product": top,
            "detected_text": ocr_text,
            "predictions": preds,
            "scraped_results": scraped,
            "history_id": history_id
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------------------------
# CART API
# ---------------------------
@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    data = request.json
    cart = Cart.query.filter_by(user_id=int(data["user_id"])).first()

    item = CartItem(
        cart_id=cart.id,
        title=data["title"],
        price=data["price"],
        link=data["link"]
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Added to cart"})


@app.route("/cart/<int:user_id>")
def get_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    items = CartItem.query.filter_by(cart_id=cart.id).all()

    return jsonify([{
        "id": i.id,
        "title": i.title,
        "price": i.price,
        "link": i.link
    } for i in items])


@app.route("/cart/delete/<int:item_id>", methods=["DELETE"])
def delete_cart_item(item_id):
    item = CartItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({"message": "Deleted"})


# ---------------------------
# FAVORITES API
# ---------------------------
@app.route("/favorite/add", methods=["POST"])
def add_favorite():
    data = request.json
    fav = Favorite(
        user_id=int(data["user_id"]),
        title=data["title"],
        price=data["price"],
        link=data["link"],
        site=data["site"]
    )
    db.session.add(fav)
    db.session.commit()
    return jsonify({"message": "Added to favorites"})


@app.route("/favorite/<int:user_id>")
def get_favorites(user_id):
    favs = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": f.id,
        "title": f.title,
        "price": f.price,
        "link": f.link,
        "site": f.site
    } for f in favs])


@app.route("/favorite/delete/<int:item_id>", methods=["DELETE"])
def delete_favorite(item_id):
    fav = Favorite.query.get(item_id)
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return jsonify({"message": "Deleted"})


# ---------------------------
# HISTORY API
# ---------------------------
@app.route("/history/<int:user_id>")
def get_history(user_id):
    hist = db.session.query(SearchHistory).filter_by(user_id=user_id).order_by(SearchHistory.timestamp.desc()).all()
    result_list = []
    for h in hist:
        products = []
        for r in h.results:
            products.append({
                "site": r.site,
                "title": r.title,
                "price": r.price,
                    "link": r.link,
                    "image": getattr(r, "image", None)
                })
            result_list.append({
                "query": h.query,
                "ocr_text": h.ocr_text,
                "top_prediction": h.top_prediction,
                "timestamp": str(h.timestamp),
                "products": products
            })
        return jsonify(result_list)


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
