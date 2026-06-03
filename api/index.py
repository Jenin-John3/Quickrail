import os
from flask import Flask, request, jsonify, render_template
import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static")
)

TRAINS = [
    {
        "id": 12631,
        "name": "Nellai Superfast",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "base_fare": 1.25,
        "route": [
            {"station": "Chennai", "arr": "19:50", "dep": "20:10", "dist": 0},
            {"station": "Trichy", "arr": "01:10", "dep": "01:15", "dist": 340},
            {"station": "Madurai", "arr": "03:50", "dep": "03:55", "dist": 495},
            {"station": "Tirunelveli", "arr": "06:40", "dep": "07:00", "dist": 650}
        ]
    },
    {
        "id": 22631,
        "name": "Tejas Express",
        "days": ["Monday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "base_fare": 3.10,
        "route": [
            {"station": "Chennai", "arr": "06:00", "dep": "06:00", "dist": 0},
            {"station": "Trichy", "arr": "10:05", "dep": "10:10", "dist": 340},
            {"station": "Madurai", "arr": "12:15", "dep": "12:15", "dist": 495}
        ]
    },
    {
        "id": 20665,
        "name": "Vande Bharat Exp",
        "days": ["Monday", "Tuesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "base_fare": 4.50,
        "route": [
            {"station": "Chennai", "arr": "13:30", "dep": "13:30", "dist": 0},
            {"station": "Trichy", "arr": "17:30", "dep": "17:35", "dist": 340},
            {"station": "Madurai", "arr": "19:20", "dep": "19:20", "dist": 495},
            {"station": "Tirunelveli", "arr": "21:15", "dep": "21:15", "dist": 650}
        ]
    },
    {
        "id": 12633,
        "name": "Kanyakumari Exp",
        "days": ["Daily"],
        "base_fare": 1.15,
        "route": [
            {"station": "Chennai", "arr": "17:15", "dep": "17:15", "dist": 0},
            {"station": "Trichy", "arr": "22:15", "dep": "22:20", "dist": 340},
            {"station": "Madurai", "arr": "01:15", "dep": "01:20", "dist": 495},
            {"station": "Tirunelveli", "arr": "03:55", "dep": "04:00", "dist": 650}
        ]
    },
    {
        "id": 12605,
        "name": "Pallavan Express",
        "days": ["Daily"],
        "base_fare": 1.40,
        "route": [
            {"station": "Chennai", "arr": "15:45", "dep": "15:45", "dist": 0},
            {"station": "Trichy", "arr": "20:50", "dep": "20:50", "dist": 340}
        ]
    },
    {
        "id": 12637,
        "name": "Pandian Express",
        "days": ["Daily"],
        "base_fare": 1.35,
        "route": [
            {"station": "Chennai", "arr": "21:40", "dep": "21:40", "dist": 0},
            {"station": "Trichy", "arr": "02:45", "dep": "02:50", "dist": 340},
            {"station": "Madurai", "arr": "05:20", "dep": "05:20", "dist": 495}
        ]
    },
    {
        "id": 16101,
        "name": "Boat Mail Exp",
        "days": ["Daily"],
        "base_fare": 1.10,
        "route": [
            {"station": "Chennai", "arr": "20:15", "dep": "20:15", "dist": 0},
            {"station": "Trichy", "arr": "01:55", "dep": "02:00", "dist": 340},
            {"station": "Madurai", "arr": "04:40", "dep": "04:45", "dist": 495}
        ]
    },
    {
        "id": 12635,
        "name": "Vaigai Express",
        "days": ["Daily"],
        "base_fare": 1.50,
        "route": [
            {"station": "Chennai", "arr": "12:15", "dep": "12:15", "dist": 0},
            {"station": "Trichy", "arr": "16:30", "dep": "16:35", "dist": 340},
            {"station": "Madurai", "arr": "18:45", "dep": "18:45", "dist": 495}
        ]
    },
    {
        "id": 16127,
        "name": "Guruvayur Express",
        "days": ["Daily"],
        "base_fare": 1.20,
        "route": [
            {"station": "Chennai", "arr": "07:45", "dep": "07:45", "dist": 0},
            {"station": "Trichy", "arr": "13:10", "dep": "13:15", "dist": 340},
            {"station": "Madurai", "arr": "15:55", "dep": "16:00", "dist": 495},
            {"station": "Tirunelveli", "arr": "18:40", "dep": "18:45", "dist": 650}
        ]
    },
    {
        "id": 22671,
        "name": "Tirunelveli SF Exp",
        "days": ["Tuesday", "Wednesday", "Friday", "Saturday", "Sunday"],
        "base_fare": 1.60,
        "route": [
            {"station": "Chennai", "arr": "23:00", "dep": "23:00", "dist": 0},
            {"station": "Trichy", "arr": "03:45", "dep": "03:50", "dist": 340},
            {"station": "Madurai", "arr": "06:20", "dep": "06:25", "dist": 495},
            {"station": "Tirunelveli", "arr": "09:05", "dep": "09:05", "dist": 650}
        ]
    },
    {
        "id": 16723,
        "name": "Ananthapuri Express",
        "days": ["Monday", "Wednesday", "Saturday"],
        "base_fare": 1.30,
        "route": [
            {"station": "Chennai", "arr": "10:30", "dep": "10:30", "dist": 0},
            {"station": "Trichy", "arr": "16:00", "dep": "16:05", "dist": 340},
            {"station": "Madurai", "arr": "18:50", "dep": "18:55", "dist": 495},
            {"station": "Tirunelveli", "arr": "21:30", "dep": "21:30", "dist": 650}
        ]
    }
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/search", methods=["POST"])
def search():
    data = request.json
    u_from = data.get("from")
    u_to = data.get("to")
    u_day = data.get("day")

    results = []

    for t in TRAINS:
        if u_day not in t["days"] and "Daily" not in t["days"]:
            continue

        stations = [r["station"] for r in t["route"]]
        if u_from in stations and u_to in stations:
            idx_from = stations.index(u_from)
            idx_to = stations.index(u_to)

            if idx_from < idx_to:
                start = t["route"][idx_from]
                end = t["route"][idx_to]

                dist = end["dist"] - start["dist"]
                total_fare = int(dist * t["base_fare"])

                t1 = datetime.datetime.strptime(start["dep"], "%H:%M")
                t2 = datetime.datetime.strptime(end["arr"], "%H:%M")
                if t2 < t1:
                    t2 += datetime.timedelta(days=1)

                total_minutes = int((t2 - t1).total_seconds() // 60)
                h, m = divmod(total_minutes, 60)
                duration = f"{h}h {m:02d}m"

                results.append({
                    "name": t["name"],
                    "dep": start["dep"],
                    "arr": end["arr"],
                    "duration": duration,
                    "fare": total_fare,
                    "id": t["id"]
                })

    return jsonify(results)

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower()

    responses = {
        ("hi", "hello", "hey"): "Welcome to QuickRail Command Center. I am your transit AI. How can I help?",
        ("fare", "price", "cost", "ticket"): "Fares depend on the train and route. Search your route and I will help you through booking.",
        ("pnr", "status", "booking"): "After dummy payment, your confirmed e-ticket appears instantly and is also saved in My Journey.",
        ("cancel", "refund"): "You can cancel a confirmed booking from My Journey and receive a 90% refund instantly.",
        ("thanks", "thank"): "At your service. Safe travels across the network.",
        ("train", "schedule", "route"): "We cover Chennai, Trichy, Madurai, and Tirunelveli. Use the search panel to find available trains.",
        ("station", "stop"): "Available stations are Chennai, Trichy, Madurai, and Tirunelveli.",
        ("name", "dob", "number"): "During booking, please enter traveller name, mobile number, and date of birth before payment."
    }

    for keys, reply in responses.items():
        if any(k in msg for k in keys):
            return jsonify({"reply": reply})

    return jsonify({"reply": "I can help with train search, booking, payment, cancellation, refund, and ticket confirmation."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
