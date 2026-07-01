# QuickRail 🚆

A train search and booking demo for the Tamil Nadu Southern Corridor —
Chennai → Trichy → Madurai → Coimbatore → Tirunelveli.

**Live demo:** add-your-vercel-url-here

> ⚠️ **This is a demo/student project.** Trains, schedules, live tracking, and
> bookings shown here are simulated and do not represent real Indian Railways
> services. No real tickets are issued and no real payment is processed.

## Features

- Search trains without signing in
- Sign in with just a mobile number — simulated OTP shown on screen, no SMS cost
- 5 seat classes (Sleeper, AC 3-Tier, AC 2-Tier, Chair Car, Executive Chair)
- **Segment-based seat allocation** — a seat can be shared by multiple
  passengers travelling different, non-overlapping parts of the same route,
  instead of being locked for the whole journey
- Coach-style seat map that shows which seats are free for *your* segment,
  even if they're booked for someone else's
- Automatic seat-splitting when no single seat covers your full journey
- 1-hour waitlist with automatic seat assignment on cancellation
- Simulated live train tracking (time-based position estimate, no real GPS)
- Rule-based conversational chatbot that can search, book, and answer
  questions — writes to the same database as the manual booking flow
- Instant booking confirmation — no payment step
- Cancel bookings with automatic 90% refund

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** PostgreSQL (Neon) in production, SQLite locally
- **Auth:** Mobile number + simulated OTP (no SMS gateway)
- **Frontend:** HTML, CSS, JavaScript (no framework)
- **Hosting:** Vercel

## Project Structure
quickrail/

├── api/index.py

├── templates/

│   ├── index.html

│   └── dashboard.html

├── static/

│   ├── style.css

│   ├── script.js

│   └── chatbot.js

├── vercel.json

└── requirements.txt

## Running Locally

```bash
pip install -r requirements.txt --break-system-packages
python api/index.py
```

Visit `http://localhost:5000`. With no environment variables set, it runs in
demo mode — full functionality, SQLite database, OTP shown directly on
screen instead of sent via SMS.

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Required in production — random string for session security |
| `DATABASE_URL` | PostgreSQL connection string (Neon) |

## Notes

Built as a learning project with help from AI tools (Claude) for code
generation, debugging, and learning Flask, databases, and full-stack
development hands-on.