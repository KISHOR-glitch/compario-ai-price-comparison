from models import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    cart = db.relationship("Cart", backref="user", uselist=False)
    history = db.relationship("SearchHistory", backref="user", lazy=True)
    favorites = db.relationship("Favorite", backref="user", lazy=True)


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    items = db.relationship("CartItem", backref="cart", lazy=True)


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"))
    title = db.Column(db.String(300))
    price = db.Column(db.String(50))
    link = db.Column(db.String(500))
    quantity = db.Column(db.Integer, default=1)


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    query = db.Column(db.String(200))
    ocr_text = db.Column(db.String(300))
    top_prediction = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=db.func.now())

    results = db.relationship("SearchResult", backref="history", lazy=True)


class SearchResult(db.Model):
    __tablename__ = "search_results"

    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey("search_history.id"))
    site = db.Column(db.String(50))
    title = db.Column(db.String(300))
    price = db.Column(db.String(50))
    link = db.Column(db.String(500))
    image = db.Column(db.String(500))


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(300))
    price = db.Column(db.String(50))
    link = db.Column(db.String(500))
    site = db.Column(db.String(50))
    added_at = db.Column(db.DateTime, default=db.func.now())
