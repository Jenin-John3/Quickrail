/* ══════════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════════ */
let searchResults = [];
let selectedTrain  = null;   // current search result being booked
let selectedSeats  = null;   // array of {seat, segStart, segEnd} — 1 or 2 entries
let currentStep    = 1;

/* ══════════════════════════════════════════════════════════
   CLASS HELPERS
══════════════════════════════════════════════════════════ */
const CLASS_META = {
    SL:  { label: "Sleeper",     css: "class-pill class-pill-SL" },
    "3A":{ label: "AC 3-Tier",   css: "class-pill class-pill-3A" },
    "2A":{ label: "AC 2-Tier",   css: "class-pill class-pill-2A" },
    CC:  { label: "Chair Car",   css: "class-pill class-pill-CC" },
    EC:  { label: "Exec. Chair", css: "class-pill class-pill-EC" },
};

function classPill(code) {
    const m = CLASS_META[code] || { label: code, css: "class-pill class-pill-SL" };
    return `<span class="${m.css}">${m.label}</span>`;
}

/* ══════════════════════════════════════════════════════════
   SEARCH
══════════════════════════════════════════════════════════ */
async function findTrains() {
    const from      = document.getElementById("fromStat").value;
    const to        = document.getElementById("toStat").value;
    const day       = document.getElementById("day").value;
    const seatClass = document.getElementById("seatClass").value;
    const resDiv    = document.getElementById("results");

    if (from === to) { showToast("Origin and destination must be different.", "danger"); return; }

    resDiv.innerHTML = `
        <div style="text-align:center;padding:5rem 0;">
            <div class="spinner"></div>
            <p style="margin-top:1.6rem;color:var(--text-dim);font-size:.77rem;
               letter-spacing:2px;font-weight:600;">SEARCHING&hellip;</p>
        </div>`;

    try {
        const res  = await fetch("/search", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ from, to, day, seat_class: seatClass })
        });
        const data = await res.json();

        searchResults = data.map(t => ({ ...t, from, to, day }));
        resDiv.innerHTML = "";

        if (!searchResults.length) {
            resDiv.innerHTML = `
                <div class="glass-card" style="text-align:center;padding:3.5rem;
                     color:var(--text-dim);border-style:dashed;">
                    <i data-lucide="alert-octagon" size="34"
                       style="margin-bottom:1.1rem;opacity:.42;color:var(--text-muted);"></i>
                    <p style="font-weight:700;margin-bottom:.4rem;color:var(--text-main);">No trains found</p>
                    <p style="font-size:.81rem;">
                        No trains between ${from} and ${to} on ${day},
                        or none offer ${CLASS_META[seatClass]?.label || seatClass}.
                        Try a different day or class.
                    </p>
                </div>`;
            lucide.createIcons();
            return;
        }

        resDiv.innerHTML =
            `<div style="font-size:.7rem;color:var(--text-muted);font-weight:700;` +
            `text-transform:uppercase;letter-spacing:1.5px;margin-bottom:1rem;">` +
            `${searchResults.length} train${searchResults.length > 1 ? "s" : ""} &nbsp;&middot;&nbsp; ` +
            `${from} &rarr; ${to} &nbsp;&middot;&nbsp; ${day}</div>`;

        searchResults.forEach((t, i) => {
            const card = document.createElement("div");
            card.className = "ticket-row animate-in";
            card.style.animationDelay = i * 0.07 + "s";
            card.innerHTML =
                `<div>
                    <div style="font-weight:800;font-size:.98rem;color:var(--text-main);
                         letter-spacing:-.3px;margin-bottom:5px;">${t.name}</div>
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                        <span style="color:var(--text-muted);font-size:.68rem;
                              display:flex;align-items:center;gap:4px;font-weight:600;">
                            <i data-lucide="hash" size="10"></i>${t.id}
                        </span>
                        ${classPill(t.seat_class)}
                        ${t.is_premium ? `<span style="font-size:.6rem;font-weight:700;color:#b45309;
                            background:var(--warning-soft);padding:2px 7px;border-radius:10px;
                            border:1px solid #fde68a;">Premium</span>` : ""}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:.93rem;color:var(--text-main);">${t.dep}</div>
                    <div class="col-label">Departure</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;color:var(--primary);font-size:.93rem;">${t.duration}</div>
                    <div class="col-label">Duration</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:800;color:var(--success);font-size:.97rem;">&#8377;${t.fare}</div>
                    <div class="col-label">Fare</div>
                </div>
                <div style="text-align:right;">
                    <button class="book-btn" onclick="openBookingModal(${i})">
                        Book <i data-lucide="chevron-right" size="13"></i>
                    </button>
                </div>`;
            resDiv.appendChild(card);
        });

        lucide.createIcons();

    } catch (err) {
        showToast("Could not reach the server.", "danger");
    }
}

/* ══════════════════════════════════════════════════════════
   BOOKING MODAL — OPEN
══════════════════════════════════════════════════════════ */
function openBookingModal(idx) {
    selectedTrain = searchResults[idx];
    selectedSeats = null;
    currentStep   = 1;

    document.getElementById("modal-train-name").innerText =
        selectedTrain.name + "  #" + selectedTrain.id;
    document.getElementById("modal-route").innerText =
        selectedTrain.from + "  \u2192  " + selectedTrain.to +
        "  \u00B7  " + selectedTrain.day;
    document.getElementById("modal-class-pill").innerHTML =
        classPill(selectedTrain.seat_class);
    document.getElementById("fare-display").innerText = "\u20B90";

    ["p-name","p-phone","p-dob"].forEach(id =>
        document.getElementById(id).value = "");

    resetConfirmBtn();

    buildSeatGrid();       /* async — loads real segment-aware seats */
    gotoStep(1);
    document.getElementById("booking-modal").style.display = "flex";
    lucide.createIcons();
}

/* ══════════════════════════════════════════════════════════
   SEGMENT-AWARE SEAT GRID
   Statuses returned by /seats/<train_id>/<day>:
     available — free for the whole requested range
     partial   — booked for a different segment, free for this one
     taken     — conflicts with the requested range
══════════════════════════════════════════════════════════ */
async function buildSeatGrid() {
    const grid = document.getElementById("seat-grid");
    grid.innerHTML =
        `<div style="grid-column:1/-1;text-align:center;padding:1.75rem 0;
             color:var(--text-muted);font-size:.8rem;">
             <div class="spinner" style="width:26px;height:26px;border-width:2px;margin:0 auto .75rem;"></div>
             Loading seats&hellip;
         </div>`;

    try {
        const url = `/seats/${selectedTrain.id}/${encodeURIComponent(selectedTrain.day)}` +
            `?class=${selectedTrain.seat_class}&idx_from=${selectedTrain.idx_from}&idx_to=${selectedTrain.idx_to}`;
        const res  = await fetch(url);
        const data = await res.json();
        const statuses    = data.statuses    || {};
        const totalSeats  = data.totalSeats  || 24;
        const routeLabels = data.routeLabels || [];

        grid.innerHTML = "";
        for (let i = 1; i <= totalSeats; i++) {
            const info   = statuses[i] || statuses[String(i)] || { status: "available", bookedSegments: [] };
            const status = info.status;
            const seat   = document.createElement("div");
            seat.className = "seat " + status;
            seat.innerHTML =
                `<span style="font-size:.49rem;opacity:.5;display:block;margin-bottom:1px;">S</span>${i}`;

            if (status !== "taken") {
                if (info.bookedSegments && info.bookedSegments.length) {
                    const segLabels = info.bookedSegments.map(([s, e]) =>
                        (routeLabels[s] || "?") + "\u2192" + (routeLabels[e] || "?")
                    ).join(", ");
                    seat.title = "Also booked for: " + segLabels;
                }
                seat.onclick = () => {
                    document.querySelectorAll(".seat").forEach(s => s.classList.remove("selected"));
                    seat.classList.add("selected");
                    selectedSeats = [{
                        seat: i,
                        segStart: selectedTrain.idx_from,
                        segEnd:   selectedTrain.idx_to,
                    }];
                    document.getElementById("fare-display").innerText =
                        "\u20B9" + selectedTrain.fare;
                };
            } else if (info.bookedSegments && info.bookedSegments.length) {
                const segLabels = info.bookedSegments.map(([s, e]) =>
                    (routeLabels[s] || "?") + "\u2192" + (routeLabels[e] || "?")
                ).join(", ");
                seat.title = "Booked for: " + segLabels;
            }
            grid.appendChild(seat);
        }
    } catch {
        grid.innerHTML =
            `<div style="grid-column:1/-1;text-align:center;padding:1.5rem;
                 color:var(--danger);font-size:.8rem;">
                 Could not load seats. Please close and try again.
             </div>`;
    }
}

/* ══════════════════════════════════════════════════════════
   STEP CONTROL
══════════════════════════════════════════════════════════ */
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
        if (!selectedSeats) { showToast("Please select a seat to continue.", "danger"); return; }
        gotoStep(2);

    } else if (currentStep === 2) {
        const name  = document.getElementById("p-name").value.trim();
        const phone = document.getElementById("p-phone").value.trim();
        const dob   = document.getElementById("p-dob").value;

        if (!name || !phone || !dob) { showToast("Please fill in all three fields.", "danger"); return; }
        if (!/^\d{10}$/.test(phone)) { showToast("Phone number must be exactly 10 digits.", "danger"); return; }

        document.getElementById("ps-train").innerText  = selectedTrain.name;
        document.getElementById("ps-route").innerText  =
            selectedTrain.from + " \u2192 " + selectedTrain.to;
        document.getElementById("ps-class").innerHTML  = classPill(selectedTrain.seat_class);
        document.getElementById("ps-seat").innerText   =
            "Seat " + selectedSeats.map(s => s.seat).join(", ");
        document.getElementById("ps-name").innerText   = name;
        document.getElementById("ps-fare").innerText   = "\u20B9" + selectedTrain.fare;

        resetConfirmBtn();
        gotoStep(3);
    }
}

function prevStep() {
    if (currentStep > 1 && currentStep < 4) gotoStep(currentStep - 1);
}

/* ══════════════════════════════════════════════════════════
   CONFIRM BOOKING — no payment step
══════════════════════════════════════════════════════════ */
async function processBooking() {
    const btn = document.getElementById("confirm-btn");
    btn.disabled = true; btn.style.opacity = ".65";
    btn.innerHTML = "Confirming\u2026";

    const passenger = {
        name:  document.getElementById("p-name").value.trim(),
        phone: document.getElementById("p-phone").value.trim(),
        dob:   fmtDOB(document.getElementById("p-dob").value),
    };

    const bookingPayload = {
        trainId:    selectedTrain.id,
        trainName:  selectedTrain.name,
        from:       selectedTrain.from,
        to:         selectedTrain.to,
        day:        selectedTrain.day,
        dep:        selectedTrain.dep,
        arr:        selectedTrain.arr,
        duration:   selectedTrain.duration,
        seatClass:  selectedTrain.seat_class,
        classLabel: selectedTrain.class_label,
        fare:       selectedTrain.fare,
        idxFrom:    selectedTrain.idx_from,
        idxTo:      selectedTrain.idx_to,
        passenger,
    };

    try {
        const res    = await fetch("/confirm-booking", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ booking_data: bookingPayload }),
        });
        const result = await res.json();

        if (!result.success) {
            showToast(result.error || "Booking failed. Please try again.", "danger");
            resetConfirmBtn();
            return;
        }

        if (result.waitlisted) {
            document.getElementById("confirm-banner").outerHTML =
                `<div id="confirm-banner" style="display:flex;align-items:center;justify-content:center;gap:6px;
                     color:#b45309;font-weight:700;font-size:.84rem;
                     background:var(--warning-soft);border:1px solid #fde68a;
                     border-radius:10px;padding:.62rem;">
                     <i data-lucide="clock" size="15"></i> Added to waitlist
                 </div>`;
            document.getElementById("split-note-display").innerHTML = "";
            document.getElementById("eticket-display").innerHTML = `
                <div style="border:1px solid var(--border);border-radius:13px;padding:1.1rem 1.3rem;
                            background:var(--surface-soft);font-size:.85rem;color:var(--text-dim);line-height:1.7;">
                    <div style="font-weight:700;color:var(--text-main);margin-bottom:6px;">PNR: ${result.pnr}</div>
                    ${result.message}<br>
                    Waitlist expires by <strong style="color:var(--text-main);">${result.waitUntil}</strong> if no seat opens up.
                    Check <strong style="color:var(--text-main);">My Journeys</strong> for updates.
                </div>`;
        } else {
            document.getElementById("confirm-banner").outerHTML =
                `<div id="confirm-banner" style="display:flex;align-items:center;justify-content:center;gap:6px;
                     color:#047857;font-weight:700;font-size:.84rem;
                     background:var(--success-soft);border:1px solid #a7f3d0;
                     border-radius:10px;padding:.62rem;">
                     <i data-lucide="check-circle" size="15"></i> Booking confirmed!
                 </div>`;
            document.getElementById("split-note-display").innerHTML = result.isSplit
                ? `<div class="split-stripe">
                       <i data-lucide="shuffle" size="14" style="flex-shrink:0;margin-top:1px;"></i>
                       <span>${result.splitNote || "Your seat changes once during this journey."}</span>
                   </div>`
                : "";
            document.getElementById("eticket-display").innerHTML = eticketHTML(result.booking);
        }

        gotoStep(4);
        lucide.createIcons();

    } catch {
        showToast("Could not confirm booking. Check your connection.", "danger");
        resetConfirmBtn();
    }
}

function resetConfirmBtn() {
    const btn = document.getElementById("confirm-btn");
    if (!btn) return;
    btn.disabled = false; btn.style.opacity = "1";
    btn.innerHTML = "Confirm Booking <i data-lucide=\"check\" size=\"13\"></i>";
    lucide.createIcons();
}

function closeModal() {
    document.getElementById("booking-modal").style.display = "none";
    selectedTrain = null; selectedSeats = null;
}
function closeTicketModal() {
    document.getElementById("ticket-view-modal").style.display = "none";
}

/* ══════════════════════════════════════════════════════════
   E-TICKET HTML
══════════════════════════════════════════════════════════ */
const ACCENT_MAP = {
    SL: "#2563eb", "3A": "#0284c7", "2A": "#059669", CC: "#d97706", EC: "#7c3aed"
};

function eticketHTML(b) {
    const from       = b.from        || "\u2014";
    const to         = b.to          || "\u2014";
    const pName      = b.passenger?.name  || "\u2014";
    const pPh        = b.passenger?.phone || "\u2014";
    const pDob       = b.passenger?.dob   || "\u2014";
    const classLabel = b.classLabel  || b.seatClass || "\u2014";
    const code       = b.seatClass   || "SL";
    const accent     = ACCENT_MAP[code] || "#2563eb";
    const seatDisp   = b.seatAssignments || "\u2014";
    const isWaitlist = b.status === "waitlisted";

    return `
    <div style="border-radius:13px;overflow:hidden;border:1px solid var(--border);font-size:.83rem;background:var(--surface);">

        <div style="background:linear-gradient(135deg,${accent} 0%,${accent}cc 100%);
                    padding:1.05rem 1.35rem;display:flex;justify-content:space-between;align-items:center;color:#fff;">
            <div>
                <div style="font-weight:800;font-size:.96rem;">\uD83D\uDE86 QuickRail</div>
                <div style="font-size:.6rem;opacity:.85;margin-top:2px;letter-spacing:.8px;text-transform:uppercase;">
                    ${classLabel} &nbsp;&middot;&nbsp; E-Ticket</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:.57rem;opacity:.8;text-transform:uppercase;letter-spacing:1px;">PNR</div>
                <div style="font-weight:800;font-size:.88rem;letter-spacing:1.5px;">${b.pnr}</div>
            </div>
        </div>

        <div style="padding:1.1rem 1.35rem;background:var(--surface-soft);">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
                <div>
                    <div style="font-size:1.15rem;font-weight:800;color:var(--text-main);">${from}</div>
                    <div style="color:${accent};font-weight:700;font-size:.86rem;">${b.dep}</div>
                    <div style="color:var(--text-muted);font-size:.6rem;margin-top:1px;">Departure</div>
                </div>
                <div style="flex:1;text-align:center;">
                    <div style="font-size:.62rem;font-weight:600;color:var(--text-muted);">${b.duration || ""}</div>
                    <div style="display:flex;align-items:center;gap:4px;margin:4px 0;">
                        <div style="flex:1;height:1px;background:var(--border);"></div>
                        <span style="color:${accent};font-size:.88rem;">&rsaquo;</span>
                        <div style="flex:1;height:1px;background:var(--border);"></div>
                    </div>
                    <div style="font-size:.58rem;color:var(--text-muted);">${b.day || ""}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.15rem;font-weight:800;color:var(--text-main);">${to}</div>
                    <div style="color:${accent};font-weight:700;font-size:.86rem;">${b.arr}</div>
                    <div style="color:var(--text-muted);font-size:.6rem;margin-top:1px;">Arrival</div>
                </div>
            </div>
            <div style="margin-top:.85rem;padding-top:.82rem;border-top:1px solid var(--border);
                        display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-weight:700;font-size:.83rem;color:var(--text-main);">${b.trainName}</div>
                    <div style="color:var(--text-muted);font-size:.63rem;">#${b.trainId}</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
                    <div style="font-weight:800;font-size:.92rem;color:${isWaitlist ? '#b45309' : 'var(--success)'};">
                        ${isWaitlist ? "Waitlisted" : seatDisp}
                    </div>
                    ${classPill(code)}
                </div>
            </div>
            ${b.isSplit ? `
            <div class="split-stripe" style="margin-top:.7rem;">
                <i data-lucide="shuffle" size="13" style="flex-shrink:0;margin-top:1px;"></i>
                <span>Seat changes mid-journey: ${seatDisp}</span>
            </div>` : ""}
        </div>

        <div style="display:flex;align-items:center;padding:0 1.35rem;margin:0 -1px;">
            <div style="width:14px;height:14px;border-radius:50%;background:var(--bg);
                        border:1px solid var(--border);margin-left:-21px;flex-shrink:0;"></div>
            <div style="flex:1;border-top:2px dashed var(--border-strong);"></div>
            <div style="width:14px;height:14px;border-radius:50%;background:var(--bg);
                        border:1px solid var(--border);margin-right:-21px;flex-shrink:0;"></div>
        </div>

        <div style="padding:.95rem 1.35rem;background:var(--surface);
                    display:grid;grid-template-columns:1fr 1fr;gap:.72rem .95rem;">
            ${pf("Passenger", pName)}
            ${pf("Phone",     pPh)}
            ${pf("D.O.B",    pDob)}
            ${pf("Fare",     "<span style='color:var(--success);'>&#8377;" + b.fare + "</span>")}
        </div>

        <div style="padding:.85rem 1.35rem;text-align:center;background:var(--surface-soft);">
            <div style="display:flex;gap:2px;justify-content:center;align-items:flex-end;
                        height:34px;margin-bottom:5px;overflow:hidden;">
                ${barcode(accent)}
            </div>
            <div style="font-size:.57rem;color:var(--text-muted);letter-spacing:2.5px;font-weight:600;">
                ${b.pnr}
            </div>
        </div>
    </div>`;
}

function pf(label, val) {
    return `<div>
        <div style="font-size:.57rem;color:var(--text-muted);text-transform:uppercase;
             letter-spacing:1px;margin-bottom:2px;">${label}</div>
        <div style="font-weight:700;font-size:.82rem;color:var(--text-main);">${val}</div>
    </div>`;
}

function barcode(accent) {
    let s = "";
    for (let i = 0; i < 52; i++) {
        const w   = Math.random() > .5 ? 3 : 1.5;
        const h   = 18 + Math.random() * 14;
        const col = Math.random() > .82 ? accent : "var(--text-muted)";
        s += `<div style="width:${w}px;height:${h}px;background:${col};
               border-radius:1px;flex-shrink:0;opacity:.75;"></div>`;
    }
    return s;
}

/* ══════════════════════════════════════════════════════════
   MY JOURNEYS  (fetched from server)
══════════════════════════════════════════════════════════ */
async function showJourneys() {
    const resDiv = document.getElementById("results");
    resDiv.innerHTML =
        `<div style="text-align:center;padding:4rem 0;">
             <div class="spinner"></div>
             <p style="margin-top:1.4rem;color:var(--text-dim);font-size:.78rem;">
                 Loading your bookings&hellip;</p>
         </div>`;

    try {
        const res     = await fetch("/bookings");
        const history = await res.json();

        if (!history.length) {
            resDiv.innerHTML = `
                <div class="glass-card" style="text-align:center;padding:3.5rem;
                     color:var(--text-dim);border-style:dashed;">
                    <i data-lucide="ticket" size="34" style="margin-bottom:1.1rem;opacity:.35;color:var(--text-muted);"></i>
                    <p style="font-weight:700;margin-bottom:.4rem;color:var(--text-main);">No bookings yet</p>
                    <p style="font-size:.81rem;color:var(--text-muted);">
                        Search for a train and complete a booking to see it here.
                    </p>
                </div>`;
            lucide.createIcons();
            return;
        }

        resDiv.innerHTML =
            `<div style="font-size:.68rem;color:var(--text-muted);font-weight:700;` +
            `text-transform:uppercase;letter-spacing:1.5px;margin-bottom:1rem;">` +
            `${history.length} booking${history.length > 1 ? "s" : ""}</div>`;

        history.forEach((b, i) => {
            const card = document.createElement("div");
            card.className = "ticket-row animate-in";
            card.style.animationDelay = i * 0.06 + "s";
            if (b.status === "cancelled") card.style.opacity = ".55";

            let rightCol;
            if (b.status === "cancelled") {
                rightCol = `<div style="text-align:right;">
                       <div class="badge badge-red" style="margin-bottom:5px;">Cancelled</div><br>
                       <div style="font-size:.68rem;color:var(--text-muted);">
                           &#8377;${b.refund} refunded
                       </div>
                   </div>`;
            } else if (b.status === "waitlisted") {
                rightCol = `<div style="text-align:right;display:flex;flex-direction:column;
                       gap:6px;align-items:flex-end;">
                       <div class="badge badge-amber">${b.pnr}</div>
                       <div style="font-size:.66rem;color:var(--text-muted);">On waitlist</div>
                       <button class="btn-sm btn-red" onclick="cancelBooking('${b.pnr}')">
                           <i data-lucide="x-circle" size="11"></i> Cancel
                       </button>
                   </div>`;
            } else {
                rightCol = `<div style="text-align:right;display:flex;flex-direction:column;
                       gap:6px;align-items:flex-end;">
                       <div class="badge badge-green">${b.pnr}</div>
                       <div style="display:flex;gap:5px;">
                           <button class="btn-sm btn-primary" onclick="viewTicket('${b.pnr}')">
                               <i data-lucide="ticket" size="11"></i> Ticket
                           </button>
                           <button class="btn-sm btn-red" onclick="cancelBooking('${b.pnr}')">
                               <i data-lucide="x-circle" size="11"></i> Cancel
                           </button>
                       </div>
                   </div>`;
            }

            const seatText = b.status === "waitlisted" ? "Waitlisted" : (b.seatAssignments || "\u2014");

            card.innerHTML =
                `<div>
                    <div style="font-weight:800;font-size:.95rem;color:var(--text-main);margin-bottom:5px;">
                        ${b.trainName}
                    </div>
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                        <span style="color:var(--text-muted);font-size:.7rem;font-weight:600;">
                            ${b.from || "\u2014"} &rarr; ${b.to || "\u2014"}
                            &nbsp;&middot;&nbsp; ${seatText}
                        </span>
                        ${classPill(b.seatClass || "SL")}
                        ${b.isSplit ? `<span style="font-size:.6rem;font-weight:700;color:var(--primary-strong);
                            background:var(--primary-soft);padding:2px 7px;border-radius:10px;
                            border:1px solid var(--primary-soft-2);">Split seat</span>` : ""}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:.9rem;color:var(--text-main);">${b.dep || "\u2014"}</div>
                    <div class="col-label">Dep.</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:.9rem;color:var(--text-main);">${b.bookedDate}</div>
                    <div class="col-label">Booked On</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:800;color:var(--success);font-size:.93rem;">
                        &#8377;${b.fare}
                    </div>
                    <div class="col-label">Fare</div>
                </div>
                ${rightCol}`;

            resDiv.appendChild(card);
        });

        lucide.createIcons();

    } catch {
        showToast("Could not load bookings.", "danger");
    }
}

/* ── Cancel ──────────────────────────────────────────────── */
async function cancelBooking(pnr) {
    if (!confirm("Cancel booking " + pnr + "?\n\nYou'll receive a 90% refund instantly.")) return;

    try {
        const res    = await fetch("/cancel-booking", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ pnr }),
        });
        const result = await res.json();

        if (result.success) {
            showToast("Cancelled \u00B7 \u20B9" + result.refund + " refunded.", "success");
            showJourneys();
        } else {
            showToast(result.error || "Could not cancel.", "danger");
        }
    } catch {
        showToast("Connection error. Try again.", "danger");
    }
}

/* ── View ticket ─────────────────────────────────────────── */
async function viewTicket(pnr) {
    try {
        const res     = await fetch("/bookings");
        const history = await res.json();
        const booking = history.find(b => b.pnr === pnr);
        if (!booking) { showToast("Booking not found.", "danger"); return; }

        document.getElementById("ticket-view-content").innerHTML = eticketHTML(booking);
        document.getElementById("ticket-view-modal").style.display = "flex";
        lucide.createIcons();
    } catch {
        showToast("Could not load ticket.", "danger");
    }
}

/* ══════════════════════════════════════════════════════════
   LIVE TRAIN TRACKING
══════════════════════════════════════════════════════════ */
async function checkLiveStatus() {
    const trainId = document.getElementById("live-train-id").value.trim();
    const resDiv  = document.getElementById("live-result");

    if (!/^\d{4,5}$/.test(trainId)) {
        showToast("Enter a valid train number.", "danger");
        return;
    }

    resDiv.innerHTML = `
        <div style="text-align:center;padding:3rem 0;">
            <div class="spinner"></div>
            <p style="margin-top:1.2rem;color:var(--text-dim);font-size:.78rem;">Checking live status&hellip;</p>
        </div>`;

    try {
        const res  = await fetch(`/live/${trainId}`);
        const data = await res.json();

        if (data.error) {
            resDiv.innerHTML = `
                <div class="glass-card" style="text-align:center;padding:2.5rem;color:var(--text-dim);">
                    <i data-lucide="alert-octagon" size="30" style="margin-bottom:.8rem;color:var(--text-muted);"></i>
                    <p style="font-weight:700;color:var(--text-main);">${data.error}</p>
                </div>`;
            lucide.createIcons();
            return;
        }

        const statusIcons = {
            in_transit:    "train-front",
            at_station:    "map-pin",
            not_departed:  "clock",
            arrived:       "check-circle",
        };
        const icon = statusIcons[data.status] || "help-circle";

        let progressBar = "";
        if (data.status === "in_transit") {
            progressBar = `
                <div style="margin-top:1rem;background:var(--border);border-radius:20px;height:8px;overflow:hidden;">
                    <div style="width:${data.progress}%;height:100%;background:var(--primary);border-radius:20px;transition:width .4s;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:.7rem;color:var(--text-muted);font-weight:600;">
                    <span>${data.from}</span><span>${data.to}</span>
                </div>`;
        }

        resDiv.innerHTML = `
            <div class="glass-card" style="padding:1.6rem;">
                <div class="live-card">
                    <div class="live-dot"></div>
                    <div style="flex:1;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                            <i data-lucide="${icon}" size="16" style="color:var(--primary);"></i>
                            <span style="font-weight:800;font-size:.98rem;color:var(--text-main);">Train ${trainId}</span>
                        </div>
                        <p style="color:var(--text-dim);font-size:.85rem;">${data.message}</p>
                    </div>
                </div>
                ${progressBar}
                <p style="margin-top:1rem;font-size:.68rem;color:var(--text-muted);">
                    Simulated position based on scheduled timings — not real GPS data.
                </p>
            </div>`;
        lucide.createIcons();

    } catch {
        resDiv.innerHTML = "";
        showToast("Could not check live status.", "danger");
    }
}

/* ══════════════════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════════════════ */
function fmtDOB(val) {
    if (!val) return "\u2014";
    const [y, m, d] = val.split("-");
    return d + "/" + m + "/" + y;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ── Toast ───────────────────────────────────────────────── */
function showToast(msg, type) {
    const t = document.createElement("div");
    t.style.cssText =
        "position:fixed;top:32px;right:32px;padding:.82rem 1.45rem;" +
        "background:" + (type === "success"
            ? "#10b981" : "#ef4444") + ";" +
        "color:#fff;border-radius:12px;font-weight:700;z-index:9999;" +
        "font-size:.84rem;box-shadow:0 13px 30px rgba(15,23,42,.22);" +
        "animation:toastIn .32s cubic-bezier(.16,1,.3,1) forwards;" +
        "font-family:inherit;max-width:310px;line-height:1.45;";
    t.innerText = msg;
    document.body.appendChild(t);
    setTimeout(() => {
        t.style.transition = "opacity .3s,transform .3s";
        t.style.opacity    = "0";
        t.style.transform  = "translateX(52px)";
        setTimeout(() => t.remove(), 320);
    }, 4500);
}

/* ── Utility styles ──────────────────────────────────────── */
const _u = document.createElement("style");
_u.innerHTML = `
    @keyframes toastIn {
        from { opacity:0; transform:translateX(72px); }
        to   { opacity:1; transform:translateX(0); }
    }
    .col-label {
        font-size:.56rem; color:var(--text-muted); letter-spacing:1px;
        font-weight:700; text-transform:uppercase; margin-top:2px;
    }
    .badge { display:inline-block; font-size:.64rem; font-weight:700;
        padding:3px 9px; border-radius:20px; letter-spacing:.4px; }
    .badge-green { background:var(--success-soft); color:#047857; border:1px solid #a7f3d0; }
    .badge-red   { background:var(--danger-soft);  color:var(--danger); border:1px solid #fecaca; }
    .badge-amber { background:var(--warning-soft); color:#b45309; border:1px solid #fde68a; }
    .btn-sm {
        padding:4px 9px; font-size:.68rem; border-radius:7px;
        display:inline-flex; align-items:center; gap:4px;
        font-weight:700; cursor:pointer; transition:.18s; border:none;
    }
    .btn-sm:hover { filter:brightness(1.06); transform:translateY(-1px); }
    .btn-primary { background:var(--primary-soft); color:var(--primary-strong); border:1px solid var(--primary-soft-2) !important; }
    .btn-red     { background:var(--danger-soft);  color:var(--danger);  border:1px solid #fecaca !important; }
    .book-btn    { padding:.52rem .95rem; font-size:.8rem; border-radius:9px; display:inline-flex; align-items:center; gap:4px; }
    .step-dot {
        width:7px; height:7px; border-radius:50%; background:var(--border-strong);
        transition:background .26s, transform .26s, box-shadow .26s; flex-shrink:0;
    }
    .step-dot.active { background:var(--primary); transform:scale(1.3); box-shadow:0 0 0 3px var(--primary-glow); }
    .step-dot.done   { background:var(--success); transform:scale(1); }
`;
document.head.appendChild(_u);