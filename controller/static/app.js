let currentSessionId = null;
let ws = null;

// List all existing sessions and populate dropdown
async function listSessions() {
  const res = await fetch("/v1/sessions");
  const data = await res.json();
  const selector = document.getElementById("sessionSelector");
  selector.innerHTML = "";
  data.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.innerText = s.id;
    selector.appendChild(opt);
  });
}

document.getElementById("vncBtn").onclick = () => {
  if (!currentSessionId) return alert("Create a session first!");

  document.getElementById("vncContainer").style.display = "block";
  document.getElementById("vncFrame").src = `/vnc/vnc.html?host=window.location.hostname&port=6080&session=${currentSessionId}`;
};


// Update dropdown and select session
async function updateSessionSelector(sessionId) {
  await listSessions();
  document.getElementById("sessionSelector").value = sessionId;
}

// Render chat messages
function renderMessages(messages) {
  const chat = document.getElementById("chat");
  chat.innerHTML = "";
  if (!messages || messages.length === 0) return; // Do not show anything if no history
  messages.forEach(m => appendMessage(m.role, m.content));
}

// Append a single message to chat
function appendMessage(role, content) {
  const chat = document.getElementById("chat");
  const p = document.createElement("p");
  p.className = `msg ${role}`;
  p.innerText = `${role.toUpperCase()}: ${content}`;
  chat.appendChild(p);
  chat.scrollTop = chat.scrollHeight;
}

// Load history for current session
async function loadHistory() {
  if (!currentSessionId) return;
  const res = await fetch(`/v1/sessions/${currentSessionId}/history`);
  if (!res.ok) {
    renderMessages([]); // No history -> clear chat
    return;
  }
  const data = await res.json();
  renderMessages(data.history);
}

// Create a new session
async function createSession() {
  const res = await fetch("/v1/sessions", { method: "POST" });
  const data = await res.json();
  if (!data.id) return;
  currentSessionId = data.id;
  document.getElementById("session-id").textContent = currentSessionId;
  await updateSessionSelector(currentSessionId);
  await loadHistory();
  connectWebSocket(currentSessionId);
}

// Send user message
async function sendMessage() {
  if (!currentSessionId) return;
  const msgInput = document.getElementById("message");
  const msg = msgInput.value.trim();
  if (!msg) return;

  await fetch(`/v1/sessions/${currentSessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: msg })
  });

  appendMessage("user", msg);
  msgInput.value = "";
}

// Connect WebSocket to session for live assistant messages
function connectWebSocket(sessionId) {
  if (ws) ws.close();
  ws = new WebSocket(`ws://${window.location.host}/v1/realtime/ws/${sessionId}`);

  ws.onmessage = e => {
    try {
      const data = JSON.parse(e.data);
      if (data.message && data.message.content) appendMessage("assistant", data.message.content);
    } catch {}
  };
}

// Handle session selection change
document.getElementById("sessionSelector").onchange = async (e) => {
  currentSessionId = e.target.value;
  await loadHistory();
  connectWebSocket(currentSessionId);
};

// Attach button events
document.getElementById("createBtn").onclick = createSession;
document.getElementById("sendBtn").onclick = sendMessage;
document.getElementById("loadHistoryBtn").onclick = loadHistory;

// Initial load of sessions
listSessions();
