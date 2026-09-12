/* Multilingual Meeting Transcription — frontend logic */
const state = {
  meetingId: null,
  languages: [],
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ---------- Languages ---------- */
async function loadLanguages() {
  const data = await api("/api/languages");
  state.languages = data.languages.filter((l) => !l.code.includes(","));
  const mode = $("language-mode");
  const notesLang = $("notes-language");
  const transLang = $("translate-language");
  for (const lang of state.languages) {
    for (const sel of [mode, notesLang, transLang]) {
      const opt = document.createElement("option");
      opt.value = lang.code;
      opt.textContent = lang.name;
      sel.appendChild(opt);
    }
  }
}

/* ---------- Upload + Transcribe ---------- */
$("btn-upload").addEventListener("click", async () => {
  const status = $("upload-status");
  status.textContent = "Working…";
  try {
    const title = $("meeting-title").value || "Untitled meeting";
    const fileInput = $("audio-file");
    if (!fileInput.files.length) throw new Error("Choose an audio file first.");

    const meeting = await api("/api/meetings", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    state.meetingId = meeting.id;

    const form = new FormData();
    form.append("file", fileInput.files[0]);
    await fetch(`/api/meetings/${state.meetingId}/upload`, { method: "POST", body: form });

    const languageMode = $("language-mode").value === "code-switching"
      ? "code-switching"
      : $("language-mode").value === "auto" ? "auto" : `manual:${$("language-mode").value}`;

    await api(`/api/meetings/${state.meetingId}/transcribe`, {
      method: "POST",
      body: JSON.stringify({
        language_mode: languageMode,
        code_switching: $("code-switching").checked,
        use_custom_vocabulary: true,
      }),
    });
    status.textContent = "Transcribed ✓";
    await renderTranscript();
  } catch (err) {
    status.textContent = "Error: " + err.message;
  }
});

/* ---------- Transcript ---------- */
async function renderTranscript() {
  if (!state.meetingId) return;
  const data = await api(`/api/meetings/${state.meetingId}/transcript`);

  const badgeRow = $("meeting-language");
  badgeRow.innerHTML = "";
  if (data.meeting_language) {
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = `Meeting language: ${data.meeting_language}`;
    badgeRow.appendChild(badge);
  }

  const container = $("transcript");
  container.innerHTML = "";
  const switches = new Set(data.language_switches.map((s) => s.at_segment));

  data.segments.forEach((seg, idx) => {
    if (switches.has(idx)) {
      const sw = data.language_switches.find((s) => s.at_segment === idx);
      const marker = document.createElement("div");
      marker.className = "switch-marker";
      marker.textContent = `⇄ Language switch: ${sw.from_lang} → ${sw.to_lang}`;
      container.appendChild(marker);
    }
    const div = document.createElement("div");
    div.className = "segment" + (seg.low_confidence ? " warning" : "");
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.innerHTML = `
      <span>[${fmt(seg.start)}]</span>
      <strong>${seg.speaker || "Speaker"}</strong>
      <span class="badge">${seg.language_label || "Unknown"}</span>
      <span>script: ${seg.script || "?"}</span>
      ${seg.language_confidence != null ? `<span>conf: ${(seg.language_confidence * 100).toFixed(0)}%</span>` : ""}
    `;
    const text = document.createElement("div");
    text.className = "text";
    text.textContent = seg.text;
    div.appendChild(meta);
    div.appendChild(text);
    if (seg.warning) {
      const warn = document.createElement("div");
      warn.className = "warning-text";
      warn.textContent = seg.warning;
      div.appendChild(warn);
    }
    container.appendChild(div);
  });
}

function fmt(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/* ---------- Notes / Translation ---------- */
$("btn-notes").addEventListener("click", async () => {
  if (!state.meetingId) return alert("Transcribe a meeting first.");
  const out = $("notes-output");
  out.textContent = "Generating…";
  try {
    const note = await api(`/api/meetings/${state.meetingId}/notes`, {
      method: "POST",
      body: JSON.stringify({
        kind: $("notes-kind").value,
        language: $("notes-language").value,
      }),
    });
    out.textContent = note.content;
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
});

$("btn-translate").addEventListener("click", async () => {
  if (!state.meetingId) return alert("Transcribe a meeting first.");
  const out = $("notes-output");
  out.textContent = "Translating…";
  try {
    const result = await api(`/api/meetings/${state.meetingId}/translate`, {
      method: "POST",
      body: JSON.stringify({
        target_language: $("translate-language").value,
        source: "transcript",
      }),
    });
    out.textContent = result.content;
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
});

/* ---------- Vocabulary ---------- */
async function renderVocabulary() {
  const entries = await api("/api/vocabulary");
  const list = $("vocab-list");
  list.innerHTML = "";
  for (const e of entries) {
    const li = document.createElement("li");
    li.innerHTML = `<span>${e.term}</span><span class="del" data-id="${e.id}">✕</span>`;
    list.appendChild(li);
  }
  list.querySelectorAll(".del").forEach((el) =>
    el.addEventListener("click", async () => {
      await fetch(`/api/vocabulary/${el.dataset.id}`, { method: "DELETE" });
      renderVocabulary();
    })
  );
}

$("btn-vocab").addEventListener("click", async () => {
  const term = $("vocab-term").value.trim();
  if (!term) return;
  await api("/api/vocabulary", {
    method: "POST",
    body: JSON.stringify({ term, category: $("vocab-category").value }),
  });
  $("vocab-term").value = "";
  renderVocabulary();
});

/* ---------- Settings ---------- */
async function loadSettings() {
  const s = await api("/api/settings");
  $("provider-name").value = s.llm_default_provider;
  const provider = s.llm_providers.find((p) => p.name === s.llm_default_provider);
  if (provider) {
    $("provider-base-url").value = provider.base_url || "";
    $("provider-api-key").value = provider.api_key || "";
    $("provider-model").value = provider.model || "";
  }
}

$("provider-name").addEventListener("change", async () => {
  const s = await api("/api/settings");
  const name = $("provider-name").value;
  const provider = s.llm_providers.find((p) => p.name === name) || { base_url: "", api_key: "", model: "" };
  $("provider-base-url").value = provider.base_url || "";
  $("provider-api-key").value = provider.api_key || "";
  $("provider-model").value = provider.model || "";
});

$("btn-settings").addEventListener("click", async () => {
  const status = $("settings-status");
  status.textContent = "Saving…";
  try {
    const name = $("provider-name").value;
    const s = await api("/api/settings");
    const providers = s.llm_providers.filter((p) => p.name !== name);
    providers.push({
      name,
      base_url: $("provider-base-url").value.trim(),
      api_key: $("provider-api-key").value.trim() || null,
      model: $("provider-model").value.trim(),
    });
    await api("/api/settings", {
      method: "PUT",
      body: JSON.stringify({ llm_default_provider: name, llm_providers: providers }),
    });
    status.textContent = "Saved ✓";
  } catch (err) {
    status.textContent = "Error: " + err.message;
  }
});

/* ---------- Boot ---------- */
(async function init() {
  try {
    await loadLanguages();
    await renderVocabulary();
    await loadSettings();
  } catch (err) {
    console.error(err);
  }
})();
