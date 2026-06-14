# QuickRail 🚆

A simple train search and booking platform for the Chennai → Trichy → Madurai → Tirunelveli corridor in Tamil Nadu.

**Live demo:** add-your-vercel-url-here

## Problem

Booking trains in Tamil Nadu is often too complicated for a quick phone search — endless verification steps, no clear pricing, and many people end up paying agents extra just to get a ticket booked.

QuickRail is a simplified alternative: search instantly without an account, see real seat availability and pricing upfront, and book with real payments in under a minute.

## Features

- Search trains without signing in
- 5 seat classes (Sleeper, AC 3-Tier, AC 2-Tier, Chair Car, Executive Chair)
- Real-time seat map — no double bookings
- Multi-step booking: seat → passenger details → payment → e-ticket
- Real payments via Razorpay (UPI/cards/netbanking), with demo mode if no keys are set
- Cancel bookings with automatic 90% refund
- In-app chat assistant

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** PostgreSQL (Neon) in production, SQLite locally
- **Payments:** Razorpay
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

Visit `http://localhost:5000`. With no environment variables set, it runs in demo mode — full functionality, simulated payments, SQLite database.

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Required in production — random string for session security |
| `DATABASE_URL` | PostgreSQL connection string (Neon) |
| `RAZORPAY_KEY_ID` | Enables real payments (optional) |
| `RAZORPAY_KEY_SECRET` | Pairs with the above (optional) |

## Notes

Built as a learning project with help from AI tools (Claude) for code generation, debugging, and learning Flask, databases, and payment integration hands-on.
