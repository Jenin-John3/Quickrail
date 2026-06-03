/* ── State ───────────────────────────────────────────────── */
let searchResults = [];
let selectedTrain = null;
let selectedSeat  = null;
let currentStep   = 1;

/* ═══════════════════════════════════════════════════════════
   SEARCH
══════════════════════════════════════════════════════════════ */
async function findTrains() {
    const from   = document.getElementById("fromStat").value;
    const to     = document.getElementById("toStat").value;
    const day    = document.getElementById("day").value;
    const resDiv = document.getElementById("results");

    if (from === to) {
        showToast("Origin and destination must differ.", "danger");
        return;
    }

    resDiv.innerHTML = `
        <div style="text-align:center; padding:5rem 0;">
            <div class="spinner"></div>
            <p style="margin-top:2rem; color:var(--text-dim); font-size:0.8rem;
               letter-spacing:2px; font-weight:600;">SEARCHING...</p>
        </div>`;

    try {
        const res  = await fetch("/search", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ from, to, day })
        });
        const data = await res.json();

        searchResults = data.map(t => ({ ...t, from, to, day }));
        resDiv.innerHTML = "";

        if (searchResults.length === 0) {
            resDiv.innerHTML = `
                <div class="glass-card" style="text-align:center; padding:4rem;
                     color:var(--text-dim); border-style:dashed;">
                    <i data-lucide="alert-octagon" size="40"
                       style="margin-bottom:1.5rem; opacity:0.5;"></i>
                    <p style="font-weight:600;">No trains found for this route on ${day}.</p>
                </div>`;
            lucide.createIcons();
            return;
        }

        searchResults.forEach((t, i) => {
            const card = document.createElement("div");
            card.className = "ticket-row animate-in";
            card.style.animationDelay = `${i * 0.07}s`;
            card.innerHTML = `
                <div>
                    <div style="font-weight:800;font-size:1.05rem;
                         letter-spacing:-0.4px;margin-bottom:4px;">${t.name}</div>
                    <div style="color:var(--text-muted);font-size:0.72rem;
                         display:flex;align-items:center;gap:5px;font-weight:600;">
                        <i data-lucide="hash" size="11"></i>${t.id}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:1rem;">${t.dep}</div>
                    <div class="col-label">Departure</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;color:var(--accent);font-size:1rem;">${t.duration}</div>
                    <div class="col-label">Duration</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:800;color:var(--success);font-size:1.05rem;">&#8377;${t.fare}</div>
                    <div class="col-label">Fare</div>
                </div>
                <div style="text-align:right;">
                    <button class="book-btn" onclick="openBookingModal(${i})">
                        Book <i data-lucide="chevron-right" size="15"></i>
                    </button>
                </div>`;
            resDiv.appendChild(card);
        });

        lucide.createIcons();

    } catch (err) {
        showToast("Could not reach the server. Is Flask running?", "danger");
    }
}

/* ═══════════════════════════════════════════════════════════
   BOOKING MODAL
══════════════════════════════════════════════════════════════ */
function openBookingModal(idx) {
    selectedTrain = searchResults[idx];
    selectedSeat  = null;
    currentStep   = 1;

    document.getElementById("modal-train-name").innerText = selectedTrain.name;
    document.getElementById("modal-route").innerText =
        selectedTrain.from + "  \u2192  " + selectedTrain.to + "  \u00B7  " + selectedTrain.day;
    document.getElementById("fare-display").innerText = "\u20B90";

    ["p-name","p-phone","p-dob"].forEach(id =>
        document.getElementById(id).value = "");

    const payBtn = document.getElementById("pay-btn");
    payBtn.disabled  = false;
    payBtn.innerHTML = "Pay \u20B9" + selectedTrain.fare +
        " <i data-lucide=\"credit-card\" size=\"15\"></i>";

    buildSeatGrid();
    gotoStep(1);
    document.getElementById("booking-modal").style.display = "flex";
    lucide.createIcons();
}

function buildSeatGrid() {
    const grid = document.getElementById("seat-grid");
    grid.innerHTML = "";
    for (let i = 1; i <= 24; i++) {
        const isTaken = Math.random() > 0.72;
        const seat    = document.createElement("div");
        seat.className = "seat " + (isTaken ? "taken" : "available");
        seat.innerHTML =
            "<span style=\"font-size:0.52rem;opacity:0.4;display:block;margin-bottom:1px;\">S</span>" + i;
        if (!isTaken) {
            seat.onclick = () => {
                document.querySelectorAll(".seat").forEach(s => s.classList.remove("selected"));
                seat.classList.add("selected");
                selectedSeat = i;
                document.getElementById("fare-display").innerText = "\u20B9" + selectedTrain.fare;
            };
        }
        grid.appendChild(seat);
    }
}

function gotoStep(n) {
    currentStep = n;
    document.querySelectorAll(".modal-step").forEach(s => s.style.display = "none");
    document.getElementById("step-" + n).style.display = "flex";

    const indWrap = document.getElementById("ind-wrap");
    if (indWrap) indWrap.style.display = n === 4 ? "none" : "block";

    document.querySelectorAll(".step-dot").forEach((dot, i) => {
        dot.classList.toggle("done",   i + 1 <  Math.min(n, 4));
        dot.classList.toggle("active", i + 1 === Math.min(n, 4));
    });
    lucide.createIcons();
}

function nextStep() {
    if (currentStep === 1) {
        if (!selectedSeat) { showToast("Please select a seat first.", "danger"); return; }
        gotoStep(2);

    } else if (currentStep === 2) {
        const name  = document.getElementById("p-name").value.trim();
        const phone = document.getElementById("p-phone").value.trim();
        const dob   = document.getElementById("p-dob").value;

        if (!name || !phone || !dob) {
            showToast("Please fill in all passenger details.", "danger"); return;
        }
        if (!/^\d{10}$/.test(phone)) {
            showToast("Enter a valid 10-digit phone number.", "danger"); return;
        }

        document.getElementById("ps-train").innerText = selectedTrain.name;
        document.getElementById("ps-route").innerText = selectedTrain.from + " \u2192 " + selectedTrain.to;
        document.getElementById("ps-seat").innerText  = "Seat " + selectedSeat;
        document.getElementById("ps-name").innerText  = name;
        document.getElementById("ps-fare").innerText  = "\u20B9" + selectedTrain.fare;
        gotoStep(3);
    }
}

function prevStep() {
    if (currentStep > 1 && currentStep < 4) gotoStep(currentStep - 1);
}

function processPayment() {
    const btn = document.getElementById("pay-btn");
    btn.disabled     = true;
    btn.style.opacity = "0.7";
    btn.innerHTML    = "Processing\u2026";
    setTimeout(finalizeBooking, 1600);
}

function finalizeBooking() {
    const pnr = "QR-" + Math.floor(100000 + Math.random() * 900000);
    const passenger = {
        name:  document.getElementById("p-name").value.trim(),
        phone: document.getElementById("p-phone").value.trim(),
        dob:   fmtDOB(document.getElementById("p-dob").value)
    };
    const booking = {
        pnr,
        trainName:  selectedTrain.name,
        trainId:    selectedTrain.id,
        from:       selectedTrain.from,
        to:         selectedTrain.to,
        dep:        selectedTrain.dep,
        arr:        selectedTrain.arr,
        duration:   selectedTrain.duration,
        day:        selectedTrain.day,
        seat:       selectedSeat,
        fare:       selectedTrain.fare,
        passenger,
        cancelled:  false,
        refund:     null,
        bookedDate: new Date().toLocaleDateString("en-GB"),
        bookedTime: new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" })
    };
    saveBooking(booking);
    document.getElementById("eticket-display").innerHTML = eticketHTML(booking);
    gotoStep(4);
}

function fmtDOB(val) {
    if (!val) return "\u2014";
    const [y, m, d] = val.split("-");
    return d + "/" + m + "/" + y;
}

function closeModal() {
    document.getElementById("booking-modal").style.display = "none";
    selectedTrain = null;
    selectedSeat  = null;
}
function closeTicketModal() {
    document.getElementById("ticket-view-modal").style.display = "none";
}

/* ═══════════════════════════════════════════════════════════
   E-TICKET HTML
══════════════════════════════════════════════════════════════ */
function eticketHTML(b) {
    const from  = b.from  || "\u2014";
    const to    = b.to    || "\u2014";
    const pName = (b.passenger && b.passenger.name)  || "\u2014";
    const pPh   = (b.passenger && b.passenger.phone) || "\u2014";
    const pDob  = (b.passenger && b.passenger.dob)   || "\u2014";

    return [
        '<div style="border-radius:14px;overflow:hidden;border:1px solid var(--glass-border);">',

        /* Header */
        '<div style="background:linear-gradient(135deg,#6366f1 0%,#4f46e5 100%);',
        'padding:1.1rem 1.4rem;display:flex;justify-content:space-between;align-items:center;">',
        '<div>',
        '<div style="font-weight:800;font-size:1rem;letter-spacing:-0.3px;">\uD83D\uDE86 QuickRail</div>',
        '<div style="font-size:0.63rem;opacity:0.75;margin-top:2px;letter-spacing:1px;text-transform:uppercase;">',
        'E-Ticket \u00B7 Confirmed</div></div>',
        '<div style="text-align:right;">',
        '<div style="font-size:0.6rem;opacity:0.7;text-transform:uppercase;letter-spacing:1px;">PNR</div>',
        '<div style="font-weight:800;font-size:0.95rem;letter-spacing:1.5px;">' + b.pnr + '</div>',
        '</div></div>',

        /* Journey */
        '<div style="padding:1.15rem 1.4rem;background:rgba(255,255,255,0.025);">',
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">',

        '<div>',
        '<div style="font-size:1.2rem;font-weight:800;">' + from + '</div>',
        '<div style="color:var(--accent);font-weight:700;font-size:0.88rem;">' + b.dep + '</div>',
        '<div style="color:var(--text-muted);font-size:0.63rem;margin-top:1px;">Departure</div>',
        '</div>',

        '<div style="flex:1;text-align:center;">',
        '<div style="font-size:0.65rem;font-weight:600;color:var(--text-muted);">' + (b.duration||"") + '</div>',
        '<div style="display:flex;align-items:center;gap:4px;margin:5px 0;">',
        '<div style="flex:1;height:1px;background:var(--glass-border);"></div>',
        '<span style="color:var(--accent);font-size:1rem;">\u203A</span>',
        '<div style="flex:1;height:1px;background:var(--glass-border);"></div>',
        '</div>',
        '<div style="font-size:0.62rem;color:var(--text-muted);">' + (b.day||"") + '</div>',
        '</div>',

        '<div style="text-align:right;">',
        '<div style="font-size:1.2rem;font-weight:800;">' + to + '</div>',
        '<div style="color:var(--accent);font-weight:700;font-size:0.88rem;">' + b.arr + '</div>',
        '<div style="color:var(--text-muted);font-size:0.63rem;margin-top:1px;">Arrival</div>',
        '</div></div>',

        '<div style="margin-top:1rem;padding-top:0.9rem;border-top:1px solid var(--glass-border);',
        'display:flex;justify-content:space-between;align-items:center;">',
        '<div>',
        '<div style="font-weight:700;font-size:0.85rem;">' + b.trainName + '</div>',
        '<div style="color:var(--text-muted);font-size:0.67rem;">#' + b.trainId + '</div>',
        '</div>',
        '<div style="text-align:right;">',
        '<div style="font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">Seat</div>',
        '<div style="font-weight:800;font-size:1.15rem;color:var(--success);">S' + b.seat + '</div>',
        '</div></div></div>',

        /* Tear line */
        '<div style="display:flex;align-items:center;padding:0 1.4rem;margin:0 -1px;">',
        '<div style="width:16px;height:16px;border-radius:50%;background:var(--bg);',
        'border:1px solid var(--glass-border);margin-left:-24px;flex-shrink:0;"></div>',
        '<div style="flex:1;border-top:2px dashed rgba(255,255,255,0.08);"></div>',
        '<div style="width:16px;height:16px;border-radius:50%;background:var(--bg);',
        'border:1px solid var(--glass-border);margin-right:-24px;flex-shrink:0;"></div>',
        '</div>',

        /* Passenger */
        '<div style="padding:1rem 1.4rem;background:rgba(0,0,0,0.18);',
        'display:grid;grid-template-columns:1fr 1fr;gap:0.8rem 1rem;">',
        pField("Passenger", pName),
        pField("Phone",     pPh),
        pField("D.O.B",    pDob),
        pField("Fare Paid", "<span style='color:var(--success);'>&#8377;" + b.fare + "</span>"),
        '</div>',

        /* Barcode */
        '<div style="padding:1rem 1.4rem;text-align:center;background:rgba(255,255,255,0.01);">',
        '<div style="display:flex;gap:2px;justify-content:center;align-items:flex-end;',
        'height:38px;margin-bottom:6px;overflow:hidden;">',
        barcode(),
        '</div>',
        '<div style="font-size:0.6rem;color:var(--text-muted);letter-spacing:2.5px;font-weight:600;">' + b.pnr + '</div>',
        '</div></div>'
    ].join("");
}

function pField(label, val) {
    return "<div>" +
        "<div style=\"font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;" +
        "letter-spacing:1px;margin-bottom:3px;\">" + label + "</div>" +
        "<div style=\"font-weight:700;font-size:0.85rem;\">" + val + "</div>" +
        "</div>";
}

function barcode() {
    var b = "";
    for (var i = 0; i < 50; i++) {
        var w = Math.random() > 0.52 ? 3 : 1.5;
        var h = 22 + Math.random() * 16;
        b += "<div style=\"width:" + w + "px;height:" + h + "px;" +
             "background:var(--text-muted);border-radius:1px;flex-shrink:0;\"></div>";
    }
    return b;
}

/* ═══════════════════════════════════════════════════════════
   STORAGE
══════════════════════════════════════════════════════════════ */
function loadHistory() {
    try { return JSON.parse(localStorage.getItem("qr_logs") || "[]"); } catch(e) { return []; }
}
function saveHistory(h) {
    try { localStorage.setItem("qr_logs", JSON.stringify(h)); } catch(e) {}
}
function saveBooking(b) {
    var h = loadHistory(); h.unshift(b); saveHistory(h);
}

/* ═══════════════════════════════════════════════════════════
   MY JOURNEYS
══════════════════════════════════════════════════════════════ */
function showJourneys() {
    const resDiv  = document.getElementById("results");
    const history = loadHistory();

    if (history.length === 0) {
        resDiv.innerHTML = `
            <div class="glass-card" style="text-align:center;padding:4rem;
                 color:var(--text-dim);border-style:dashed;">
                <i data-lucide="ticket" size="40" style="margin-bottom:1.5rem;opacity:0.4;"></i>
                <p style="font-weight:600;">No bookings yet.</p>
                <p style="font-size:0.83rem;margin-top:0.5rem;color:var(--text-muted);">
                    Search for trains and make your first booking.
                </p>
            </div>`;
        lucide.createIcons();
        return;
    }

    resDiv.innerHTML =
        `<div style="font-size:0.73rem;color:var(--text-muted);font-weight:700;` +
        `text-transform:uppercase;letter-spacing:1.5px;margin-bottom:1.25rem;">` +
        `My Journeys &nbsp;&middot;&nbsp; ${history.length} booking${history.length > 1 ? "s" : ""}` +
        `</div>`;

    history.forEach((b, i) => {
        const card = document.createElement("div");
        card.className = "ticket-row animate-in";
        card.style.animationDelay = i * 0.06 + "s";
        if (b.cancelled) card.style.opacity = "0.55";

        const from = b.from || "\u2014";
        const to   = b.to   || "\u2014";
        const date = b.bookedDate || b.date || "\u2014";

        let rightCol;
        if (b.cancelled) {
            rightCol =
                `<div style="text-align:right;">` +
                `<div class="badge badge-red">Cancelled</div>` +
                `<div style="font-size:0.7rem;color:var(--text-muted);margin-top:5px;">` +
                `&#8377;${b.refund} refunded</div></div>`;
        } else {
            rightCol =
                `<div style="text-align:right;display:flex;flex-direction:column;` +
                `gap:7px;align-items:flex-end;">` +
                `<div class="badge badge-green">${b.pnr}</div>` +
                `<div style="display:flex;gap:6px;">` +
                `<button class="btn-sm btn-primary" onclick="viewTicket('${b.pnr}')">` +
                `<i data-lucide="ticket" size="12"></i> Ticket</button>` +
                `<button class="btn-sm btn-red" onclick="cancelBooking('${b.pnr}')">` +
                `<i data-lucide="x-circle" size="12"></i> Cancel</button>` +
                `</div></div>`;
        }

        card.innerHTML =
            `<div>` +
            `<div style="font-weight:800;font-size:1rem;margin-bottom:3px;">${b.trainName}</div>` +
            `<div style="color:var(--text-muted);font-size:0.73rem;font-weight:600;">` +
            `${from} &rarr; ${to} &nbsp;&middot;&nbsp; Seat ${b.seat}</div></div>` +
            `<div style="text-align:center;">` +
            `<div style="font-weight:700;">${b.dep}</div>` +
            `<div class="col-label">Dep.</div></div>` +
            `<div style="text-align:center;">` +
            `<div style="font-weight:700;">${date}</div>` +
            `<div class="col-label">Booked On</div></div>` +
            `<div style="text-align:center;">` +
            `<div style="font-weight:800;color:var(--success);">&#8377;${b.fare}</div>` +
            `<div class="col-label">Fare</div></div>` +
            rightCol;

        resDiv.appendChild(card);
    });

    lucide.createIcons();
}

function cancelBooking(pnr) {
    if (!confirm("Cancel booking " + pnr + "?\n\nYou will receive a 90% refund.")) return;
    const history = loadHistory();
    const idx     = history.findIndex(b => b.pnr === pnr);
    if (idx === -1) return;
    const refund = Math.floor(history[idx].fare * 0.9);
    history[idx].cancelled = true;
    history[idx].refund    = refund;
    saveHistory(history);
    showToast("Cancelled \u00B7 \u20B9" + refund + " refund in 24 hrs", "success");
    showJourneys();
}

function viewTicket(pnr) {
    const booking = loadHistory().find(b => b.pnr === pnr);
    if (!booking) return;
    document.getElementById("ticket-view-content").innerHTML = eticketHTML(booking);
    document.getElementById("ticket-view-modal").style.display = "flex";
    lucide.createIcons();
}

/* ═══════════════════════════════════════════════════════════
   TOAST
══════════════════════════════════════════════════════════════ */
function showToast(msg, type) {
    const t = document.createElement("div");
    t.style.cssText =
        "position:fixed;top:36px;right:36px;padding:0.9rem 1.6rem;" +
        "background:" + (type === "success" ? "rgba(16,185,129,0.93)" : "rgba(239,68,68,0.93)") + ";" +
        "color:#fff;border-radius:14px;font-weight:700;z-index:9999;" +
        "font-size:0.87rem;box-shadow:0 16px 36px rgba(0,0,0,0.4);" +
        "animation:toastIn 0.4s cubic-bezier(0.16,1,0.3,1) forwards;" +
        "font-family:inherit;max-width:340px;line-height:1.4;";
    t.innerText = msg;
    document.body.appendChild(t);
    setTimeout(() => {
        t.style.transition = "opacity .35s,transform .35s";
        t.style.opacity    = "0";
        t.style.transform  = "translateX(60px)";
        setTimeout(() => t.remove(), 380);
    }, 4500);
}

/* Utility styles */
const _u = document.createElement("style");
_u.innerHTML = `
    @keyframes toastIn {
        from { opacity:0; transform:translateX(80px); }
        to   { opacity:1; transform:translateX(0); }
    }
    .col-label {
        font-size:0.58rem; color:var(--text-muted); letter-spacing:1px;
        font-weight:700; text-transform:uppercase; margin-top:2px;
    }
    .badge {
        display:inline-block; font-size:0.68rem; font-weight:700;
        padding:4px 10px; border-radius:20px; letter-spacing:0.5px;
    }
    .badge-green { background:rgba(16,185,129,0.1); color:var(--success); border:1px solid rgba(16,185,129,0.2); }
    .badge-red   { background:rgba(239,68,68,0.1);  color:var(--danger);  border:1px solid rgba(239,68,68,0.2); }
    .btn-sm {
        padding:5px 10px; font-size:0.72rem; border-radius:8px;
        display:inline-flex; align-items:center; gap:4px; font-weight:700;
        cursor:pointer; transition:.2s; border:none;
    }
    .btn-sm:hover { filter:brightness(1.15); transform:translateY(-1px); }
    .btn-primary { background:rgba(99,102,241,0.12); color:var(--primary); border:1px solid rgba(99,102,241,0.25) !important; }
    .btn-red     { background:rgba(239,68,68,0.1);   color:var(--danger);  border:1px solid rgba(239,68,68,0.22) !important; }
    .book-btn {
        padding:0.6rem 1.1rem; font-size:0.85rem; border-radius:10px;
        display:inline-flex; align-items:center; gap:5px;
    }
    .step-dot {
        width:8px; height:8px; border-radius:50%;
        background:var(--glass-border);
        transition:background .3s, transform .3s, box-shadow .3s;
        flex-shrink:0;
    }
    .step-dot.active {
        background:var(--primary); transform:scale(1.25);
        box-shadow:0 0 8px var(--primary-glow);
    }
    .step-dot.done { background:var(--success); }
    .modal-step { display:none; flex-direction:column; gap:1rem; }
`;
document.head.appendChild(_u);