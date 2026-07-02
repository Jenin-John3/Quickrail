import os
import re
import time
import random
import datetime
from functools import wraps

from flask import (Flask, request, jsonify, render_template,
                   session, redirect, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

# ── App & config ──────────────────────────────────────────
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static")
)

_db_url = os.environ.get("DATABASE_URL", "")

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    if _db_url:
        raise RuntimeError("SECRET_KEY environment variable must be set in production.")
    app.config["SECRET_KEY"] = "dev-only-secret-change-me"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session cookies need SameSite=Lax + Secure in production (HTTPS on Vercel)
# so the browser actually keeps sending them back on subsequent fetch() calls.
# Without this, some browsers silently drop the cookie cross-request on
# serverless deployments, which looks exactly like "randomly logged out".
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = bool(os.environ.get("DATABASE_URL"))
app.config["SESSION_COOKIE_HTTPONLY"] = True

if not _db_url:
    _db_url = "sqlite:///" + os.path.join(BASE, "quickrail.db")
elif _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
db = SQLAlchemy(app)


# ── Models ────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    phone      = db.Column(db.String(15), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bookings   = db.relationship("Booking", backref="user", lazy=True)


class SegmentBooking(db.Model):
    """
    One row per seat-segment allocation.

    A seat is identified by (train_id, travel_day, seat_number, seat_class).
    Each row records which index range [start_idx, end_idx) that seat is
    occupied for. Two bookings on the same seat overlap when their index
    ranges intersect — checked via interval overlap logic before inserting.

    Linked to a Booking via pnr. A single user Booking may produce multiple
    SegmentBooking rows when the journey had to be split across seats.
    """
    __tablename__ = "segment_bookings"
    id          = db.Column(db.Integer, primary_key=True)
    pnr         = db.Column(db.String(20), nullable=False)          # parent booking
    train_id    = db.Column(db.Integer, nullable=False)
    travel_day  = db.Column(db.String(20), nullable=False)
    seat_class  = db.Column(db.String(5), nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    start_idx   = db.Column(db.Integer, nullable=False)             # inclusive
    end_idx     = db.Column(db.Integer, nullable=False)             # exclusive


class Booking(db.Model):
    __tablename__  = "bookings"
    id             = db.Column(db.Integer, primary_key=True)
    pnr            = db.Column(db.String(20), unique=True, nullable=False)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    train_id       = db.Column(db.Integer, nullable=False)
    train_name     = db.Column(db.String(100))
    from_station   = db.Column(db.String(50))
    to_station     = db.Column(db.String(50))
    travel_day     = db.Column(db.String(20))
    seat_class     = db.Column(db.String(5))
    class_label    = db.Column(db.String(30))
    fare           = db.Column(db.Integer)
    dep_time       = db.Column(db.String(10))
    arr_time       = db.Column(db.String(10))
    duration       = db.Column(db.String(20))
    passenger_name = db.Column(db.String(100))
    passenger_phone= db.Column(db.String(15))
    passenger_dob  = db.Column(db.String(20))
    # seat_assignments: JSON-ish string — e.g. "4" or "4(Chennai→Madurai),9(Madurai→Coimbatore)"
    seat_assignments = db.Column(db.String(300))
    is_split       = db.Column(db.Boolean, default=False)
    status         = db.Column(db.String(20), default="confirmed")
    waitlist_until = db.Column(db.DateTime, nullable=True)          # set when waitlisted
    refund_amount  = db.Column(db.Integer)
    created_at     = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "pnr":            self.pnr,
            "trainName":      self.train_name,
            "trainId":        self.train_id,
            "from":           self.from_station,
            "to":             self.to_station,
            "day":            self.travel_day,
            "dep":            self.dep_time,
            "arr":            self.arr_time,
            "duration":       self.duration,
            "seatClass":      self.seat_class,
            "classLabel":     self.class_label,
            "fare":           self.fare,
            "seatAssignments":self.seat_assignments,
            "isSplit":        self.is_split,
            "passenger": {
                "name":  self.passenger_name,
                "phone": self.passenger_phone,
                "dob":   self.passenger_dob,
            },
            "status":     self.status,
            "refund":     self.refund_amount,
            "bookedDate": self.created_at.strftime("%d/%m/%Y") if self.created_at else "",
            "bookedTime": self.created_at.strftime("%H:%M")    if self.created_at else "",
        }


class WaitlistEntry(db.Model):
    """Passengers queued when no seat combination could be found."""
    __tablename__ = "waitlist"
    id          = db.Column(db.Integer, primary_key=True)
    pnr         = db.Column(db.String(20), unique=True, nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    train_id    = db.Column(db.Integer, nullable=False)
    travel_day  = db.Column(db.String(20), nullable=False)
    seat_class  = db.Column(db.String(5), nullable=False)
    start_idx   = db.Column(db.Integer, nullable=False)
    end_idx     = db.Column(db.Integer, nullable=False)
    queued_at   = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at  = db.Column(db.DateTime, nullable=False)            # queued_at + 1 hour


def _run_light_migrations():
    """
    db.create_all() only creates tables that don't exist yet -- it never
    alters a table that's already there. If this database still has tables
    from an earlier version of QuickRail (different columns -- e.g. the old
    email/password/Razorpay schema), two separate problems show up:

    1. Missing columns -- inserts against the current models fail with
       "column does not exist" because new columns (seat_assignments,
       is_split, waitlist_until, etc.) simply aren't in the live table.

    2. Leftover legacy columns -- e.g. an old `email` or `password_hash`
       column that was NOT NULL under the old schema. The current code
       never populates those columns, so every insert fails with a
       "NOT NULL constraint" violation on a column the app doesn't even
       know about anymore.

    This function fixes both: it adds any column the current models expect
    but the live table is missing, and it relaxes NOT NULL on any column
    that exists in the live table but is NOT part of the current model
    (i.e. a leftover the app will never populate). Existing rows and data
    are never touched or dropped. Safe to run on every startup -- it's a
    no-op once the schema is caught up.
    """
    from sqlalchemy import inspect, text

    inspector       = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for model in (User, SegmentBooking, Booking, WaitlistEntry):
        table_name = model.__tablename__
        if table_name not in existing_tables:
            continue  # brand-new table -- db.create_all() already built it correctly

        model_cols  = {col.name for col in model.__table__.columns}
        db_columns  = inspector.get_columns(table_name)
        existing_cols = {c["name"] for c in db_columns}

        # 1) Add any column the model expects that the live table is missing.
        for col in model.__table__.columns:
            if col.name in existing_cols:
                continue
            try:
                ddl_type = col.type.compile(dialect=db.engine.dialect)
                db.session.execute(text(
                    f'ALTER TABLE {table_name} ADD COLUMN {col.name} {ddl_type}'
                ))
                db.session.commit()
                print(f"[migration] Added missing column {table_name}.{col.name}")
            except Exception as e:
                db.session.rollback()
                print(f"[migration] Could not add {table_name}.{col.name}: {e}")

        # 2) Relax NOT NULL on any leftover column the current model doesn't
        #    have -- the app will never provide a value for it on insert.
        for c in db_columns:
            if c["name"] in model_cols:
                continue
            if c.get("nullable", True):
                continue  # already nullable, nothing to do
            try:
                db.session.execute(text(
                    f'ALTER TABLE {table_name} ALTER COLUMN {c["name"]} DROP NOT NULL'
                ))
                db.session.commit()
                print(f"[migration] Relaxed NOT NULL on legacy column {table_name}.{c['name']}")
            except Exception as e:
                db.session.rollback()
                print(f"[migration] Could not relax NOT NULL on {table_name}.{c['name']}: {e}")


with app.app_context():
    db.create_all()
    _run_light_migrations()


# Any route NOT in this set is treated as an API endpoint for error-handling
# purposes: unhandled exceptions there return JSON instead of Flask's default
# HTML error page, so fetch().json() in the frontend never breaks silently.
_PAGE_ROUTES = {"/", "/dashboard"}


@app.errorhandler(Exception)
def handle_uncaught(e):
    # Werkzeug/Flask's own routine HTTP errors (404 for an undefined route
    # like /favicon.ico, 400 for a bad request, 401, etc.) are HTTPException
    # subclasses -- and therefore also plain Exception subclasses. Catching
    # them here and rewriting them as a generic 500 is wrong: it was turning
    # an ordinary "route not found" into a fake "something went wrong" and
    # masking the real status code. Let Flask handle those exactly as it
    # normally would; only genuinely unhandled crashes fall through below.
    if isinstance(e, HTTPException):
        return e

    db.session.rollback()
    if request.path not in _PAGE_ROUTES:
        import traceback
        traceback.print_exc()
        # Surfacing the real exception type + message directly in the
        # response (not just Vercel's log viewer) so failures are
        # immediately diagnosable without a trip through the dashboard.
        # Fine for a demo project; tighten this before any real deployment.
        return jsonify({"success": False,
                        "error": f"[debug] {type(e).__name__}: {e}"}), 500
    raise e


# ── Auth helpers ──────────────────────────────────────────
def page_login_required(f):
    """
    For HTML page routes only (e.g. /dashboard). Not logged in -> redirect
    to the landing page so the browser shows a real page, not JSON.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def login_required(f):
    """
    For API routes called via fetch() from script.js/chatbot.js.
    Always returns JSON on auth failure -- never a redirect. A redirect here
    would return the HTML landing page to fetch(), which fetch() follows
    silently, and res.json() then throws -- surfacing as a generic
    "could not connect" error in the UI even though the real problem is
    just an expired/missing session.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "Session expired. Please sign in again."}), 401
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "user_id" in session:
        return db.session.get(User, session["user_id"])
    return None


# ── Simple in-memory rate limiter ────────────────────────
_rate_hits = {}

def rate_limit(max_requests=5, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip  = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
            key = (ip, request.endpoint)
            now = time.time()
            hits = [t for t in _rate_hits.get(key, []) if now - t < window_seconds]
            if len(hits) >= max_requests:
                return jsonify({"success": False, "error": "Too many attempts. Please wait a minute."}), 429
            hits.append(now)
            _rate_hits[key] = hits
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ── In-memory OTP store  {phone: (otp_str, expires_ts)} ─
_otp_store: dict[str, tuple[str, float]] = {}


# ── Seat class definitions ────────────────────────────────
CLASSES = {
    "SL": {"label": "Sleeper",     "multiplier": 1.0,  "total_seats": 72},
    "3A": {"label": "AC 3-Tier",   "multiplier": 2.6,  "total_seats": 64},
    "2A": {"label": "AC 2-Tier",   "multiplier": 3.9,  "total_seats": 48},
}
PREMIUM_CLASSES = {
    "CC": {"label": "Chair Car",   "multiplier": 1.0,  "total_seats": 78},
    "EC": {"label": "Exec. Chair", "multiplier": 1.85, "total_seats": 56},
}
PREMIUM_TRAIN_IDS = {20665, 22631}


# ── Train data  (Coimbatore added between Madurai & Tirunelveli) ──
TRAINS = [
    {
        "id": 12631, "name": "Nellai Superfast",
        "days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 1.25,
        "route": [
            {"station": "Chennai",      "arr": "19:50", "dep": "20:10", "dist": 0},
            {"station": "Trichy",       "arr": "01:10", "dep": "01:15", "dist": 340},
            {"station": "Madurai",      "arr": "03:50", "dep": "03:55", "dist": 495},
            {"station": "Coimbatore",   "arr": "06:05", "dep": "06:10", "dist": 590},
            {"station": "Tirunelveli",  "arr": "08:40", "dep": "09:00", "dist": 650},
        ],
    },
    {
        "id": 22631, "name": "Tejas Express",
        "days": ["Monday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 3.10,
        "route": [
            {"station": "Chennai",    "arr": "06:00", "dep": "06:00", "dist": 0},
            {"station": "Trichy",     "arr": "10:05", "dep": "10:10", "dist": 340},
            {"station": "Madurai",    "arr": "12:15", "dep": "12:20", "dist": 495},
            {"station": "Coimbatore", "arr": "14:10", "dep": "14:10", "dist": 590},
        ],
    },
    {
        "id": 20665, "name": "Vande Bharat Exp",
        "days": ["Monday","Tuesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 4.50,
        "route": [
            {"station": "Chennai",     "arr": "13:30", "dep": "13:30", "dist": 0},
            {"station": "Trichy",      "arr": "17:30", "dep": "17:35", "dist": 340},
            {"station": "Madurai",     "arr": "19:20", "dep": "19:25", "dist": 495},
            {"station": "Coimbatore",  "arr": "21:10", "dep": "21:10", "dist": 590},
            {"station": "Tirunelveli", "arr": "23:15", "dep": "23:15", "dist": 650},
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
            {"station": "Coimbatore",  "arr": "03:10", "dep": "03:15", "dist": 590},
            {"station": "Tirunelveli", "arr": "05:55", "dep": "06:00", "dist": 650},
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
            {"station": "Chennai",    "arr": "21:40", "dep": "21:40", "dist": 0},
            {"station": "Trichy",     "arr": "02:45", "dep": "02:50", "dist": 340},
            {"station": "Madurai",    "arr": "05:20", "dep": "05:25", "dist": 495},
            {"station": "Coimbatore", "arr": "07:15", "dep": "07:15", "dist": 590},
        ],
    },
    {
        "id": 16101, "name": "Boat Mail Exp",
        "days": ["Daily"],
        "base_fare": 1.10,
        "route": [
            {"station": "Chennai",    "arr": "20:15", "dep": "20:15", "dist": 0},
            {"station": "Trichy",     "arr": "01:55", "dep": "02:00", "dist": 340},
            {"station": "Madurai",    "arr": "04:40", "dep": "04:45", "dist": 495},
            {"station": "Coimbatore", "arr": "06:35", "dep": "06:40", "dist": 590},
        ],
    },
    {
        "id": 12635, "name": "Vaigai Express",
        "days": ["Daily"],
        "base_fare": 1.50,
        "route": [
            {"station": "Chennai",    "arr": "12:15", "dep": "12:15", "dist": 0},
            {"station": "Trichy",     "arr": "16:30", "dep": "16:35", "dist": 340},
            {"station": "Madurai",    "arr": "18:45", "dep": "18:50", "dist": 495},
            {"station": "Coimbatore", "arr": "20:40", "dep": "20:40", "dist": 590},
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
            {"station": "Coimbatore",  "arr": "17:50", "dep": "17:55", "dist": 590},
            {"station": "Tirunelveli", "arr": "20:40", "dep": "20:45", "dist": 650},
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
            {"station": "Coimbatore",  "arr": "08:15", "dep": "08:20", "dist": 590},
            {"station": "Tirunelveli", "arr": "11:05", "dep": "11:05", "dist": 650},
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
            {"station": "Coimbatore",  "arr": "20:45", "dep": "20:50", "dist": 590},
            {"station": "Tirunelveli", "arr": "23:30", "dep": "23:30", "dist": 650},
        ],
    },
]

# Quick lookup by train id
TRAIN_BY_ID = {t["id"]: t for t in TRAINS}

ALL_STATIONS = ["Chennai", "Trichy", "Madurai", "Coimbatore", "Tirunelveli"]


# ── Segment-based seat allocation ─────────────────────────

def _get_booked_segments(train_id, travel_day, seat_class):
    """
    Returns a dict: seat_number -> list of (start_idx, end_idx) ranges
    that are already occupied for this train/day/class.
    """
    rows = SegmentBooking.query.filter_by(
        train_id=train_id,
        travel_day=travel_day,
        seat_class=seat_class,
    ).all()
    occupied: dict[int, list[tuple[int,int]]] = {}
    for r in rows:
        occupied.setdefault(r.seat_number, []).append((r.start_idx, r.end_idx))
    return occupied


def _overlaps(existing: list[tuple[int,int]], start: int, end: int) -> bool:
    """True if [start, end) overlaps any interval in the existing list."""
    for (s, e) in existing:
        if start < e and end > s:
            return True
    return False


def find_seats_for_range(train_id, travel_day, seat_class, start_idx, end_idx):
    """
    Try to allocate seats for the requested index range [start_idx, end_idx).

    Strategy:
    1. Look for a single seat free for the entire range → return [(seat, start_idx, end_idx)]
    2. If none, try to cover the range with 2 seats via a split at each intermediate
       station index → return [(seat_a, start_idx, mid), (seat_b, mid, end_idx)]
    3. If still no combination works → return None (caller puts on waitlist)

    Returns: list of (seat_number, seg_start, seg_end) tuples, or None.
    """
    class_info  = (PREMIUM_CLASSES if train_id in PREMIUM_TRAIN_IDS else CLASSES).get(seat_class)
    if not class_info:
        return None
    total_seats = class_info["total_seats"]

    occupied = _get_booked_segments(train_id, travel_day, seat_class)

    # Pass 1 — single seat covering the whole range
    for seat in range(1, total_seats + 1):
        segs = occupied.get(seat, [])
        if not _overlaps(segs, start_idx, end_idx):
            return [(seat, start_idx, end_idx)]

    # Pass 2 — try splitting at each intermediate station index
    for mid in range(start_idx + 1, end_idx):
        seat_a = None
        seat_b = None
        for seat in range(1, total_seats + 1):
            segs = occupied.get(seat, [])
            if seat_a is None and not _overlaps(segs, start_idx, mid):
                seat_a = seat
            if seat_b is None and not _overlaps(segs, mid, end_idx):
                seat_b = seat
            if seat_a and seat_b:
                break
        if seat_a and seat_b:
            return [(seat_a, start_idx, mid), (seat_b, mid, end_idx)]

    return None  # waitlist


def _seat_status_for_range(train_id, travel_day, seat_class, start_idx, end_idx):
    """
    For the seat map: returns per-seat status from the passenger's perspective.
      'available'      — free for requested range
      'partial'        — booked for other segments but free for yours
      'taken'          — conflicts with your requested range
    """
    class_info  = (PREMIUM_CLASSES if train_id in PREMIUM_TRAIN_IDS else CLASSES).get(seat_class)
    if not class_info:
        return {}
    total_seats = class_info["total_seats"]

    occupied = _get_booked_segments(train_id, travel_day, seat_class)
    result   = {}
    for seat in range(1, total_seats + 1):
        segs = occupied.get(seat, [])
        if not segs:
            result[seat] = {"status": "available", "bookedSegments": []}
        elif _overlaps(segs, start_idx, end_idx):
            result[seat] = {"status": "taken",     "bookedSegments": list(segs)}
        else:
            result[seat] = {"status": "partial",   "bookedSegments": list(segs)}
    return result


def _station_label(train, idx):
    """Short 'From→To' label for a segment split."""
    route = train["route"]
    return f"{route[idx]['station']}→{route[idx+1]['station'] if idx+1 < len(route) else '?'}"


# ── Page routes ───────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@page_login_required
def dashboard():
    user = current_user()
    return render_template("dashboard.html", user_name=user.name)


# ── Auth — OTP-based mobile login ────────────────────────

@app.route("/send-otp", methods=["POST"])
@rate_limit(5, 60)
def send_otp():
    phone = (request.get_json(silent=True) or {}).get("phone", "").strip()
    if not re.fullmatch(r"\d{10}", phone):
        return jsonify({"success": False, "error": "Enter a valid 10-digit mobile number."}), 400

    otp = str(random.randint(100000, 999999))
    _otp_store[phone] = (otp, time.time() + 300)   # 5-minute expiry
    # In a real system: send via SMS gateway. Here we return it to the client.
    return jsonify({"success": True, "otp": otp,
                    "note": "Simulated OTP — not sent via SMS."})


@app.route("/verify-otp", methods=["POST"])
@rate_limit(10, 60)
def verify_otp():
    data  = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()
    otp   = data.get("otp",   "").strip()
    name  = data.get("name",  "").strip()   # required only for new users

    stored = _otp_store.get(phone)
    if not stored:
        return jsonify({"success": False, "error": "No OTP sent to this number."}), 400
    stored_otp, expires = stored
    if time.time() > expires:
        del _otp_store[phone]
        return jsonify({"success": False, "error": "OTP expired. Please request a new one."}), 400
    if otp != stored_otp:
        return jsonify({"success": False, "error": "Incorrect OTP."}), 400

    # OTP is valid. Do NOT consume it yet -- a brand-new phone number needs a
    # second round-trip (this same endpoint, called again with `name` filled
    # in) before the flow is actually complete. Deleting it here would
    # invalidate that second call and break every new-user signup with
    # "No OTP sent to this number."
    user = User.query.filter_by(phone=phone).first()
    if not user:
        if not name:
            # New user -- ask the frontend to collect the name. OTP stays
            # valid in the store until this call comes back with a name.
            return jsonify({"success": False, "needsName": True,
                            "message": "New user — please provide your name."})
        user = User(name=name, phone=phone)
        db.session.add(user)
        db.session.commit()

    # Flow is complete (existing user logged in, or new user just created) --
    # the OTP has done its job and can now be safely consumed.
    del _otp_store[phone]

    session["user_id"]   = user.id
    session["user_name"] = user.name
    return jsonify({"success": True, "name": user.name})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# ── Search ────────────────────────────────────────────────

@app.route("/search", methods=["POST"])
def search():
    data    = request.get_json(silent=True) or {}
    u_from  = data.get("from", "")
    u_to    = data.get("to",   "")
    u_day   = data.get("day",  "")
    u_class = data.get("seat_class", "SL")
    results = []

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
        total_min = int((t2 - t1).total_seconds() // 60)
        h, m = divmod(total_min, 60)
        duration = f"{h}h {m:02d}m"

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
            "idx_from":    idx_from,
            "idx_to":      idx_to,
        })

    return jsonify(results)


# ── Seat map ─────────────────────────────────────────────

@app.route("/seats/<int:train_id>/<path:travel_day>")
def get_seats(train_id, travel_day):
    data      = request.args
    seat_class = data.get("class", "SL")
    idx_from   = int(data.get("idx_from", 0))
    idx_to     = int(data.get("idx_to",   1))

    statuses  = _seat_status_for_range(train_id, travel_day, seat_class, idx_from, idx_to)
    train     = TRAIN_BY_ID.get(train_id)
    is_premium = train_id in PREMIUM_TRAIN_IDS
    class_map  = PREMIUM_CLASSES if is_premium else CLASSES
    cls_info   = class_map.get(seat_class, list(class_map.values())[0])

    # Build station labels for tooltip context
    route_labels = [s["station"] for s in train["route"]] if train else []

    return jsonify({
        "statuses":    statuses,
        "totalSeats":  cls_info["total_seats"],
        "routeLabels": route_labels,
    })


# ── Confirm booking (no payment step) ────────────────────

@app.route("/confirm-booking", methods=["POST"])
@login_required
def confirm_booking():
    data = request.get_json(silent=True) or {}
    booking_data = data.get("booking_data", {})

    train_id   = booking_data.get("trainId")
    travel_day = booking_data.get("day")
    seat_class = booking_data.get("seatClass")
    idx_from   = booking_data.get("idxFrom")
    idx_to     = booking_data.get("idxTo")

    if None in (train_id, travel_day, seat_class, idx_from, idx_to):
        return jsonify({"success": False, "error": "Incomplete booking data."}), 400

    train = TRAIN_BY_ID.get(train_id)
    if not train:
        return jsonify({"success": False, "error": "Train not found."}), 404

    pnr = "QR-" + str(random.randint(100000, 999999))

    # Try to allocate seats using segment logic
    allocation = find_seats_for_range(train_id, travel_day, seat_class, idx_from, idx_to)

    if allocation is None:
        # Waitlist — queue for 1 hour
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        booking = Booking(
            pnr            = pnr,
            user_id        = session["user_id"],
            train_id       = train_id,
            train_name     = booking_data.get("trainName"),
            from_station   = booking_data.get("from"),
            to_station     = booking_data.get("to"),
            travel_day     = travel_day,
            dep_time       = booking_data.get("dep"),
            arr_time       = booking_data.get("arr"),
            duration       = booking_data.get("duration"),
            seat_class     = seat_class,
            class_label    = booking_data.get("classLabel"),
            fare           = booking_data.get("fare"),
            passenger_name = booking_data.get("passenger", {}).get("name"),
            passenger_phone= booking_data.get("passenger", {}).get("phone"),
            passenger_dob  = booking_data.get("passenger", {}).get("dob"),
            seat_assignments = "Waitlisted",
            is_split       = False,
            status         = "waitlisted",
            waitlist_until = expires,
        )
        db.session.add(booking)
        db.session.commit()

        entry = WaitlistEntry(
            pnr        = pnr,
            user_id    = session["user_id"],
            train_id   = train_id,
            travel_day = travel_day,
            seat_class = seat_class,
            start_idx  = idx_from,
            end_idx    = idx_to,
            expires_at = expires,
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify({
            "success":    True,
            "waitlisted": True,
            "pnr":        pnr,
            "waitUntil":  expires.strftime("%H:%M"),
            "message":    "No seats available right now. You've been added to the waitlist. "
                          "If a seat frees up within 1 hour, it will be auto-assigned to you.",
        })

    # Build seat assignment string and persist SegmentBookings
    route   = train["route"]
    is_split = len(allocation) > 1
    parts   = []
    for (seat_num, seg_s, seg_e) in allocation:
        seg_booking = SegmentBooking(
            pnr         = pnr,
            train_id    = train_id,
            travel_day  = travel_day,
            seat_class  = seat_class,
            seat_number = seat_num,
            start_idx   = seg_s,
            end_idx     = seg_e,
        )
        db.session.add(seg_booking)
        if is_split:
            seg_label = f"{route[seg_s]['station']}→{route[seg_e]['station']}"
            parts.append(f"Seat {seat_num} ({seg_label})")
        else:
            parts.append(str(seat_num))

    seat_assignment_str = ", ".join(parts)

    booking = Booking(
        pnr            = pnr,
        user_id        = session["user_id"],
        train_id       = train_id,
        train_name     = booking_data.get("trainName"),
        from_station   = booking_data.get("from"),
        to_station     = booking_data.get("to"),
        travel_day     = travel_day,
        dep_time       = booking_data.get("dep"),
        arr_time       = booking_data.get("arr"),
        duration       = booking_data.get("duration"),
        seat_class     = seat_class,
        class_label    = booking_data.get("classLabel"),
        fare           = booking_data.get("fare"),
        passenger_name = booking_data.get("passenger", {}).get("name"),
        passenger_phone= booking_data.get("passenger", {}).get("phone"),
        passenger_dob  = booking_data.get("passenger", {}).get("dob"),
        seat_assignments = seat_assignment_str,
        is_split       = is_split,
        status         = "confirmed",
    )
    db.session.add(booking)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False,
                        "error": "Seat just taken by someone else. Please retry."}), 409

    return jsonify({
        "success":   True,
        "waitlisted": False,
        "booking":   booking.to_dict(),
        "isSplit":   is_split,
        "splitNote": (
            "Your journey requires a seat change mid-way. "
            "Details are shown on your e-ticket."
        ) if is_split else None,
    })


# ── My bookings ───────────────────────────────────────────

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


# ── Cancel booking ────────────────────────────────────────

@app.route("/cancel-booking", methods=["POST"])
@login_required
def cancel_booking():
    pnr     = (request.get_json(silent=True) or {}).get("pnr", "")
    booking = Booking.query.filter_by(pnr=pnr, user_id=session["user_id"]).first()

    if not booking:
        return jsonify({"success": False, "error": "Booking not found."}), 404
    if booking.status == "cancelled":
        return jsonify({"success": False, "error": "Already cancelled."}), 400

    refund                = int((booking.fare or 0) * 0.9)
    booking.status        = "cancelled"
    booking.refund_amount = refund

    # Free segment seats
    SegmentBooking.query.filter_by(pnr=pnr).delete()

    # Remove from waitlist if applicable
    WaitlistEntry.query.filter_by(pnr=pnr).delete()

    db.session.commit()

    # Try to auto-assign waiting passengers whose range can now be satisfied
    _process_waitlist(booking.train_id, booking.travel_day, booking.seat_class)

    return jsonify({"success": True, "refund": refund})


def _process_waitlist(train_id, travel_day, seat_class):
    """
    Called after a cancellation. Tries to allocate seats for any active
    waitlist entries on the same train/day/class, oldest first.
    Expired entries are cleaned up.
    """
    now     = datetime.datetime.utcnow()
    entries = (
        WaitlistEntry.query
        .filter_by(train_id=train_id, travel_day=travel_day, seat_class=seat_class)
        .filter(WaitlistEntry.expires_at > now)
        .order_by(WaitlistEntry.queued_at)
        .all()
    )

    # Clean up expired entries
    (WaitlistEntry.query
        .filter_by(train_id=train_id, travel_day=travel_day, seat_class=seat_class)
        .filter(WaitlistEntry.expires_at <= now)
        .delete())
    db.session.commit()

    for entry in entries:
        allocation = find_seats_for_range(
            entry.train_id, entry.travel_day, entry.seat_class,
            entry.start_idx, entry.end_idx
        )
        if allocation is None:
            continue

        booking = Booking.query.filter_by(pnr=entry.pnr).first()
        if not booking:
            db.session.delete(entry)
            continue

        train    = TRAIN_BY_ID.get(train_id)
        route    = train["route"] if train else []
        is_split = len(allocation) > 1
        parts    = []
        for (seat_num, seg_s, seg_e) in allocation:
            sb = SegmentBooking(
                pnr=entry.pnr, train_id=train_id, travel_day=travel_day,
                seat_class=seat_class, seat_number=seat_num,
                start_idx=seg_s, end_idx=seg_e,
            )
            db.session.add(sb)
            if is_split and route:
                label = f"{route[seg_s]['station']}→{route[seg_e]['station']}"
                parts.append(f"Seat {seat_num} ({label})")
            else:
                parts.append(str(seat_num))

        booking.seat_assignments = ", ".join(parts)
        booking.is_split         = is_split
        booking.status           = "confirmed"
        booking.waitlist_until   = None

        db.session.delete(entry)
        db.session.commit()


# ── Fake live train tracking ──────────────────────────────

def _fake_live_status(train_id):
    """
    Time-based interpolation: given now(), figure out which segment
    the train is currently in and estimate position / ETA.
    Returns a dict with status string + ETA info.
    """
    train = TRAIN_BY_ID.get(train_id)
    if not train:
        return {"error": "Train not found"}

    route = train["route"]
    now   = datetime.datetime.now()
    today = now.strftime("%H:%M")

    # Convert all station dep/arr times to today's datetime for comparison.
    # Trains that cross midnight get +1 day applied progressively.
    def to_dt(t_str, base_date, carry_day):
        dt = datetime.datetime.combine(base_date, datetime.time(*map(int, t_str.split(":"))))
        if carry_day:
            dt += datetime.timedelta(days=1)
        return dt

    base = now.date()
    times = []
    carry = False
    prev_dep = None
    for stop in route:
        arr_dt = to_dt(stop["arr"], base, carry)
        if prev_dep and arr_dt < prev_dep:
            carry = True
            arr_dt += datetime.timedelta(days=1)
        dep_dt = to_dt(stop["dep"], base, carry)
        if dep_dt < arr_dt:
            dep_dt += datetime.timedelta(days=1)
        times.append({"station": stop["station"], "arr": arr_dt, "dep": dep_dt})
        prev_dep = dep_dt

    first_dep = times[0]["dep"]
    last_arr  = times[-1]["arr"]

    if now < first_dep:
        mins_to_dep = int((first_dep - now).total_seconds() // 60)
        return {
            "status":  "not_departed",
            "message": f"Departs {route[0]['station']} in {mins_to_dep} min "
                       f"(at {route[0]['dep']})",
        }
    if now > last_arr:
        return {
            "status":  "arrived",
            "message": f"Arrived at {route[-1]['station']}",
        }

    # Find which segment the train is currently in
    for i in range(len(times) - 1):
        dep_cur = times[i]["dep"]
        arr_nxt = times[i + 1]["arr"]
        if dep_cur <= now <= arr_nxt:
            elapsed   = (now - dep_cur).total_seconds()
            total_seg = (arr_nxt - dep_cur).total_seconds()
            pct       = elapsed / total_seg if total_seg else 0
            mins_eta  = int((arr_nxt - now).total_seconds() // 60)
            from_s    = route[i]["station"]
            to_s      = route[i + 1]["station"]
            return {
                "status":   "in_transit",
                "from":     from_s,
                "to":       to_s,
                "progress": round(pct * 100),
                "etaMins":  mins_eta,
                "message":  f"Between {from_s} and {to_s} — "
                            f"ETA {to_s}: {mins_eta} min",
            }
        # Train is at a station (between arr and dep)
        if times[i]["arr"] <= now <= times[i]["dep"]:
            return {
                "status":  "at_station",
                "station": route[i]["station"],
                "message": f"At {route[i]['station']} — departs soon",
            }

    return {"status": "unknown", "message": "Status unavailable"}


@app.route("/live/<int:train_id>")
def live_status(train_id):
    return jsonify(_fake_live_status(train_id))


# ── Chat assistant — state-machine booking + info ─────────

# Session key for chat state
_CHAT_KEY = "chat_state"

STATION_ALIASES = {
    "chennai": "Chennai", "madras": "Chennai",
    "trichy": "Trichy", "tiruchirappalli": "Trichy",
    "madurai": "Madurai",
    "coimbatore": "Coimbatore", "kovai": "Coimbatore",
    "tirunelveli": "Tirunelveli", "nellai": "Tirunelveli",
}

CLASS_ALIASES = {
    "sleeper": "SL", "sl": "SL",
    "ac 3": "3A", "3a": "3A", "3 tier": "3A",
    "ac 2": "2A", "2a": "2A", "2 tier": "2A",
    "chair": "CC", "cc": "CC", "chair car": "CC",
    "executive": "EC", "ec": "EC", "exec": "EC",
}

DAY_ALIASES = {
    "mon": "Monday", "monday": "Monday",
    "tue": "Tuesday", "tuesday": "Tuesday",
    "wed": "Wednesday", "wednesday": "Wednesday",
    "thu": "Thursday", "thursday": "Thursday",
    "fri": "Friday", "friday": "Friday",
    "sat": "Saturday", "saturday": "Saturday",
    "sun": "Sunday", "sunday": "Sunday",
    "today": None,   # resolved at runtime
    "tomorrow": None,
}


def _resolve_day(word):
    w = word.lower().strip()
    if w == "today":
        return datetime.datetime.now().strftime("%A")
    if w == "tomorrow":
        return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%A")
    return DAY_ALIASES.get(w)


def _extract_station(text):
    t = text.lower()
    for alias, name in STATION_ALIASES.items():
        if alias in t:
            return name
    return None


def _extract_class(text):
    t = text.lower()
    for alias, code in CLASS_ALIASES.items():
        if alias in t:
            return code
    return None


def _extract_day(text):
    t = text.lower()
    for alias in DAY_ALIASES:
        if alias in t:
            return _resolve_day(alias)
    return None


def _search_trains_for_chat(from_s, to_s, day, seat_class):
    """Returns list of matching trains (same logic as /search)."""
    results = []
    for t in TRAINS:
        if day not in t["days"] and "Daily" not in t["days"]:
            continue
        stations = [r["station"] for r in t["route"]]
        if from_s not in stations or to_s not in stations:
            continue
        idx_from = stations.index(from_s)
        idx_to   = stations.index(to_s)
        if idx_from >= idx_to:
            continue
        start = t["route"][idx_from]
        end   = t["route"][idx_to]
        dist  = end["dist"] - start["dist"]
        t1 = datetime.datetime.strptime(start["dep"], "%H:%M")
        t2 = datetime.datetime.strptime(end["arr"],   "%H:%M")
        if t2 < t1:
            t2 += datetime.timedelta(days=1)
        total_min = int((t2 - t1).total_seconds() // 60)
        h, m = divmod(total_min, 60)
        is_premium = t["id"] in PREMIUM_TRAIN_IDS
        class_map  = PREMIUM_CLASSES if is_premium else CLASSES
        resolved   = seat_class if seat_class in class_map else next(iter(class_map))
        cls_info   = class_map[resolved]
        fare       = int(dist * t["base_fare"] * cls_info["multiplier"])
        results.append({
            "id": t["id"], "name": t["name"],
            "dep": start["dep"], "arr": end["arr"],
            "duration": f"{h}h {m:02d}m",
            "fare": fare, "seatClass": resolved,
            "classLabel": cls_info["label"],
            "idxFrom": idx_from, "idxTo": idx_to,
        })
    return results


def _handle_info_query(msg):
    """
    Returns a string reply for informational queries, or None if not matched.
    """
    m = msg.lower()

    # Live train status
    train_match = re.search(r"\b(\d{4,5})\b", msg)
    if train_match and any(w in m for w in ("where", "live", "status", "location", "running", "track")):
        tid = int(train_match.group(1))
        if tid in TRAIN_BY_ID:
            s = _fake_live_status(tid)
            return f"🚆 <b>{TRAIN_BY_ID[tid]['name']}</b>: {s.get('message', 'Status unavailable')}"
        return "I couldn't find that train number. Try one of: " + ", ".join(str(t["id"]) for t in TRAINS)

    if any(w in m for w in ("station", "stop", "cover", "route", "corridor")):
        return ("QuickRail covers the Tamil Nadu Southern Corridor — "
                "<b>Chennai → Trichy → Madurai → Coimbatore → Tirunelveli</b> (650 km).")

    if any(w in m for w in ("fare", "price", "cost", "class", "sleeper", "ac", "chair", "class")):
        return ("We have <b>5 seat classes</b>:<br>"
                "• <b>SL</b> Sleeper &nbsp;• <b>3A</b> AC 3-Tier &nbsp;• <b>2A</b> AC 2-Tier<br>"
                "• <b>CC</b> Chair Car &nbsp;• <b>EC</b> Executive Chair (Vande Bharat / Tejas only)<br>"
                "Fares depend on distance. Search a route to see exact prices.")

    if any(w in m for w in ("cancel", "refund")):
        return "You can cancel any booking from <b>My Journeys</b>. A 90% refund is applied instantly."

    if any(w in m for w in ("train", "schedule", "time", "when")):
        lines = []
        for t in TRAINS:
            days_str = "Daily" if "Daily" in t["days"] else ", ".join(t["days"][:3]) + ("…" if len(t["days"]) > 3 else "")
            lines.append(f"• <b>{t['name']}</b> ({t['id']}) — {days_str}")
        return "Trains on our corridor:<br>" + "<br>".join(lines)

    if any(w in m for w in ("pnr", "booking", "journey", "ticket")):
        return "All your bookings are under <b>My Journeys</b> in the sidebar. You can view the e-ticket or cancel there."

    if any(w in m for w in ("pay", "payment", "money", "razorpay", "upi")):
        return "QuickRail confirms bookings <b>instantly</b> with no payment required — this is a demo project."

    if any(w in m for w in ("waitlist", "wait", "queue", "full", "no seat")):
        return ("If all seats are taken for your route, you're added to a <b>1-hour waitlist</b>. "
                "If someone cancels within that window, the seat is auto-assigned to you.")

    if any(w in m for w in ("hi", "hello", "hey", "namaste")):
        return ("👋 Hi! I'm your QuickRail assistant.<br>"
                "I can help you <b>search and book trains</b>, check <b>live status</b>, "
                "or answer questions about fares and schedules.<br>"
                "Just say something like: <i>\"Book Chennai to Madurai on Friday\"</i>")

    if any(w in m for w in ("thanks", "thank", "great", "ok", "okay", "cool")):
        return "Happy to help! Have a good journey. 🚆"

    return None


# States: idle → ask_from → ask_to → ask_day → ask_class → ask_name
#          → ask_phone → ask_dob → pick_train → confirm → done

@app.route("/chat", methods=["POST"])
def chat():
    msg   = (request.get_json(silent=True) or {}).get("message", "").strip()
    state = session.get(_CHAT_KEY, {"step": "idle"})

    msg_l = msg.lower()

    # ── Cancel / reset mid-flow ──
    if any(w in msg_l for w in ("cancel", "reset", "restart", "stop", "quit", "nevermind", "start over")):
        if state["step"] not in ("idle",):
            session[_CHAT_KEY] = {"step": "idle"}
            return jsonify({"reply": "Booking cancelled. How else can I help you?"})

    # ── Trigger booking intent from idle ──
    booking_trigger = any(w in msg_l for w in ("book", "reserve", "ticket", "travel", "journey", "buy"))

    # ── Handle info queries in idle / non-blocking steps ──
    if state["step"] == "idle" and not booking_trigger:
        info = _handle_info_query(msg)
        if info:
            return jsonify({"reply": info})
        # Try to detect booking intent with station names even without trigger word
        frm = _extract_station(msg)
        if frm:
            booking_trigger = True

    # ── Start booking flow ──
    if state["step"] == "idle" and booking_trigger:
        # Try to pre-fill as much as possible from the first message
        frm   = _extract_station(msg)
        to    = _extract_station(msg.replace(frm.lower() if frm else "", "", 1)) if frm else None
        day   = _extract_day(msg)
        cls   = _extract_class(msg)

        # if both stations present but same → ignore
        if frm and to and frm == to:
            to = None

        state = {
            "step":  "idle",
            "from":  frm,
            "to":    to,
            "day":   day,
            "class": cls or "SL",
        }

        # Advance to the first missing field
        if not state["from"]:
            state["step"] = "ask_from"
            session[_CHAT_KEY] = state
            return jsonify({"reply": "Sure! Which station are you travelling <b>from</b>?<br>"
                            "<small>Chennai · Trichy · Madurai · Coimbatore · Tirunelveli</small>"})
        if not state["to"]:
            state["step"] = "ask_to"
            session[_CHAT_KEY] = state
            return jsonify({"reply": f"Got it — from <b>{state['from']}</b>. Where are you going <b>to</b>?"})
        if not state["day"]:
            state["step"] = "ask_day"
            session[_CHAT_KEY] = state
            return jsonify({"reply": f"<b>{state['from']} → {state['to']}</b>. Which day?<br>"
                            "<small>Monday · Tuesday · Wednesday … or just say 'today' / 'tomorrow'</small>"})

        state["step"] = "ask_class"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"Almost there — <b>{state['from']} → {state['to']}</b> on <b>{state['day']}</b>.<br>"
                        "Which seat class? <small>SL · 3A · 2A · CC · EC</small>"})

    # ── ask_from ──
    if state["step"] == "ask_from":
        frm = _extract_station(msg)
        if not frm:
            return jsonify({"reply": "I didn't catch that station. Please choose one of:<br>"
                            "Chennai · Trichy · Madurai · Coimbatore · Tirunelveli"})
        state["from"] = frm
        state["step"] = "ask_to"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"Great — from <b>{frm}</b>. Where to?"})

    # ── ask_to ──
    if state["step"] == "ask_to":
        to = _extract_station(msg)
        if not to:
            return jsonify({"reply": "Please name a destination station."})
        if to == state.get("from"):
            return jsonify({"reply": "Origin and destination can't be the same. Where are you going?"})
        state["to"]   = to
        state["step"] = "ask_day"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"<b>{state['from']} → {to}</b>. Which day of travel?"})

    # ── ask_day ──
    if state["step"] == "ask_day":
        day = _extract_day(msg)
        if not day:
            # Try direct match
            for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
                if d.lower() in msg_l:
                    day = d
                    break
        if not day:
            return jsonify({"reply": "Please tell me the day — e.g. Monday, Friday, or 'today'."})
        state["day"]  = day
        state["step"] = "ask_class"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"Day: <b>{day}</b>. Which seat class?<br>"
                        "<small>SL (Sleeper) · 3A (AC 3-Tier) · 2A (AC 2-Tier) · CC (Chair Car) · EC (Exec. Chair)</small>"})

    # ── ask_class ──
    if state["step"] == "ask_class":
        cls = _extract_class(msg)
        if not cls:
            cls = "SL"   # default
        state["class"] = cls
        state["step"]  = "pick_train"
        session[_CHAT_KEY] = state

        trains = _search_trains_for_chat(state["from"], state["to"], state["day"], cls)
        if not trains:
            session[_CHAT_KEY] = {"step": "idle"}
            return jsonify({"reply": f"No trains found for <b>{state['from']} → {state['to']}</b> "
                            f"on <b>{state['day']}</b>. Try a different day or route."})

        state["trains"] = trains
        session[_CHAT_KEY] = state

        lines = [f"Found <b>{len(trains)}</b> train(s):<br>"]
        for i, t in enumerate(trains, 1):
            lines.append(f"<b>{i}.</b> {t['name']} ({t['id']}) — "
                         f"{t['dep']}→{t['arr']} · {t['duration']} · ₹{t['fare']} ({t['classLabel']})")
        lines.append("<br>Reply with the <b>number</b> to select (e.g. <i>1</i>).")
        return jsonify({"reply": "<br>".join(lines)})

    # ── pick_train ──
    if state["step"] == "pick_train":
        trains = state.get("trains", [])
        # Try to parse a number
        num_match = re.search(r"\b(\d+)\b", msg)
        if not num_match or int(num_match.group(1)) < 1 or int(num_match.group(1)) > len(trains):
            return jsonify({"reply": f"Please reply with a number between 1 and {len(trains)}."})
        chosen = trains[int(num_match.group(1)) - 1]
        state["train"]  = chosen
        state["step"]   = "ask_name"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"Selected: <b>{chosen['name']}</b> · "
                        f"{chosen['dep']}→{chosen['arr']} · ₹{chosen['fare']}<br>"
                        "Passenger name?"})

    # ── ask_name ──
    if state["step"] == "ask_name":
        name = msg.strip().title()
        if len(name) < 2:
            return jsonify({"reply": "Please enter a valid passenger name."})
        state["pax_name"] = name
        state["step"]     = "ask_phone"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"Name: <b>{name}</b>. Passenger mobile number (10 digits)?"})

    # ── ask_phone ──
    if state["step"] == "ask_phone":
        phone = re.sub(r"\D", "", msg)
        if len(phone) != 10:
            return jsonify({"reply": "Please enter a valid 10-digit phone number."})
        state["pax_phone"] = phone
        state["step"]      = "ask_dob"
        session[_CHAT_KEY] = state
        return jsonify({"reply": f"Phone: <b>{phone}</b>. Date of birth? (DD/MM/YYYY)"})

    # ── ask_dob ──
    if state["step"] == "ask_dob":
        dob_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", msg)
        if not dob_match:
            return jsonify({"reply": "Please enter DOB in DD/MM/YYYY format."})
        dob = dob_match.group(1).replace("-", "/")
        state["pax_dob"] = dob
        state["step"]    = "confirm"
        session[_CHAT_KEY] = state

        t = state["train"]
        return jsonify({"reply":
            f"<b>Booking summary:</b><br>"
            f"🚆 {t['name']} ({t['id']})<br>"
            f"📍 {state['from']} → {state['to']} · {state['day']}<br>"
            f"⏱ {t['dep']} → {t['arr']} ({t['duration']})<br>"
            f"🪑 {t['classLabel']} · ₹{t['fare']}<br>"
            f"👤 {state['pax_name']} · {state['pax_phone']} · {dob}<br><br>"
            "Type <b>confirm</b> to book, or <b>cancel</b> to abort."
        })

    # ── confirm ──
    if state["step"] == "confirm":
        if "confirm" in msg_l:
            if "user_id" not in session:
                session[_CHAT_KEY] = {"step": "idle"}
                return jsonify({"reply": "⚠️ You need to be logged in to book. Please sign in first."})

            t      = state["train"]
            pnr    = "QR-" + str(random.randint(100000, 999999))
            alloc  = find_seats_for_range(
                t["id"], state["day"], t["seatClass"],
                t["idxFrom"], t["idxTo"]
            )

            if alloc is None:
                # Waitlist
                expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                booking = Booking(
                    pnr=pnr, user_id=session["user_id"],
                    train_id=t["id"], train_name=t["name"],
                    from_station=state["from"], to_station=state["to"],
                    travel_day=state["day"],
                    dep_time=t["dep"], arr_time=t["arr"], duration=t["duration"],
                    seat_class=t["seatClass"], class_label=t["classLabel"],
                    fare=t["fare"],
                    passenger_name=state["pax_name"],
                    passenger_phone=state["pax_phone"],
                    passenger_dob=state["pax_dob"],
                    seat_assignments="Waitlisted",
                    status="waitlisted", waitlist_until=expires,
                )
                db.session.add(booking)
                entry = WaitlistEntry(
                    pnr=pnr, user_id=session["user_id"],
                    train_id=t["id"], travel_day=state["day"],
                    seat_class=t["seatClass"],
                    start_idx=t["idxFrom"], end_idx=t["idxTo"],
                    expires_at=expires,
                )
                db.session.add(entry)
                db.session.commit()
                session[_CHAT_KEY] = {"step": "idle"}
                return jsonify({"reply":
                    f"⏳ No seats available right now. You're on the <b>waitlist</b> (PNR: <b>{pnr}</b>).<br>"
                    f"If a seat frees up within 1 hour, it'll be auto-assigned. Check My Journeys for updates."
                })

            train_data = TRAIN_BY_ID[t["id"]]
            route      = train_data["route"]
            is_split   = len(alloc) > 1
            parts      = []
            for (seat_num, seg_s, seg_e) in alloc:
                sb = SegmentBooking(
                    pnr=pnr, train_id=t["id"], travel_day=state["day"],
                    seat_class=t["seatClass"], seat_number=seat_num,
                    start_idx=seg_s, end_idx=seg_e,
                )
                db.session.add(sb)
                if is_split:
                    label = f"{route[seg_s]['station']}→{route[seg_e]['station']}"
                    parts.append(f"Seat {seat_num} ({label})")
                else:
                    parts.append(str(seat_num))

            seat_str = ", ".join(parts)
            booking = Booking(
                pnr=pnr, user_id=session["user_id"],
                train_id=t["id"], train_name=t["name"],
                from_station=state["from"], to_station=state["to"],
                travel_day=state["day"],
                dep_time=t["dep"], arr_time=t["arr"], duration=t["duration"],
                seat_class=t["seatClass"], class_label=t["classLabel"],
                fare=t["fare"],
                passenger_name=state["pax_name"],
                passenger_phone=state["pax_phone"],
                passenger_dob=state["pax_dob"],
                seat_assignments=seat_str,
                is_split=is_split, status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()
            session[_CHAT_KEY] = {"step": "idle"}

            split_note = (f"<br>⚠️ Seat change mid-journey: {seat_str}" if is_split else "")
            return jsonify({"reply":
                f"✅ <b>Booking Confirmed!</b><br>"
                f"PNR: <b>{pnr}</b><br>"
                f"Seat(s): <b>{seat_str}</b>{split_note}<br>"
                f"View your e-ticket in <b>My Journeys</b>."
            })

        session[_CHAT_KEY] = {"step": "idle"}
        return jsonify({"reply": "Booking cancelled. Let me know if you need anything else."})

    # ── Fallback: info query at any step ──
    info = _handle_info_query(msg)
    if info:
        return jsonify({"reply": info})

    return jsonify({"reply":
        "I didn't quite catch that. You can ask about fares, schedules, live train status, "
        "or say <b>'Book Chennai to Coimbatore on Monday'</b> to start a booking."
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)