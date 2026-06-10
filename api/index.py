import os
import datetime
from flask import Flask, request, jsonify, render_template

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static")
)

# ── Seat classes ──────────────────────────────────────────
# multiplier is applied on top of each train's per-km base_fare
CLASSES = {
    "SL": {"label": "Sleeper",     "multiplier": 1.0},
    "3A": {"label": "AC 3-Tier",   "multiplier": 2.6},
    "2A": {"label": "AC 2-Tier",   "multiplier": 3.9},
}

# Premium trains (Vande Bharat / Tejas) only offer chair-car classes
PREMIUM_CLASSES = {
    "CC": {"label": "Chair Car",   "multiplier": 1.0},
    "EC": {"label": "Exec. Chair", "multiplier": 1.85},
}

PREMIUM_TRAIN_IDS = {20665, 22631}   # Vande Bharat, Tejas

# ── Train data ────────────────────────────────────────────
TRAINS = [
    {
        "id": 12631,
        "name": "Nellai Superfast",
        "days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 1.25,
        "route": [
            {"station": "Chennai",      "arr": "19:50", "dep": "20:10", "dist": 0},
            {"station": "Trichy",       "arr": "01:10", "dep": "01:15", "dist": 340},
            {"station": "Madurai",      "arr": "03:50", "dep": "03:55", "dist": 495},
            {"station": "Tirunelveli", "arr": "06:40", "dep": "07:00", "dist": 650},
        ],
    },
    {
        "id": 22631,
        "name": "Tejas Express",
        "days": ["Monday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 3.10,
        "route": [
            {"station": "Chennai", "arr": "06:00", "dep": "06:00", "dist": 0},
            {"station": "Trichy",  "arr": "10:05", "dep": "10:10", "dist": 340},
            {"station": "Madurai", "arr": "12:15", "dep": "12:15", "dist": 495},
        ],
    },
    {
        "id": 20665,
        "name": "Vande Bharat Exp",
        "days": ["Monday","Tuesday","Thursday","Friday","Saturday","Sunday"],
        "base_fare": 4.50,
        "route": [
            {"station": "Chennai",      "arr": "13:30", "dep": "13:30", "dist": 0},
            {"station": "Trichy",       "arr": "17:30", "dep": "17:35", "dist": 340},
            {"station": "Madurai",      "arr": "19:20", "dep": "19:20", "dist": 495},
            {"station": "Tirunelveli", "arr": "21:15", "dep": "21:15", "dist": 650},
        ],
    },
    {
        "id": 12633,
        "name": "Kanyakumari Exp",
        "days": ["Daily"],
        "base_fare": 1.15,
        "route": [
            {"station": "Chennai",      "arr": "17:15", "dep": "17:15", "dist": 0},
            {"station": "Trichy",       "arr": "22:15", "dep": "22:20", "dist": 340},
            {"station": "Madurai",      "arr": "01:15", "dep": "01:20", "dist": 495},
            {"station": "Tirunelveli", "arr": "03:55", "dep": "04:00", "dist": 650},
        ],
    },
    {
        "id": 12605,
        "name": "Pallavan Express",
        "days": ["Daily"],
        "base_fare": 1.40,
        "route": [
            {"station": "Chennai", "arr": "15:45", "dep": "15:45", "dist": 0},
            {"station": "Trichy",  "arr": "20:50", "dep": "20:50", "dist": 340},
        ],
    },
    {
        "id": 12637,
        "name": "Pandian Express",
        "days": ["Daily"],
        "base_fare": 1.35,
        "route": [
            {"station": "Chennai", "arr": "21:40", "dep": "21:40", "dist": 0},
            {"station": "Trichy",  "arr": "02:45", "dep": "02:50", "dist": 340},
            {"station": "Madurai", "arr": "05:20", "dep": "05:20", "dist": 495},
        ],
    },
    {
        "id": 16101,
        "name": "Boat Mail Exp",
        "days": ["Daily"],
        "base_fare": 1.10,
        "route": [
            {"station": "Chennai", "arr": "20:15", "dep": "20:15", "dist": 0},
            {"station": "Trichy",  "arr": "01:55", "dep": "02:00", "dist": 340},
            {"station": "Madurai", "arr": "04:40", "dep": "04:45", "dist": 495},
        ],
    },
    {
        "id": 12635,
        "name": "Vaigai Express",
        "days": ["Daily"],
        "base_fare": 1.50,
        "route": [
            {"station": "Chennai", "arr": "12:15", "dep": "12:15", "dist": 0},
            {"station": "Trichy",  "arr": "16:30", "dep": "16:35", "dist": 340},
            {"station": "Madurai", "arr": "18:45", "dep": "18:45", "dist": 495},
        ],
    },
    {
        "id": 16127,
        "name": "Guruvayur Express",
        "days": ["Daily"],
        "base_fare": 1.20,
        "route": [
            {"station": "Chennai",      "arr": "07:45", "dep": "07:45", "dist": 0},
            {"station": "Trichy",       "arr": "13:10", "dep": "13:15", "dist": 340},
            {"station": "Madurai",      "arr": "15:55", "dep": "16:00", "dist": 495},
            {"station": "Tirunelveli", "arr": "18:40", "dep": "18:45", "dist": 650},
        ],
    },
    {
        "id": 22671,
        "name": "Tirunelveli SF Exp",
        "days": ["Tuesday","Wednesday","Friday","Saturday","Sunday"],
        "base_fare": 1.60,
        "route": [
            {"station": "Chennai",      "arr": "23:00", "dep": "23:00", "dist": 0},
            {"station": "Trichy",       "arr": "03:45", "dep": "03:50", "dist": 340},
            {"station": "Madurai",      "arr": "06:20", "dep": "06:25", "dist": 495},
            {"station": "Tirunelveli", "arr": "09:05", "dep": "09:05", "dist": 650},
        ],
    },
    {
        "id": 16723,
        "name": "Ananthapuri Express",
        "days": ["Monday","Wednesday","Saturday"],
        "base_fare": 1.30,
        "route": [
            {"station": "Chennai",      "arr": "10:30", "dep": "10:30", "dist": 0},
            {"station": "Trichy",       "arr": "16:00", "dep": "16:05", "dist": 340},
            {"station": "Madurai",      "arr": "18:50", "dep": "18:55", "dist": 495},
            {"station": "Tirunelveli", "arr": "21:30", "dep": "21:30", "dist": 650},
        ],
    },
]


# ── Routes ────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/search", methods=["POST"])
def search():
    data      = request.json
    u_from    = data.get("from", "")
    u_to      = data.get("to", "")
    u_day     = data.get("day", "")
    u_class   = data.get("seat_class", "SL")      # new: seat class from frontend

    # Resolve class map (premium trains use different classes)
    results = []

    for t in TRAINS:
        # Day filter
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

        # Duration
        t1 = datetime.datetime.strptime(start["dep"], "%H:%M")
        t2 = datetime.datetime.strptime(end["arr"],   "%H:%M")
        if t2 < t1:
            t2 += datetime.timedelta(days=1)
        total_min = int((t2 - t1).total_seconds() // 60)
        h, m = divmod(total_min, 60)
        duration = f"{h}h {m:02d}m"

        # Seat class & fare
        is_premium = t["id"] in PREMIUM_TRAIN_IDS
        class_map  = PREMIUM_CLASSES if is_premium else CLASSES

        # If the requested class doesn't exist on this train, use the cheapest available
        if u_class not in class_map:
            resolved_class = next(iter(class_map))
        else:
            resolved_class = u_class

        cls_info   = class_map[resolved_class]
        base_fare  = int(dist * t["base_fare"])
        final_fare = int(base_fare * cls_info["multiplier"])

        results.append({
            "id":          t["id"],
            "name":        t["name"],
            "dep":         start["dep"],
            "arr":         end["arr"],
            "duration":    duration,
            "fare":        final_fare,
            "seat_class":  resolved_class,
            "class_label": cls_info["label"],
            "is_premium":  is_premium,
        })

    return jsonify(results)


@app.route("/classes", methods=["POST"])
def get_classes():
    """Return available seat classes for a given train id."""
    train_id = request.json.get("train_id")
    is_premium = train_id in PREMIUM_TRAIN_IDS
    class_map  = PREMIUM_CLASSES if is_premium else CLASSES
    return jsonify([
        {"code": k, "label": v["label"]} for k, v in class_map.items()
    ])


@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower()

    responses = {
        ("hi", "hello", "hey"):
            "Hi! I'm the QuickRail assistant. Ask me about trains, fares, stations, or your bookings.",
        ("fare", "price", "cost", "ticket", "class", "sleeper", "ac"):
            "We offer three classes — Sleeper (SL), AC 3-Tier (3A), and AC 2-Tier (2A). "
            "Premium trains like Vande Bharat have Chair Car (CC) and Executive Chair (EC). "
            "Select your class in the search panel to see the exact fare.",
        ("pnr", "status", "booking", "journey"):
            "Your bookings are saved under 'My Journeys' in the sidebar. "
            "You can view your e-ticket or cancel there.",
        ("cancel", "refund"):
            "You can cancel any booking from 'My Journeys'. "
            "A 90% refund is processed back to your account within 24 hours.",
        ("station", "stop", "where"):
            "We currently cover four stations: Chennai, Trichy, Madurai, and Tirunelveli — "
            "along the 650 km southern corridor.",
        ("train", "schedule", "route", "when", "time"):
            "We have 11 trains on this corridor with departures spread across the day. "
            "Use the search panel to filter by route and day.",
        ("vande", "bharat", "tejas", "premium"):
            "Vande Bharat and Tejas are premium services with Chair Car and Executive Chair classes. "
            "They're faster but don't have sleeper berths.",
        ("jenin", "developer", "who built", "creator"):
            "QuickRail was built by Jenin — a project for the Chennai–Tirunelveli rail corridor.",
        ("thanks", "thank", "okay", "ok", "great"):
            "Happy to help. Have a good journey!",
    }

    for keys, reply in responses.items():
        if any(k in msg for k in keys):
            return jsonify({"reply": reply})

    return jsonify({
        "reply": "I didn't quite catch that. Try asking about fares, seat classes, stations, or your bookings."
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)