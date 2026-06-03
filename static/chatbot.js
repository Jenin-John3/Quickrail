/* ── Toggle ──────────────────────────────────────────────── */
function toggleChat() {
    const win       = document.getElementById("chat-window");
    const isVisible = win.style.display === "flex";

    if (isVisible) {
        win.style.opacity   = "0";
        win.style.transform = "translateY(20px) scale(0.97)";
        setTimeout(() => { win.style.display = "none"; }, 350);
    } else {
        win.style.display   = "flex";
        win.style.opacity   = "0";
        win.style.transform = "translateY(20px) scale(0.97)";
        void win.offsetHeight; /* force reflow */
        win.style.transition = "opacity .4s cubic-bezier(.16,1,.3,1), transform .4s cubic-bezier(.16,1,.3,1)";
        win.style.opacity    = "1";
        win.style.transform  = "translateY(0) scale(1)";

        /* One-time welcome message */
        const box = document.getElementById("chat-msgs");
        if (!box.dataset.greeted) {
            box.dataset.greeted = "1";
            appendBot("👋 Hi! I'm your QuickRail assistant. Ask me about fares, stations, schedules, or bookings.");
        }
        document.getElementById("chat-in").focus();
    }
}

/* ── Send ────────────────────────────────────────────────── */
async function sendChat() {
    const inp = document.getElementById("chat-in");
    const msg = inp.value.trim();
    if (!msg) return;

    appendUser(msg);
    inp.value = "";

    const typingId = showTyping();

    try {
        const res  = await fetch("/chat", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ message: msg })
        });
        const data = await res.json();
        removeTyping(typingId);
        appendBot(data.reply);
    } catch (err) {
        removeTyping(typingId);
        appendBot("⚠️ Connection lost. Please check the server.");
    }
}

/* ── Append helpers ──────────────────────────────────────── */
function appendUser(msg) {
    const box = document.getElementById("chat-msgs");
    const el  = document.createElement("div");
    el.className = "cb-row cb-user";
    el.innerHTML = `<div class="cb-bubble cb-bubble-user">${escHtml(msg)}</div>`;
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
}

function appendBot(html) {
    const box = document.getElementById("chat-msgs");
    const el  = document.createElement("div");
    el.className = "cb-row cb-bot";
    el.innerHTML = `<div class="cb-bubble cb-bubble-bot">${html}</div>`;
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
}

function showTyping() {
    const box = document.getElementById("chat-msgs");
    const id  = "tp-" + Date.now();
    const el  = document.createElement("div");
    el.id        = id;
    el.className = "cb-row cb-bot";
    /* typing bubble gets its own class so it can use flex for the dots */
    el.innerHTML =
        `<div class="cb-bubble cb-bubble-bot cb-typing">` +
        `<span class="cb-dot"></span>` +
        `<span class="cb-dot" style="animation-delay:.18s"></span>` +
        `<span class="cb-dot" style="animation-delay:.36s"></span>` +
        `</div>`;
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function escHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

/* ── Enter key ───────────────────────────────────────────── */
document.getElementById("chat-in")
    ?.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendChat();
        }
    });

/* ── Styles ──────────────────────────────────────────────── */
const _cs = document.createElement("style");
_cs.innerHTML = `
    /* Row wrappers control left/right alignment */
    .cb-row {
        display: flex;
        margin-bottom: 10px;
        animation: cbFade .32s cubic-bezier(.16,1,.3,1) forwards;
    }
    .cb-user { justify-content: flex-end; }
    .cb-bot  { justify-content: flex-start; }

    /* Bubble base — NO flex here, so text wraps normally */
    .cb-bubble {
        max-width: 80%;
        padding: 10px 14px;
        border-radius: 16px;
        font-size: 0.86rem;
        line-height: 1.55;
        word-break: break-word;
        white-space: pre-wrap;   /* preserves line breaks if any */
    }

    /* User bubble */
    .cb-bubble-user {
        background: var(--primary);
        color: #fff;
        border-bottom-right-radius: 4px;
        box-shadow: 0 5px 16px var(--primary-glow);
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Bot bubble */
    .cb-bubble-bot {
        background: rgba(255,255,255,0.05);
        color: var(--text-main);
        border: 1px solid var(--glass-border);
        border-bottom-left-radius: 4px;
    }

    /* Typing bubble — ONLY this one uses flex for the dots */
    .cb-typing {
        display: flex !important;
        align-items: center;
        gap: 5px;
        padding: 12px 16px;
    }

    /* Typing dots */
    .cb-dot {
        width: 6px;
        height: 6px;
        background: var(--text-muted);
        border-radius: 50%;
        flex-shrink: 0;
        animation: cbBlink 1.2s infinite ease-in-out;
    }

    @keyframes cbBlink {
        0%, 100% { opacity: .25; transform: scale(1);   }
        50%       { opacity: 1;   transform: scale(1.3); }
    }

    @keyframes cbFade {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(_cs);