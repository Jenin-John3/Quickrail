/* ══════════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════════ */
let searchResults = [];
let selectedTrain = null;
let selectedSeat  = null;
let currentStep   = 1;

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
                       style="margin-bottom:1.1rem;opacity:.42;"></i>
                    <p style="font-weight:700;margin-bottom:.4rem;">No trains found</p>
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
                    <div style="font-weight:800;font-size:.98rem;
                         letter-spacing:-.3px;margin-bottom:5px;">${t.name}</div>
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                        <span style="color:var(--text-muted);font-size:.68rem;
                              display:flex;align-items:center;gap:4px;font-weight:600;">
                            <i data-lucide="hash" size="10"></i>${t.id}
                        </span>
                        ${classPill(t.seat_class)}
                        ${t.is_premium ? `<span style="font-size:.6rem;font-weight:700;color:#fbbf24;
                            background:rgba(251,191,36,.08);padding:2px 7px;border-radius:10px;
                            border:1px solid rgba(251,191,36,.18);">Premium</span>` : ""}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:.93rem;">${t.dep}</div>
                    <div class="col-label">Departure</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;color:var(--accent);font-size:.93rem;">${t.duration}</div>
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
    selectedSeat  = null;
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

    /* Payment mode notice in step 3 */
    document.getElementById("payment-mode-notice").innerHTML = DEMO_MODE
        ? `<div class="demo-stripe">
               <i data-lucide="alert-triangle" size="14"></i>
               Demo mode — no real payment. Click Pay to simulate.
           </div>`
        : `<div style="display:flex;align-items:center;gap:8px;
               background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.15);
               border-radius:10px;padding:.7rem .85rem;font-size:.74rem;
               color:var(--success);font-weight:600;">
               <i data-lucide="shield-check" size="14"></i>
               Secured by Razorpay — UPI, cards &amp; netbanking accepted.
           </div>`;

    /* Reset pay button */
    resetPayBtn();

    buildSeatGrid();       /* async — loads real seats */
    gotoStep(1);
    document.getElementById("booking-modal").style.display = "flex";
    lucide.createIcons();
}

/* ══════════════════════════════════════════════════════════
   REAL-TIME SEAT GRID
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
        const res  = await fetch(
            `/seats/${selectedTrain.id}/${encodeURIComponent(selectedTrain.day)}`
        );
        const data = await res.json();
        const booked = new Set(data.booked || []);

        grid.innerHTML = "";
        for (let i = 1; i <= 24; i++) {
            const isTaken = booked.has(i);
            const seat    = document.createElement("div");
            seat.className = "seat " + (isTaken ? "taken" : "available");
            seat.innerHTML =
                `<span style="font-size:.49rem;opacity:.36;display:block;margin-bottom:1px;">S</span>${i}`;
            if (!isTaken) {
                seat.onclick = () => {
                    document.querySelectorAll(".seat").forEach(s => s.classList.remove("selected"));
                    seat.classList.add("selected");
                    selectedSeat = i;
                    document.getElementById("fare-display").innerText =
                        "\u20B9" + selectedTrain.fare;
                };
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
        if (!selectedSeat) { showToast("Please select a seat to continue.", "danger"); return; }
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
        document.getElementById("ps-seat").innerText   = "Seat " + selectedSeat;
        document.getElementById("ps-name").innerText   = name;
        document.getElementById("ps-fare").innerText   = "\u20B9" + selectedTrain.fare;

        const payBtn = document.getElementById("pay-btn");
        payBtn.innerHTML =
            "Pay \u20B9" + selectedTrain.fare +
            " <i data-lucide=\"credit-card\" size=\"13\"></i>";
        lucide.createIcons();

        gotoStep(3);
    }
}

function prevStep() {
    if (currentStep > 1 && currentStep < 4) gotoStep(currentStep - 1);
}

/* ══════════════════════════════════════════════════════════
   PAYMENT
══════════════════════════════════════════════════════════ */
async function processPayment() {
    const btn = document.getElementById("pay-btn");
    btn.disabled = true; btn.style.opacity = ".65";
    btn.innerHTML = "Creating order\u2026";

    /* Gather passenger data */
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
        seat:       selectedSeat,
        seatClass:  selectedTrain.seat_class,
        classLabel: selectedTrain.class_label,
        fare:       selectedTrain.fare,
        passenger,
    };

    try {
        /* Step 1 — create Razorpay order on the server */
        const orderRes = await fetch("/create-order", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ fare: selectedTrain.fare }),
        });
        const order = await orderRes.json();

        if (!orderRes.ok) {
            showToast(order.error || "Could not create order.", "danger");
            resetPayBtn(); return;
        }

        /* Step 2a — DEMO MODE: simulate payment */
        if (order.demo_mode) {
            btn.innerHTML = "Simulating payment\u2026";
            await sleep(1500);
            await confirmPayment(
                order.order_id, "DEMO_PAY_" + Date.now(), "DEMO_SIG",
                true, bookingPayload
            );
            return;
        }

        /* Step 2b — REAL: open Razorpay checkout */
        btn.innerHTML = "Opening payment\u2026";
        const options = {
            key:       order.key,
            amount:    order.amount,
            currency:  "INR",
            order_id:  order.order_id,
            name:      "QuickRail",
            description:
                selectedTrain.name + " \u00B7 " +
                selectedTrain.from + " \u2192 " + selectedTrain.to,
            handler: async function (response) {
                const payBtn = document.getElementById("pay-btn");
                payBtn.innerHTML = "Verifying\u2026";
                await confirmPayment(
                    response.razorpay_order_id,
                    response.razorpay_payment_id,
                    response.razorpay_signature,
                    false, bookingPayload
                );
            },
            prefill: {
                name:    passenger.name,
                contact: "+91" + passenger.phone,
            },
            theme: { color: "#6366f1" },
            modal: {
                ondismiss: function () {
                    resetPayBtn();
                }
            },
        };

        const rzpInstance = new Razorpay(options);
        rzpInstance.on("payment.failed", function (resp) {
            showToast("Payment failed: " + resp.error.description, "danger");
            resetPayBtn();
        });
        rzpInstance.open();

    } catch (err) {
        showToast("Something went wrong. Please try again.", "danger");
        resetPayBtn();
    }
}

/* Called after Razorpay success (or demo simulate) */
async function confirmPayment(orderId, paymentId, signature, demoMode, bookingPayload) {
    try {
        const res  = await fetch("/verify-payment", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                razorpay_order_id:   orderId,
                razorpay_payment_id: paymentId,
                razorpay_signature:  signature,
                demo_mode:           demoMode,
                booking_data:        bookingPayload,
            }),
        });
        const result = await res.json();

        if (result.success) {
            document.getElementById("eticket-display").innerHTML =
                eticketHTML(result.booking);
            gotoStep(4);
        } else {
            showToast(result.error || "Booking failed. Please try again.", "danger");
            resetPayBtn();
        }
    } catch {
        showToast("Could not confirm booking. Check your connection.", "danger");
        resetPayBtn();
    }
}

function resetPayBtn() {
    const btn = document.getElementById("pay-btn");
    if (!btn) return;
    btn.disabled = false; btn.style.opacity = "1";
    const fare = selectedTrain ? selectedTrain.fare : 0;
    btn.innerHTML =
        "Pay \u20B9" + fare +
        " <i data-lucide=\"credit-card\" size=\"13\"></i>";
    lucide.createIcons();
}

function closeModal() {
    document.getElementById("booking-modal").style.display = "none";
    selectedTrain = null; selectedSeat = null;
}
function closeTicketModal() {
    document.getElementById("ticket-view-modal").style.display = "none";
}

/* ══════════════════════════════════════════════════════════
   E-TICKET HTML
══════════════════════════════════════════════════════════ */
const ACCENT_MAP = {
    SL: "#6366f1", "3A": "#22d3ee", "2A": "#10b981", CC: "#fbbf24", EC: "#ef4444"
};

function eticketHTML(b) {
    const from       = b.from        || "\u2014";
    const to         = b.to          || "\u2014";
    const pName      = b.passenger?.name  || "\u2014";
    const pPh        = b.passenger?.phone || "\u2014";
    const pDob       = b.passenger?.dob   || "\u2014";
    const classLabel = b.classLabel  || b.seatClass || "\u2014";
    const code       = b.seatClass   || "SL";
    const accent     = ACCENT_MAP[code] || "#6366f1";

    return `
    <div style="border-radius:13px;overflow:hidden;border:1px solid var(--glass-border);font-size:.83rem;">

        <div style="background:linear-gradient(135deg,${accent} 0%,${accent}cc 100%);
                    padding:1.05rem 1.35rem;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-weight:800;font-size:.96rem;">\uD83D\uDE86 QuickRail</div>
                <div style="font-size:.6rem;opacity:.8;margin-top:2px;letter-spacing:.8px;text-transform:uppercase;">
                    ${classLabel} &nbsp;&middot;&nbsp; E-Ticket</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:.57rem;opacity:.75;text-transform:uppercase;letter-spacing:1px;">PNR</div>
                <div style="font-weight:800;font-size:.88rem;letter-spacing:1.5px;">${b.pnr}</div>
            </div>
        </div>

        <div style="padding:1.1rem 1.35rem;background:rgba(255,255,255,.025);">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
                <div>
                    <div style="font-size:1.15rem;font-weight:800;">${from}</div>
                    <div style="color:${accent};font-weight:700;font-size:.86rem;">${b.dep}</div>
                    <div style="color:var(--text-muted);font-size:.6rem;margin-top:1px;">Departure</div>
                </div>
                <div style="flex:1;text-align:center;">
                    <div style="font-size:.62rem;font-weight:600;color:var(--text-muted);">${b.duration || ""}</div>
                    <div style="display:flex;align-items:center;gap:4px;margin:4px 0;">
                        <div style="flex:1;height:1px;background:var(--glass-border);"></div>
                        <span style="color:${accent};font-size:.88rem;">&rsaquo;</span>
                        <div style="flex:1;height:1px;background:var(--glass-border);"></div>
                    </div>
                    <div style="font-size:.58rem;color:var(--text-muted);">${b.day || ""}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.15rem;font-weight:800;">${to}</div>
                    <div style="color:${accent};font-weight:700;font-size:.86rem;">${b.arr}</div>
                    <div style="color:var(--text-muted);font-size:.6rem;margin-top:1px;">Arrival</div>
                </div>
            </div>
            <div style="margin-top:.85rem;padding-top:.82rem;border-top:1px solid var(--glass-border);
                        display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-weight:700;font-size:.83rem;">${b.trainName}</div>
                    <div style="color:var(--text-muted);font-size:.63rem;">#${b.trainId}</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
                    <div style="font-weight:800;font-size:1.05rem;color:var(--success);">S${b.seat}</div>
                    ${classPill(code)}
                </div>
            </div>
        </div>

        <div style="display:flex;align-items:center;padding:0 1.35rem;margin:0 -1px;">
            <div style="width:14px;height:14px;border-radius:50%;background:var(--bg);
                        border:1px solid var(--glass-border);margin-left:-21px;flex-shrink:0;"></div>
            <div style="flex:1;border-top:2px dashed rgba(255,255,255,.07);"></div>
            <div style="width:14px;height:14px;border-radius:50%;background:var(--bg);
                        border:1px solid var(--glass-border);margin-right:-21px;flex-shrink:0;"></div>
        </div>

        <div style="padding:.95rem 1.35rem;background:rgba(0,0,0,.16);
                    display:grid;grid-template-columns:1fr 1fr;gap:.72rem .95rem;">
            ${pf("Passenger", pName)}
            ${pf("Phone",     pPh)}
            ${pf("D.O.B",    pDob)}
            ${pf("Fare Paid","<span style='color:var(--success);'>&#8377;" + b.fare + "</span>")}
        </div>

        <div style="padding:.85rem 1.35rem;text-align:center;background:rgba(255,255,255,.01);">
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
        <div style="font-weight:700;font-size:.82rem;">${val}</div>
    </div>`;
}

function barcode(accent) {
    let s = "";
    for (let i = 0; i < 52; i++) {
        const w   = Math.random() > .5 ? 3 : 1.5;
        const h   = 18 + Math.random() * 14;
        const col = Math.random() > .82 ? accent : "var(--text-muted)";
        s += `<div style="width:${w}px;height:${h}px;background:${col};
               border-radius:1px;flex-shrink:0;opacity:.68;"></div>`;
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
                    <i data-lucide="ticket" size="34" style="margin-bottom:1.1rem;opacity:.33;"></i>
                    <p style="font-weight:700;margin-bottom:.4rem;">No bookings yet</p>
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
            if (b.cancelled) card.style.opacity = ".5";

            const rightCol = b.cancelled
                ? `<div style="text-align:right;">
                       <div class="badge badge-red" style="margin-bottom:5px;">Cancelled</div><br>
                       <div style="font-size:.68rem;color:var(--text-muted);">
                           &#8377;${b.refund} refunded
                       </div>
                   </div>`
                : `<div style="text-align:right;display:flex;flex-direction:column;
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

            card.innerHTML =
                `<div>
                    <div style="font-weight:800;font-size:.95rem;margin-bottom:5px;">
                        ${b.trainName}
                    </div>
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                        <span style="color:var(--text-muted);font-size:.7rem;font-weight:600;">
                            ${b.from || "\u2014"} &rarr; ${b.to || "\u2014"}
                            &nbsp;&middot;&nbsp; Seat ${b.seat}
                        </span>
                        ${classPill(b.seatClass || "SL")}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:.9rem;">${b.dep}</div>
                    <div class="col-label">Dep.</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700;font-size:.9rem;">${b.bookedDate}</div>
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
    if (!confirm("Cancel booking " + pnr + "?\n\nYou'll receive a 90% refund within 24 hours.")) return;

    try {
        const res    = await fetch("/cancel-booking", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ pnr }),
        });
        const result = await res.json();

        if (result.success) {
            showToast("Cancelled \u00B7 \u20B9" + result.refund + " refund in 24 hrs.", "success");
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
            ? "rgba(16,185,129,.94)" : "rgba(239,68,68,.94)") + ";" +
        "color:#fff;border-radius:12px;font-weight:700;z-index:9999;" +
        "font-size:.84rem;box-shadow:0 13px 30px rgba(0,0,0,.4);" +
        "animation:toastIn .36s cubic-bezier(.16,1,.3,1) forwards;" +
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
    .badge-green { background:rgba(16,185,129,.1); color:var(--success); border:1px solid rgba(16,185,129,.2); }
    .badge-red   { background:rgba(239,68,68,.1);  color:var(--danger);  border:1px solid rgba(239,68,68,.2); }
    .btn-sm {
        padding:4px 9px; font-size:.68rem; border-radius:7px;
        display:inline-flex; align-items:center; gap:4px;
        font-weight:700; cursor:pointer; transition:.18s; border:none;
    }
    .btn-sm:hover { filter:brightness(1.14); transform:translateY(-1px); }
    .btn-primary { background:rgba(99,102,241,.12); color:var(--primary); border:1px solid rgba(99,102,241,.22) !important; }
    .btn-red     { background:rgba(239,68,68,.09);  color:var(--danger);  border:1px solid rgba(239,68,68,.2)  !important; }
    .book-btn    { padding:.52rem .95rem; font-size:.8rem; border-radius:9px; display:inline-flex; align-items:center; gap:4px; }
    .step-dot {
        width:7px; height:7px; border-radius:50%; background:var(--glass-border);
        transition:background .26s, transform .26s, box-shadow .26s; flex-shrink:0;
    }
    .step-dot.active { background:var(--primary); transform:scale(1.3); box-shadow:0 0 7px var(--primary-glow); }
    .step-dot.done   { background:var(--success); transform:scale(1); }
    .modal-step { display:none; flex-direction:column; gap:.92rem; }
    .demo-stripe {
        display:flex; align-items:center; gap:8px;
        background:rgba(251,191,36,.07); border:1px solid rgba(251,191,36,.18);
        border-radius:10px; padding:.68rem .82rem;
        font-size:.73rem; color:#fbbf24; font-weight:600;
    }
`;
document.head.appendChild(_u);