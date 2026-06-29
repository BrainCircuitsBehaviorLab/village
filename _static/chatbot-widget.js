/**
 * Training Village - Documentation Chatbot Widget
 *
 * Usage: included automatically via conf.py html_js_files
 * Requires: WORKER_URL updated to your Cloudflare Worker URL
 */

(function () {
  const WORKER_URL = "https://village-chatbot.braincircuitsbehaviorlab.workers.dev";

  const CSS = `
    :root {
      --tv-accent: #185FA5;
      --tv-accent-light: #E6F1FB;
      --tv-accent-mid: #378ADD;
      --tv-accent-dark: #0C447C;
      --tv-radius: 14px;
      --tv-shadow: 0 4px 24px rgba(24,95,165,0.13), 0 1px 4px rgba(0,0,0,0.08);
    }
    #tv-chat-btn {
      position: fixed; bottom: 28px; right: 28px;
      width: 54px; height: 54px; border-radius: 50%;
      background: var(--tv-accent); border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: var(--tv-shadow); z-index: 9999;
      transition: background 0.15s, transform 0.15s;
    }
    #tv-chat-btn:hover { background: var(--tv-accent-dark); transform: scale(1.06); }
    #tv-chat-btn:active { transform: scale(0.97); }
    #tv-chat-btn svg { width: 26px; height: 26px; fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    #tv-chat-panel {
      position: fixed; bottom: 92px; right: 28px;
      width: 360px; max-height: 520px;
      display: flex; flex-direction: column;
      background: #fff; border: 0.5px solid rgba(0,0,0,0.12);
      border-radius: var(--tv-radius); box-shadow: var(--tv-shadow);
      z-index: 9998; overflow: hidden;
      transition: opacity 0.18s, transform 0.18s;
    }
    [data-theme="dark"] #tv-chat-panel { background: #1e1e1e; border-color: rgba(255,255,255,0.1); }
    #tv-chat-panel.tv-hidden { opacity: 0; pointer-events: none; transform: translateY(10px) scale(0.98); }
    #tv-header {
      background: var(--tv-accent); padding: 14px 16px;
      display: flex; align-items: center; gap: 10px;
    }
    #tv-header-icon {
      width: 32px; height: 32px; border-radius: 50%;
      background: rgba(255,255,255,0.18);
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    #tv-header-icon svg { width: 17px; height: 17px; fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    #tv-header-text { flex: 1; }
    #tv-header-title { color: #fff; font-size: 14px; font-weight: 500; margin: 0; line-height: 1.2; }
    #tv-header-sub { color: rgba(255,255,255,0.72); font-size: 11px; margin: 0; }
    #tv-close-btn {
      background: none; border: none; cursor: pointer; padding: 4px;
      border-radius: 6px; color: rgba(255,255,255,0.8); display: flex; align-items: center;
    }
    #tv-close-btn:hover { color: #fff; background: rgba(255,255,255,0.12); }
    #tv-close-btn svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
    #tv-messages {
      flex: 1; overflow-y: auto; padding: 14px;
      display: flex; flex-direction: column; gap: 10px; min-height: 0;
    }
    .tv-msg {
      max-width: 88%; font-size: 13.5px; line-height: 1.55;
      padding: 9px 13px; border-radius: 12px; white-space: pre-wrap; word-break: break-word;
    }
    .tv-msg.tv-bot { background: #f0f0ee; color: #1a1a1a; align-self: flex-start; border-bottom-left-radius: 4px; }
    [data-theme="dark"] .tv-msg.tv-bot { background: #2a2a2a; color: #e8e8e8; }
    .tv-msg.tv-user { background: var(--tv-accent); color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }
    .tv-msg.tv-error { background: #FCEBEB; color: #A32D2D; align-self: flex-start; border-bottom-left-radius: 4px; font-size: 13px; }
    .tv-sources {
      margin-top: 4px; font-size: 11px; color: #888;
      display: flex; flex-wrap: wrap; gap: 4px;
      align-self: flex-start; max-width: 88%;
    }
    .tv-source-tag {
      background: var(--tv-accent-light); color: var(--tv-accent-dark);
      border-radius: 4px; padding: 2px 6px; font-size: 10.5px;
      font-family: monospace; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis; max-width: 160px;
    }
    .tv-typing {
      display: flex; gap: 4px; align-items: center; padding: 10px 14px;
      background: #f0f0ee; border-radius: 12px; border-bottom-left-radius: 4px;
      align-self: flex-start;
    }
    [data-theme="dark"] .tv-typing { background: #2a2a2a; }
    .tv-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--tv-accent-mid); animation: tv-bounce 1.2s infinite;
    }
    .tv-dot:nth-child(2) { animation-delay: 0.2s; }
    .tv-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes tv-bounce {
      0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
      40% { transform: translateY(-5px); opacity: 1; }
    }
    #tv-footer {
      padding: 10px 12px;
      border-top: 0.5px solid rgba(0,0,0,0.1);
      display: flex; gap: 8px; align-items: flex-end;
    }
    [data-theme="dark"] #tv-footer { border-top-color: rgba(255,255,255,0.08); }
    #tv-input {
      flex: 1; border: 0.5px solid rgba(0,0,0,0.18); border-radius: 10px;
      padding: 8px 11px; font-size: 13.5px; font-family: inherit;
      color: #1a1a1a; background: #fff; resize: none; outline: none;
      line-height: 1.45; max-height: 90px; overflow-y: auto;
    }
    [data-theme="dark"] #tv-input { background: #2a2a2a; color: #e8e8e8; border-color: rgba(255,255,255,0.15); }
    #tv-input:focus { border-color: var(--tv-accent-mid); box-shadow: 0 0 0 3px rgba(55,138,221,0.15); }
    #tv-input::placeholder { color: #aaa; }
    #tv-send-btn {
      width: 36px; height: 36px; border-radius: 9px;
      background: var(--tv-accent); border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: background 0.12s, transform 0.1s;
    }
    #tv-send-btn:hover { background: var(--tv-accent-dark); }
    #tv-send-btn:active { transform: scale(0.94); }
    #tv-send-btn:disabled { background: #ccc; cursor: not-allowed; }
    #tv-send-btn svg { width: 17px; height: 17px; fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    #tv-footer-note { text-align: center; font-size: 10.5px; color: #bbb; padding: 0 12px 8px; }
  `;

  function init() {
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    document.body.insertAdjacentHTML("beforeend", `
      <button id="tv-chat-btn" aria-label="Open documentation chatbot" title="Ask about the Training Village">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      </button>

      <div id="tv-chat-panel" class="tv-hidden" role="dialog" aria-label="Training Village chatbot">
        <div id="tv-header">
          <div id="tv-header-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 14h.01M12 14h.01M16 14h.01"/></svg>
          </div>
          <div id="tv-header-text">
            <p id="tv-header-title">Training Village assistant</p>
            <p id="tv-header-sub">Ask anything about the docs &amp; code</p>
          </div>
          <button id="tv-close-btn" aria-label="Close chatbot">
            <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div id="tv-messages" role="log" aria-live="polite">
          <div class="tv-msg tv-bot">Hi! I can answer questions about the Training Village system — hardware, software, configuration, and example tasks. What would you like to know?</div>
        </div>
        <div id="tv-footer">
          <textarea id="tv-input" rows="1" placeholder="Ask a question..." aria-label="Your question"></textarea>
          <button id="tv-send-btn" aria-label="Send">
            <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
        <div id="tv-footer-note">Powered by Claude · answers based on TV docs &amp; source code</div>
      </div>
    `);

    const chatBtn = document.getElementById("tv-chat-btn");
    const chatPanel = document.getElementById("tv-chat-panel");
    const closeBtn = document.getElementById("tv-close-btn");
    const msgs = document.getElementById("tv-messages");
    const inp = document.getElementById("tv-input");
    const sndBtn = document.getElementById("tv-send-btn");

    let isLoading = false;

    chatBtn.addEventListener("click", () => togglePanel(true));
    closeBtn.addEventListener("click", () => togglePanel(false));

    function togglePanel(open) {
      chatPanel.classList.toggle("tv-hidden", !open);
      chatBtn.querySelector("svg").innerHTML = open
        ? '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'
        : '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>';
      if (open) setTimeout(() => inp.focus(), 150);
    }

    inp.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    inp.addEventListener("input", () => {
      inp.style.height = "auto";
      inp.style.height = Math.min(inp.scrollHeight, 90) + "px";
    });
    sndBtn.addEventListener("click", sendMessage);

    function addMessage(text, role, sources) {
      const div = document.createElement("div");
      div.className = "tv-msg tv-" + role;
      div.textContent = text;
      msgs.appendChild(div);

      if (sources && sources.length > 0) {
        const st = document.createElement("div");
        st.className = "tv-sources";
        const unique = [...new Set(sources.map((s) => s.path.split("/").pop()))].slice(0, 4);
        unique.forEach((name) => {
          const tag = document.createElement("span");
          tag.className = "tv-source-tag";
          tag.textContent = name;
          st.appendChild(tag);
        });
        msgs.appendChild(st);
      }
      msgs.scrollTop = msgs.scrollHeight;
    }

    function showTyping() {
      const d = document.createElement("div");
      d.className = "tv-typing"; d.id = "tv-typing";
      d.innerHTML = '<div class="tv-dot"></div><div class="tv-dot"></div><div class="tv-dot"></div>';
      msgs.appendChild(d);
      msgs.scrollTop = msgs.scrollHeight;
    }

    function hideTyping() {
      const d = document.getElementById("tv-typing");
      if (d) d.remove();
    }

    async function sendMessage() {
      const q = inp.value.trim();
      if (!q || isLoading) return;
      addMessage(q, "user");
      inp.value = ""; inp.style.height = "auto";
      sndBtn.disabled = true; isLoading = true;
      showTyping();
      try {
        const res = await fetch(WORKER_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        });
        const data = await res.json();
        hideTyping();
        if (!res.ok) {
          addMessage(data.error || "Something went wrong. Please try again.", "error");
        } else {
          addMessage(data.answer, "bot", data.sources);
        }
      } catch {
        hideTyping();
        addMessage("Connection error. Please check your network and try again.", "error");
      } finally {
        isLoading = false; sndBtn.disabled = false; inp.focus();
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
