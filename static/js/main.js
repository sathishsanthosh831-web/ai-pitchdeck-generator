const form = document.getElementById("ideaForm");
const statusEl = document.getElementById("status");
const generateBtn = document.getElementById("generateBtn");

function showStatus(message, type) {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const idea_description = document.getElementById("startup_idea").value.trim();
  const industry = document.getElementById("industry").value.trim();

  if (!idea_description) return;

  generateBtn.disabled = true;
  showStatus("Generating your pitch deck with AI... this can take a few seconds.", "loading");

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea_description, industry }),
    });

    const data = await res.json();

    if (!res.ok) {
      showStatus(data.error || "Something went wrong. Please try again.", "error");
      generateBtn.disabled = false;
      return;
    }

    showStatus(`Deck created for "${data.startup_name}". Redirecting to editor...`, "success");
    setTimeout(() => {
      window.location.href = `/editor/${data.deck_id}`;
    }, 800);
  } catch (err) {
    showStatus("Network error — is the Flask server running?", "error");
    generateBtn.disabled = false;
  }
});
