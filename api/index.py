import os
import hmac
import hashlib
import random
import datetime
from functools import wraps
from flask import (Flask, request, jsonify, render_template,
                   session, redirect, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ══════════════════════════════════════════════════════════
#  APP SETUP
# ══════════════════════════════════════════════════════════
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static")
)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# SQLite locally → PostgreSQL on Vercel/Neon
_db_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE, "quickrail.db")
)
if _db_url.startswith("postgres://"):          # Neon gives postgres://, SQLAlchemy needs postgresql://
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url

db = SQLAlchemy(app)

# ── Razorpay ──────────────────────────────────────────────
RAZORPAY_KEY_ID     = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
DEMO_MODE           = not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

rzp = None
if not DEMO_MODE:
    try:
        import razorpay as _rzp
        rzp = _rzp.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        DEMO_MODE = True


# ══════════════════════════════════════════════════════════
#  DATABASE MODELS
# ══════════════════════════════════════════════════════════
class User(db.Model):
    __tablename__  = "users"
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    phone          = db.Column(db.String(15))
    password_hash  = db.Column(db.String(256), nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bookings       = db.relationship("Booking", backref="user", lazy=True)


class Booking(db.Model):
    __tablename__        = "bookings"
    id                   = db.Column(db.Integer, primary_key=True)
    pnr                  = db.Column(db.String(20), unique=True, nullable=False)
    user_id              = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    train_id             = db.Column(db.Integer, nullable=False)
    train_name           = db.Column(db.String(100))
    from_station         = db.Column(db.String(50))
    to_station           = db.Column(db.String(50))
    travel_day           = db.Column(db.String(20))
    seat_number          = db.Column(db.Integer)
    seat_class           = db.Column(db.String(5))
    class_label          = db.Column(db.String(30))
    fare                 = db.Column(db.Integer)
    dep_time             = db.Column(db.String(10))
    arr_time             = db.Column(db.String(10))
    duration             = db.Column(db.String(20))
    passenger_name       = db.Column(db.String(100))
    passenger_phone      = db.Column(db.String(15))
    passenger_dob        = db.Column(db.String(20))
    status               = db.Column(db.String(20), default="confirmed")  # confirmed | cancelled
    razorpay_order_id    = db.Column(db.String(100))
    razorpay_payment_id  = db.Column(db.String(100))
    refund_amount        = db.Column(db.Integer)
    created_at           = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "pnr":        self.pnr,
            "trainName":  self.train_name,
            "trainId":    self.train_id,
            "from":       self.from_station,
            "to":         self.to_station,
            "day":        self.travel_day,
            "dep":        self.dep_time,
            "arr":        self.arr_time,
            "duration":   self.duration,
            "seat":       self.seat_number,
            "seatClass":  self.seat_class,
            "classLabel": self.class_label,
            "fare":       self.fare,
            "passenger": {
                "name":  self.passenger_name,
                "phone": self.passenger_phone,
                "dob":   self.passenger_dob,
            },
            "cancelled":  self.status == "cancelled",
            "refund":     self.refund_amount,
            "bookedDate": self.created_at.strftime("%d/%m/%Y") if self.created_at else "",
            "bookedTime": self.created_at.strftime("%H:%M")    if self.created_at else "",
        }


# Create all tables on startup
with app.app_context():
    db.create_all()


# ══════════════════════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════════════════════
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"success": False, "error": "Not logged in"}), 401
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if "user_id" in session:
        return db.session.get(User, session["user_id"])
    return None


# ══════════════════════════════════════════════════════════
#  SEAT CLASS DEFINITIONS
# ══════════════════════════════════════════════════════════
CLASSES = {
    "SL": {"label": "Sleeper",     "multiplier": 1.0},
    "3A": {"label": "AC 3-Tier",   "multiplier": 2.6},
    "2A": {"label": "AC 2-Tier",   "multiplier": 3.9},
}
PREMIUM_CLASSES = {
    "CC": {"label": "Chair Car",   "multiplier": 1.0},
    "EC": {"label": "Exec. Chair", "multiplier": 1.85},
}
PREMIUM_TRAIN_IDS = {20665, 22631}


# ══════════════════════════════════════════════════════════
#  TRAIN DATA
# ══════════════════════════════════════════════════════════
TRAINS = [
    {
        "id": 12631, "name": "Nellai Superfast",
        "days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 1.25,
        "route": [
            {"station": "Chennai",     "arr": "19:50", "dep": "20:10", "dist": 0},
            {"station": "Trichy",      "arr": "01:10", "dep": "01:15", "dist": 340},
            {"station": "Madurai",     "arr": "03:50", "dep": "03:55", "dist": 495},
            {"station": "Tirunelveli","arr": "06:40", "dep": "07:00", "dist": 650},
        ],
    },
    {
        "id": 22631, "name": "Tejas Express",
        "days": ["Monday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 3.10,
        "route": [
            {"station": "Chennai", "arr": "06:00", "dep": "06:00", "dist": 0},
            {"station": "Trichy",  "arr": "10:05", "dep": "10:10", "dist": 340},
            {"station": "Madurai", "arr": "12:15", "dep": "12:15", "dist": 495},
        ],
    },
    {
        "id": 20665, "name": "Vande Bharat Exp",
        "days": ["Monday","Tuesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 4.50,
        "route": [
            {"station": "Chennai",     "arr": "13:30", "dep": "13:30", "dist": 0},
            {"station": "Trichy",      "arr": "17:30", "dep": "17:35", "dist": 340},
            {"station": "Madurai",     "arr": "19:20", "dep": "19:20", "dist": 495},
            {"station": "Tirunelveli","arr": "21:15", "dep": "21:15", "dist": 650},
        ],
    },
    {
        "id": 12633, "name": "Kanyakumari Exp",
        "days": ["Daily"],
        "base_fare": 1.15,
        "route": [
            {"station": "Chennai",     "arr": "17:15", "dep": "17:15", "dist": 0},
            {"station": "Trichy",      "arr": "22:15", "dep": "22:20", "dist": 340},
            {"station": "Madurai",     "arr": "01:15", "dep": "01:20", "dist": 495},
            {"station": "Tirunelveli","arr": "03:55", "dep": "04:00", "dist": 650},
        ],
    },
    {
        "id": 12605, "name": "Pallavan Express",
        "days": ["Daily"],
        "base_fare": 1.40,
        "route": [
            {"station": "Chennai", "arr": "15:45", "dep": "15:45", "dist": 0},
            {"station": "Trichy",  "arr": "20:50", "dep": "20:50", "dist": 340},
        ],
    },
    {
        "id": 12637, "name": "Pandian Express",
        "days": ["Daily"],
        "base_fare": 1.35,
        "route": [
            {"station": "Chennai", "arr": "21:40", "dep": "21:40", "dist": 0},
            {"station": "Trichy",  "arr": "02:45", "dep": "02:50", "dist": 340},
            {"station": "Madurai", "arr": "05:20", "dep": "05:20", "dist": 495},
        ],
    },
    {
        "id": 16101, "name": "Boat Mail Exp",
        "days": ["Daily"],
        "base_fare": 1.10,
        "route": [
            {"station": "Chennai", "arr": "20:15", "dep": "20:15", "dist": 0},
            {"station": "Trichy",  "arr": "01:55", "dep": "02:00", "dist": 340},
            {"station": "Madurai", "arr": "04:40", "dep": "04:45", "dist": 495},
        ],
    },
    {
        "id": 12635, "name": "Vaigai Express",
        "days": ["Daily"],
        "base_fare": 1.50,
        "route": [
            {"station": "Chennai", "arr": "12:15", "dep": "12:15", "dist": 0},
            {"station": "Trichy",  "arr": "16:30", "dep": "16:35", "dist": 340},
            {"station": "Madurai", "arr": "18:45", "dep": "18:45", "dist": 495},
        ],
    },
    {
        "id": 16127, "name": "Guruvayur Express",
        "days": ["Daily"],
        "base_fare": 1.20,
        "route": [
            {"station": "Chennai",     "arr": "07:45", "dep": "07:45", "dist": 0},
            {"station": "Trichy",      "arr": "13:10", "dep": "13:15", "dist": 340},
            {"station": "Madurai",     "arr": "15:55", "dep": "16:00", "dist": 495},
            {"station": "Tirunelveli","arr": "18:40", "dep": "18:45", "dist": 650},
        ],
    },
    {
        "id": 22671, "name": "Tirunelveli SF Exp",
        "days": ["Tuesday","Wednesday","Friday","Saturday","Sunday"],
        "base_fare": 1.60,
        "route": [
            {"station": "Chennai",     "arr": "23:00", "dep": "23:00", "dist": 0},
            {"station": "Trichy",      "arr": "03:45", "dep": "03:50", "dist": 340},
            {"station": "Madurai",     "arr": "06:20", "dep": "06:25", "dist": 495},
            {"station": "Tirunelveli","arr": "09:05", "dep": "09:05", "dist": 650},
        ],
    },
    {
        "id": 16723, "name": "Ananthapuri Express",
        "days": ["Monday","Wednesday","Saturday"],
        "base_fare": 1.30,
        "route": [
            {"station": "Chennai",     "arr": "10:30", "dep": "10:30", "dist": 0},
            {"station": "Trichy",      "arr": "16:00", "dep": "16:05", "dist": 340},
            {"station": "Madurai",     "arr": "18:50", "dep": "18:55", "dist": 495},
            {"station": "Tirunelveli","arr": "21:30", "dep": "21:30", "dist": 650},
        ],
    },
]


# ══════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html", demo_mode=DEMO_MODE)


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return render_template(
        "dashboard.html",
        user_name=user.name,
        demo_mode=DEMO_MODE,
        razorpay_key=RAZORPAY_KEY_ID
    )


# ══════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════
@app.route("/register", methods=["POST"])
def register():
    data     = request.json or {}
    name     = data.get("name",     "").strip()
    email    = data.get("email",    "").strip().lower()
    phone    = data.get("phone",    "").strip()
    password = data.get("password", "")

    if not all([name, email, phone, password]):
        return jsonify({"success": False, "error": "All fields are required."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "An account with this email already exists."}), 400

    user = User(
        name=name, email=email, phone=phone,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    session["user_id"]   = user.id
    session["user_name"] = user.name
    return jsonify({"success": True})


@app.route("/login", methods=["POST"])
def login():
    data     = request.json or {}
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"success": False, "error": "Incorrect email or password."}), 401

    session["user_id"]   = user.id
    session["user_name"] = user.name
    return jsonify({"success": True})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════
#  SEARCH
# ══════════════════════════════════════════════════════════
@app.route("/search", methods=["POST"])
def search():
    data        = request.json or {}
    u_from      = data.get("from", "")
    u_to        = data.get("to",   "")
    u_day       = data.get("day",  "")
    u_class     = data.get("seat_class", "SL")
    results     = []

    for t in TRAINS:
        if u_day not in t["days"] and "Daily" not in t["days"]:
            continue

        stations = [r["station"] for r in t["route"]]
        if u_from not in stations or u_to not in stations:
            continue

        idx_from = stations.index(u_from)
        idx_to   = stations.index(u_to)
        if idx_from >= idx_to:
            continue

        start = t["route"][idx_from]
        end   = t["route"][idx_to]
        dist  = end["dist"] - start["dist"]

        t1 = datetime.datetime.strptime(start["dep"], "%H:%M")
        t2 = datetime.datetime.strptime(end["arr"],   "%H:%M")
        if t2 < t1:
            t2 += datetime.timedelta(days=1)
        total_min  = int((t2 - t1).total_seconds() // 60)
        h, m       = divmod(total_min, 60)
        duration   = f"{h}h {m:02d}m"

        is_premium = t["id"] in PREMIUM_TRAIN_IDS
        class_map  = PREMIUM_CLASSES if is_premium else CLASSES

        resolved   = u_class if u_class in class_map else next(iter(class_map))
        cls_info   = class_map[resolved]
        final_fare = int(dist * t["base_fare"] * cls_info["multiplier"])

        results.append({
            "id":          t["id"],
            "name":        t["name"],
            "dep":         start["dep"],
            "arr":         end["arr"],
            "duration":    duration,
            "fare":        final_fare,
            "seat_class":  resolved,
            "class_label": cls_info["label"],
            "is_premium":  is_premium,
        })

    return jsonify(results)


# ══════════════════════════════════════════════════════════
#  REAL-TIME SEAT AVAILABILITY
# ══════════════════════════════════════════════════════════
@app.route("/seats/<int:train_id>/<path:travel_day>")
def get_seats(train_id, travel_day):
    """Return seat numbers already booked for this train + day."""
    booked = (
        Booking.query
        .filter_by(train_id=train_id, travel_day=travel_day, status="confirmed")
        .with_entities(Booking.seat_number)
        .all()
    )
    return jsonify({"booked": [b.seat_number for b in booked]})


# ══════════════════════════════════════════════════════════
#  PAYMENT — CREATE ORDER
# ══════════════════════════════════════════════════════════
@app.route("/create-order", methods=["POST"])
@login_required
def create_order():
    fare = int(request.json.get("fare", 0))

    if DEMO_MODE:
        return jsonify({
            "order_id":  "demo_" + str(random.randint(100000, 999999)),
            "amount":    fare * 100,
            "currency":  "INR",
            "key":       "",
            "demo_mode": True,
        })

    try:
        order = rzp.order.create({
            "amount":          fare * 100,
            "currency":        "INR",
            "receipt":         "qr_" + str(int(datetime.datetime.utcnow().timestamp())),
            "payment_capture": 1,
        })
        return jsonify({
            "order_id":  order["id"],
            "amount":    order["amount"],
            "currency":  order["currency"],
            "key":       RAZORPAY_KEY_ID,
            "demo_mode": False,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  PAYMENT — VERIFY & CONFIRM BOOKING
# ══════════════════════════════════════════════════════════
@app.route("/verify-payment", methods=["POST"])
@login_required
def verify_payment():
    data         = request.json or {}
    payment_id   = data.get("razorpay_payment_id",  "")
    order_id     = data.get("razorpay_order_id",    "")
    signature    = data.get("razorpay_signature",   "")
    demo         = data.get("demo_mode", False)
    booking_data = data.get("booking_data", {})

    # ── Verify Razorpay signature (skip in demo mode) ──
    if not demo and not DEMO_MODE:
        msg      = f"{order_id}|{payment_id}"
        expected = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return jsonify({"success": False, "error": "Payment verification failed."}), 400

    # ── Race condition: seat already taken? ─────────────
    conflict = Booking.query.filter_by(
        train_id    = booking_data.get("trainId"),
        travel_day  = booking_data.get("day"),
        seat_number = booking_data.get("seat"),
        status      = "confirmed",
    ).first()
    if conflict:
        return jsonify({
            "success": False,
            "error":   "This seat was just booked by someone else. Please choose another."
        }), 409

    # ── Save booking ─────────────────────────────────────
    pnr     = "QR-" + str(random.randint(100000, 999999))
    booking = Booking(
        pnr                  = pnr,
        user_id              = session["user_id"],
        train_id             = booking_data.get("trainId"),
        train_name           = booking_data.get("trainName"),
        from_station         = booking_data.get("from"),
        to_station           = booking_data.get("to"),
        travel_day           = booking_data.get("day"),
        dep_time             = booking_data.get("dep"),
        arr_time             = booking_data.get("arr"),
        duration             = booking_data.get("duration"),
        seat_number          = booking_data.get("seat"),
        seat_class           = booking_data.get("seatClass"),
        class_label          = booking_data.get("classLabel"),
        fare                 = booking_data.get("fare"),
        passenger_name       = booking_data.get("passenger", {}).get("name"),
        passenger_phone      = booking_data.get("passenger", {}).get("phone"),
        passenger_dob        = booking_data.get("passenger", {}).get("dob"),
        razorpay_order_id    = order_id,
        razorpay_payment_id  = payment_id if not demo else "DEMO_" + pnr,
        status               = "confirmed",
    )
    db.session.add(booking)
    db.session.commit()

    return jsonify({"success": True, "booking": booking.to_dict()})


# ══════════════════════════════════════════════════════════
#  MY BOOKINGS
# ══════════════════════════════════════════════════════════
@app.route("/bookings")
@login_required
def get_bookings():
    bookings = (
        Booking.query
        .filter_by(user_id=session["user_id"])
        .order_by(Booking.created_at.desc())
        .all()
    )
    return jsonify([b.to_dict() for b in bookings])


# ══════════════════════════════════════════════════════════
#  CANCEL BOOKING
# ══════════════════════════════════════════════════════════
@app.route("/cancel-booking", methods=["POST"])
@login_required
def cancel_booking():
    pnr     = (request.json or {}).get("pnr", "")
    booking = Booking.query.filter_by(pnr=pnr, user_id=session["user_id"]).first()

    if not booking:
        return jsonify({"success": False, "error": "Booking not found."}), 404
    if booking.status == "cancelled":
        return jsonify({"success": False, "error": "This booking is already cancelled."}), 400

    refund                = int(booking.fare * 0.9)
    booking.status        = "cancelled"
    booking.refund_amount = refund

    # Real Razorpay refund (only if live payment was made)
    if (not DEMO_MODE and rzp
            and booking.razorpay_payment_id
            and not booking.razorpay_payment_id.startswith("DEMO_")):
        try:
            rzp.payment.refund(booking.razorpay_payment_id, {"amount": refund * 100})
        except Exception:
            pass  # Don't block cancellation if refund API call fails

    db.session.commit()
    return jsonify({"success": True, "refund": refund})


# ══════════════════════════════════════════════════════════
#  CHAT
# ══════════════════════════════════════════════════════════
@app.route("/chat", methods=["POST"])
def chat():
    msg = (request.json or {}).get("message", "").lower()

    responses = {
        ("hi", "hello", "hey"):
            "Hi! I'm your QuickRail assistant. Ask me about trains, fares, stations, or bookings.",
        ("fare", "price", "cost", "ticket", "class", "sleeper", "ac"):
            "We offer Sleeper (SL), AC 3-Tier (3A), and AC 2-Tier (2A). "
            "Vande Bharat and Tejas have Chair Car (CC) and Executive Chair (EC). "
            "Select your class in the search panel to see the exact fare.",
        ("pnr", "status", "booking", "journey"):
            "All your bookings are saved under 'My Journeys' in the sidebar. "
            "You can view the e-ticket or cancel there.",
        ("cancel", "refund"):
            "You can cancel any booking from 'My Journeys'. "
            "A 90% refund is processed within 24 hours.",
        ("station", "stop", "where"):
            "We cover Chennai, Trichy, Madurai, and Tirunelveli — "
            "the 650 km southern Tamil Nadu corridor.",
        ("train", "schedule", "route", "when", "time"):
            "We have 11 trains on this corridor with departures spread across the day. "
            "Use the search panel to filter by route and day.",
        ("payment", "pay", "razorpay", "upi", "card"):
            "We use Razorpay for secure payments — UPI, debit/credit cards, "
            "and netbanking are all supported.",
        ("vande", "bharat", "tejas", "premium"):
            "Vande Bharat and Tejas are premium services with Chair Car and Executive Chair classes. "
            "They're faster but don't have sleeper berths.",
        ("register", "sign up", "account", "create"):
            "Click 'Create account' on the sign-in page. "
            "You need an account to book — searching is free without logging in.",
        ("jenin", "developer", "who built", "creator"):
            "QuickRail was built by Jenin — a project for the Chennai–Tirunelveli corridor.",
        ("thanks", "thank", "okay", "ok", "great"):
            "Happy to help. Have a good journey!",
    }

    for keys, reply in responses.items():
        if any(k in msg for k in keys):
            return jsonify({"reply": reply})

    return jsonify({
        "reply": "I didn't quite catch that. "
                 "Try asking about fares, seat classes, stations, payments, or your bookings."
    })


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000)