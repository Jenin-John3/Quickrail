<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuickRail | Search Trains</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        /* ── Layout ──────────────────────────────────── */
        .sidebar {
            width: 252px;
            height: 100vh;
            position: fixed;
            left: 0; top: 0;
            padding: 2.2rem 1.15rem;
            border-right: 1px solid var(--glass-border);
            background: rgba(2, 6, 23, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
            z-index: 100;
        }
        .main-content {
            margin-left: 252px;
            padding: 3rem 3.5rem;
            max-width: 1060px;
        }

        /* ── Nav items ───────────────────────────────── */
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 14px;
            border-radius: 12px;
            color: var(--text-dim);
            cursor: pointer;
            transition: background .2s, color .2s;
            margin-bottom: 4px;
            font-weight: 500;
            font-size: 0.87rem;
            border: 1px solid transparent;
        }
        .nav-item.active  { background: var(--primary-glow); color: var(--text-main); border-color: var(--glass-border); }
        .nav-item:hover:not(.active):not(.danger) { background: rgba(255,255,255,0.05); color: var(--text-main); }
        .nav-item.danger  { color: var(--danger); margin-top: auto; opacity: .75; }
        .nav-item.danger:hover { background: rgba(239,68,68,0.07); opacity: 1; }

        /* ── Search grid ─────────────────────────────── */
        .search-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr auto;
            gap: 14px;
            align-items: flex-end;
        }
        .field-label {
            display: block;
            font-size: 0.68rem;
            font-weight: 700;
            color: var(--text-muted);
            margin-bottom: 7px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        /* ── Class pill on result cards ──────────────── */
        .class-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 20px;
            letter-spacing: 0.4px;
            text-transform: uppercase;
        }
        .class-pill-sl { background: rgba(99,102,241,0.12); color: var(--primary); border: 1px solid rgba(99,102,241,0.2); }
        .class-pill-3a { background: rgba(34,211,238,0.1);  color: var(--accent);  border: 1px solid rgba(34,211,238,0.2); }
        .class-pill-2a { background: rgba(16,185,129,0.1);  color: var(--success); border: 1px solid rgba(16,185,129,0.2); }
        .class-pill-cc { background: rgba(251,191,36,0.1);  color: #fbbf24;        border: 1px solid rgba(251,191,36,0.2); }
        .class-pill-ec { background: rgba(239,68,68,0.1);   color: var(--danger);  border: 1px solid rgba(239,68,68,0.2); }

        /* ── Modal overlay ───────────────────────────── */
        .modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.82);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        /* ── Booking modal ───────────────────────────── */
        .bm-inner {
            width: 100%;
            max-width: 510px;
            position: relative;
            overflow: hidden;
            max-height: 92vh;
            display: flex;
            flex-direction: column;
        }
        .bm-header {
            padding: 1.5rem 1.75rem 1rem;
            border-bottom: 1px solid var(--glass-border);
            background: rgba(15,23,42,0.95);
            backdrop-filter: blur(20px);
            flex-shrink: 0;
        }
        .bm-body {
            overflow-y: auto;
            flex: 1;
        }
        .modal-step {
            padding: 1.4rem 1.75rem;
            flex-direction: column;
            gap: 1rem;
            display: none;
        }
        .step-footer {
            padding-top: 1rem;
            border-top: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .ind-track {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 0.9rem;
        }
        .ind-line  { flex: 1; height: 1px; background: var(--glass-border); }
        .ind-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 4px;
            font-size: 0.59rem;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        /* payment summary rows */
        .sum-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.83rem;
        }
        .sum-row span:first-child { color: var(--text-muted); }
        .sum-row span:last-child  { font-weight: 700; }

        /* ── Chat window ─────────────────────────────── */
        #chat-window {
            display: none;
            position: fixed;
            bottom: 104px; right: 26px;
            width: 362px; height: 480px;
            flex-direction: column;
            overflow: hidden;
            z-index: 3000;
            transition: opacity .38s cubic-bezier(.16,1,.3,1),
                        transform .38s cubic-bezier(.16,1,.3,1);
        }
        .chat-fab {
            position: fixed;
            bottom: 26px; right: 26px;
            width: 56px; height: 56px;
            border-radius: 16px;
            background: var(--primary);
            display: flex; align-items: center; justify-content: center;
            cursor: pointer;
            box-shadow: 0 10px 26px var(--primary-glow);
            z-index: 4000;
            transition: transform .2s, box-shadow .2s;
            border: none; padding: 0;
        }
        .chat-fab:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 16px 36px var(--primary-glow); }
    </style>
</head>
<body>

<!-- ══════════════ SIDEBAR ══════════════════════════════ -->
<aside class="sidebar">
    <div style="display:flex;align-items:center;gap:9px;margin-bottom:2.2rem;padding-left:4px;">
        <i data-lucide="train-front" style="color:var(--primary);" size="18"></i>
        <span style="font-size:1.25rem;font-weight:800;letter-spacing:-0.5px;">QuickRail</span>
    </div>

    <nav style="display:flex;flex-direction:column;flex:1;">
        <div class="nav-item active" id="nav-search" onclick="showSearch()">
            <i data-lucide="search" size="16"></i> Find Trains
        </div>
        <div class="nav-item" id="nav-journeys" onclick="activateJourneys()">
            <i data-lucide="ticket" size="16"></i> My Journeys
        </div>
        <div class="nav-item">
            <i data-lucide="navigation" size="16"></i> Live Status
        </div>
        <div class="nav-item">
            <i data-lucide="user-circle" size="16"></i> Profile
        </div>
        <div class="nav-item danger" onclick="location.href='/'">
            <i data-lucide="log-out" size="16"></i> Sign Out
        </div>
    </nav>

    <!-- Corridor info at bottom of sidebar -->
    <div style="margin-top:auto;padding:1rem;border-radius:12px;
                background:rgba(255,255,255,0.02);border:1px solid var(--glass-border);
                font-size:0.72rem;color:var(--text-muted);line-height:1.7;">
        <div style="font-weight:700;color:var(--text-dim);margin-bottom:4px;">Corridor</div>
        Chennai → Trichy → Madurai → Tirunelveli
        <div style="margin-top:6px;color:var(--text-muted);">650 km &nbsp;·&nbsp; 11 trains</div>
    </div>
</aside>

<!-- ══════════════ MAIN ══════════════════════════════════ -->
<main class="main-content">

    <!-- Page header -->
    <header style="margin-bottom:2.5rem;">
        <h1 id="page-title" style="font-size:1.75rem;font-weight:800;margin-bottom:0.3rem;letter-spacing:-0.5px;">
            Find a Train
        </h1>
        <p id="page-sub" style="color:var(--text-dim);font-size:0.87rem;">
            Search by route, day, and seat class. Booking takes under a minute.
        </p>
    </header>

    <!-- Search panel -->
    <section id="search-panel" class="glass-card" style="padding:1.85rem;margin-bottom:2rem;">
        <div class="search-grid">
            <div>
                <label class="field-label">From</label>
                <select id="fromStat">
                    <option>Chennai</option>
                    <option>Trichy</option>
                    <option>Madurai</option>
                    <option>Tirunelveli</option>
                </select>
            </div>
            <div>
                <label class="field-label">To</label>
                <select id="toStat">
                    <option>Tirunelveli</option>
                    <option>Madurai</option>
                    <option>Trichy</option>
                    <option>Chennai</option>
                </select>
            </div>
            <div>
                <label class="field-label">Day</label>
                <select id="day">
                    <option>Monday</option><option>Tuesday</option><option>Wednesday</option>
                    <option>Thursday</option><option>Friday</option>
                    <option>Saturday</option><option>Sunday</option>
                </select>
            </div>
            <div>
                <label class="field-label">Seat Class</label>
                <select id="seatClass">
                    <option value="SL">Sleeper (SL)</option>
                    <option value="3A">AC 3-Tier (3A)</option>
                    <option value="2A">AC 2-Tier (2A)</option>
                    <option value="CC">Chair Car (CC)</option>
                    <option value="EC">Exec. Chair (EC)</option>
                </select>
            </div>
            <button onclick="findTrains()" style="height:44px;padding:0 1.4rem;white-space:nowrap;">
                <i data-lucide="search" size="15"></i> Search
            </button>
        </div>

        <!-- Class hint -->
        <p id="class-hint" style="margin-top:1rem;font-size:0.76rem;color:var(--text-muted);
           padding:0.65rem 0.9rem;background:rgba(255,255,255,0.02);
           border-radius:8px;border:1px solid var(--glass-border);display:none;"></p>
    </section>

    <!-- Results -->
    <div id="results">
        <div style="text-align:center;padding:4rem 0;opacity:0.28;">
            <i data-lucide="train-front" size="40" style="margin-bottom:0.9rem;"></i>
            <p style="font-size:0.87rem;">Pick your route and class above, then click Search.</p>
        </div>
    </div>

</main>

<!-- ══════════════ BOOKING MODAL ════════════════════════ -->
<div id="booking-modal" class="modal-overlay">
    <div class="glass-card bm-inner">

        <!-- Sticky header -->
        <div class="bm-header">
            <button onclick="closeModal()"
                    style="position:absolute;top:14px;right:14px;background:transparent;
                           padding:5px;border:1px solid var(--glass-border);border-radius:7px;">
                <i data-lucide="x" size="15"></i>
            </button>
            <div style="padding-right:2rem;">
                <div id="modal-train-name" style="font-weight:800;font-size:1.05rem;margin-bottom:2px;"></div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:3px;">
                    <span id="modal-route"  style="color:var(--text-muted);font-size:0.76rem;font-weight:600;"></span>
                    <span id="modal-class-pill"></span>
                </div>
            </div>

            <!-- Step indicator -->
            <div id="ind-wrap">
                <div class="ind-track">
                    <div class="step-dot active"></div>
                    <div class="ind-line"></div>
                    <div class="step-dot"></div>
                    <div class="ind-line"></div>
                    <div class="step-dot"></div>
                </div>
                <div class="ind-labels">
                    <span>Seat</span><span>Details</span><span>Payment</span>
                </div>
            </div>
        </div>

        <!-- Scrollable steps -->
        <div class="bm-body">

            <!-- Step 1 · Seat selection -->
            <div id="step-1" class="modal-step" style="display:flex;">
                <p style="font-size:0.81rem;color:var(--text-dim);">
                    Available seats are shown below. Tap one to select it.
                </p>
                <div class="seat-map" id="seat-grid"></div>
                <div style="display:flex;gap:14px;font-size:0.67rem;color:var(--text-muted);font-weight:600;">
                    <span style="display:flex;align-items:center;gap:5px;">
                        <span style="width:9px;height:9px;border-radius:3px;
                                     background:rgba(255,255,255,0.03);
                                     border:1px solid var(--glass-border);"></span>Available
                    </span>
                    <span style="display:flex;align-items:center;gap:5px;">
                        <span style="width:9px;height:9px;border-radius:3px;background:var(--success);"></span>Selected
                    </span>
                    <span style="display:flex;align-items:center;gap:5px;">
                        <span style="width:9px;height:9px;border-radius:3px;background:rgba(100,116,139,0.3);"></span>Taken
                    </span>
                </div>
                <div class="step-footer">
                    <div>
                        <p style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">Fare</p>
                        <p id="fare-display" style="font-size:1.25rem;font-weight:800;color:var(--accent);">&#8377;0</p>
                    </div>
                    <button onclick="nextStep()" style="padding:.65rem 1.35rem;">
                        Continue <i data-lucide="arrow-right" size="14"></i>
                    </button>
                </div>
            </div>

            <!-- Step 2 · Passenger details -->
            <div id="step-2" class="modal-step">
                <p style="font-size:0.81rem;color:var(--text-dim);">
                    These details will appear on your e-ticket.
                </p>
                <div>
                    <label class="field-label">Full Name</label>
                    <input type="text" id="p-name" placeholder="As on your ID card" autocomplete="name">
                </div>
                <div>
                    <label class="field-label">Phone Number</label>
                    <input type="tel" id="p-phone" placeholder="10-digit mobile number"
                           maxlength="10" autocomplete="tel" inputmode="numeric">
                </div>
                <div>
                    <label class="field-label">Date of Birth</label>
                    <input type="date" id="p-dob" autocomplete="bday">
                </div>
                <div class="step-footer">
                    <button onclick="prevStep()"
                            style="background:transparent;color:var(--text-dim);border:1px solid var(--glass-border);">
                        <i data-lucide="arrow-left" size="14"></i> Back
                    </button>
                    <button onclick="nextStep()" style="padding:.65rem 1.35rem;">
                        Review booking <i data-lucide="arrow-right" size="14"></i>
                    </button>
                </div>
            </div>

            <!-- Step 3 · Payment -->
            <div id="step-3" class="modal-step">
                <p style="font-size:0.81rem;color:var(--text-dim);">
                    Check your booking details before paying.
                </p>

                <div style="background:rgba(255,255,255,0.025);border:1px solid var(--glass-border);
                            border-radius:13px;padding:1.1rem 1.15rem;
                            display:flex;flex-direction:column;gap:0.65rem;">
                    <div class="sum-row"><span>Train</span>      <span id="ps-train"></span></div>
                    <div class="sum-row"><span>Route</span>      <span id="ps-route"></span></div>
                    <div class="sum-row"><span>Class</span>      <span id="ps-class"></span></div>
                    <div class="sum-row"><span>Seat</span>       <span id="ps-seat"></span></div>
                    <div class="sum-row"><span>Passenger</span>  <span id="ps-name"></span></div>
                    <div style="border-top:1px solid var(--glass-border);padding-top:0.65rem;" class="sum-row">
                        <span style="font-weight:700;color:var(--text-main);font-size:0.9rem;">Total</span>
                        <span id="ps-fare" style="font-size:1.15rem;font-weight:800;color:var(--success);"></span>
                    </div>
                </div>

                <div style="background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.14);
                            border-radius:11px;padding:0.85rem;
                            display:flex;align-items:center;gap:9px;">
                    <i data-lucide="shield-check" size="16" style="color:var(--primary);flex-shrink:0;"></i>
                    <p style="font-size:0.75rem;color:var(--text-dim);margin:0;">
                        Demo mode — no real payment is processed.
                    </p>
                </div>

                <div class="step-footer">
                    <button onclick="prevStep()"
                            style="background:transparent;color:var(--text-dim);border:1px solid var(--glass-border);">
                        <i data-lucide="arrow-left" size="14"></i> Back
                    </button>
                    <button id="pay-btn" onclick="processPayment()" style="padding:.7rem 1.6rem;">
                        Pay &#8377;0 <i data-lucide="credit-card" size="14"></i>
                    </button>
                </div>
            </div>

            <!-- Step 4 · E-ticket -->
            <div id="step-4" class="modal-step">
                <div style="display:flex;align-items:center;justify-content:center;gap:7px;
                            color:var(--success);font-weight:700;font-size:0.86rem;
                            background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.14);
                            border-radius:10px;padding:0.65rem;">
                    <i data-lucide="check-circle" size="16"></i> Booking confirmed!
                </div>
                <div id="eticket-display"></div>
                <button onclick="closeModal()" style="width:100%;justify-content:center;">
                    Done <i data-lucide="check" size="14"></i>
                </button>
            </div>

        </div><!-- /bm-body -->
    </div><!-- /bm-inner -->
</div>

<!-- ══════════════ TICKET VIEW MODAL ════════════════════ -->
<div id="ticket-view-modal" class="modal-overlay" style="z-index:2500;">
    <div class="glass-card" style="width:100%;max-width:480px;position:relative;
         max-height:90vh;overflow-y:auto;padding:1.75rem;">
        <button onclick="closeTicketModal()"
                style="position:absolute;top:14px;right:14px;background:transparent;
                       padding:5px;border:1px solid var(--glass-border);border-radius:7px;">
            <i data-lucide="x" size="15"></i>
        </button>
        <h3 style="font-weight:800;margin-bottom:1.2rem;font-size:1rem;">Your E-Ticket</h3>
        <div id="ticket-view-content"></div>
    </div>
</div>

<!-- ══════════════ CHAT FAB ═════════════════════════════ -->
<button class="chat-fab" onclick="toggleChat()" title="Ask anything">
    <i data-lucide="bot" color="white" size="24"></i>
</button>

<!-- ══════════════ CHAT WINDOW ══════════════════════════ -->
<div id="chat-window" class="glass-card">
    <div style="padding:1.1rem 1.35rem;border-bottom:1px solid var(--glass-border);
                display:flex;align-items:center;gap:9px;flex-shrink:0;">
        <span style="width:8px;height:8px;background:var(--success);border-radius:50%;
                     box-shadow:0 0 6px var(--success);"></span>
        <span style="font-weight:700;font-size:0.85rem;">QuickRail Assistant</span>
        <button onclick="toggleChat()"
                style="margin-left:auto;background:transparent;padding:4px;
                       border:1px solid var(--glass-border);border-radius:6px;">
            <i data-lucide="x" size="13"></i>
        </button>
    </div>
    <div id="chat-msgs"
         style="flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;"></div>
    <div style="padding:0.85rem 1rem;display:flex;gap:8px;
                background:rgba(0,0,0,0.2);flex-shrink:0;
                border-top:1px solid var(--glass-border);">
        <input type="text" id="chat-in" placeholder="Ask about trains, fares, bookings…" style="flex:1;">
        <button onclick="sendChat()" style="padding:0.6rem 0.8rem;">
            <i data-lucide="send" size="14"></i>
        </button>
    </div>
</div>

<script src="{{ url_for('static', filename='script.js') }}"></script>
<script src="{{ url_for('static', filename='chatbot.js') }}"></script>
<script>
    lucide.createIcons();

    /* ── Class hint text ──────────────────────────── */
    const classHints = {
        SL: "Sleeper — basic berths, no AC. Best value for overnight journeys.",
        "3A": "AC 3-Tier — air-conditioned berths, side and main. Good comfort for long trips.",
        "2A": "AC 2-Tier — wider berths, privacy curtains, best AC comfort.",
        CC:  "Chair Car — reclining seats, no berths. Available on Vande Bharat & Tejas only.",
        EC:  "Executive Chair — premium wide seats with extra legroom. Vande Bharat & Tejas only.",
    };

    document.getElementById("seatClass").addEventListener("change", function () {
        const hint = document.getElementById("class-hint");
        hint.style.display = "block";
        hint.textContent   = classHints[this.value] || "";
    });

    /* ── Nav switching ────────────────────────────── */
    function showSearch() {
        document.getElementById("search-panel").style.display = "";
        document.getElementById("page-title").innerText = "Find a Train";
        document.getElementById("page-sub").innerText   = "Search by route, day, and seat class. Booking takes under a minute.";
        document.getElementById("nav-search").classList.add("active");
        document.getElementById("nav-journeys").classList.remove("active");
        document.getElementById("results").innerHTML =
            '<div style="text-align:center;padding:4rem 0;opacity:0.28;">' +
            '<i data-lucide="train-front" size="40" style="margin-bottom:0.9rem;"></i>' +
            '<p style="font-size:0.87rem;">Pick your route and class above, then click Search.</p></div>';
        lucide.createIcons();
    }

    function activateJourneys() {
        document.getElementById("search-panel").style.display = "none";
        document.getElementById("page-title").innerText = "My Journeys";
        document.getElementById("page-sub").innerText   = "View, download, or cancel your bookings.";
        document.getElementById("nav-journeys").classList.add("active");
        document.getElementById("nav-search").classList.remove("active");
        showJourneys();
    }
</script>
</body>
</html>