const container = document.getElementById("slidesContainer");
const deckTitleEl = document.getElementById("deckTitle");
const exportBtn = document.getElementById("exportBtn");

let saveTimers = {}; // debounce per-slide saves

function debounceSave(slideId, fn) {
  clearTimeout(saveTimers[slideId]);
  saveTimers[slideId] = setTimeout(fn, 600);
}

function renderSlide(slide) {
  const card = document.createElement("div");
  card.className = "slide-card";
  card.dataset.slideId = slide.id;

  const label = document.createElement("div");
  label.className = "slide-label";
  label.textContent = slide.slide_type.replace(/_/g, " ");
  card.appendChild(label);

  const titleInput = document.createElement("input");
  titleInput.className = "slide-title";
  titleInput.value = slide.title || "";
  card.appendChild(titleInput);

  const bulletsWrap = document.createElement("div");
  bulletsWrap.className = "bullets-wrap";
  card.appendChild(bulletsWrap);

  const bullets = (slide.content && slide.content.bullets) || [];
  bullets.forEach((bullet) => addBulletRow(bulletsWrap, bullet));

  const addBtn = document.createElement("button");
  addBtn.className = "add-bullet-btn";
  addBtn.textContent = "+ Add point";
  addBtn.type = "button";
  addBtn.addEventListener("click", () => {
    addBulletRow(bulletsWrap, "");
    scheduleSave(slide.id, card);
  });
  card.appendChild(addBtn);

  const hint = document.createElement("div");
  hint.className = "save-hint";
  hint.textContent = "Changes save automatically";
  card.appendChild(hint);

  // Save on any edit
  card.addEventListener("input", () => scheduleSave(slide.id, card));

  return card;
}

function addBulletRow(wrap, text) {
  const row = document.createElement("div");
  row.className = "bullet-row";

  const textarea = document.createElement("textarea");
  textarea.value = text;
  row.appendChild(textarea);

  const removeBtn = document.createElement("button");
  removeBtn.textContent = "Remove";
  removeBtn.type = "button";
  removeBtn.addEventListener("click", () => {
    row.remove();
    row.dispatchEvent(new Event("input", { bubbles: true }));
  });
  row.appendChild(removeBtn);

  wrap.appendChild(row);
}

function collectSlideData(card) {
  const title = card.querySelector(".slide-title").value;
  const bulletTexts = Array.from(card.querySelectorAll(".bullet-row textarea"))
    .map((t) => t.value.trim())
    .filter((t) => t.length > 0);
  return { title, content: { bullets: bulletTexts } };
}

function scheduleSave(slideId, card) {
  debounceSave(slideId, async () => {
    const payload = collectSlideData(card);
    await fetch(`/api/slides/${slideId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  });
}

async function loadDeck() {
  const res = await fetch(`/api/decks/${DECK_ID}`);
  if (!res.ok) {
    deckTitleEl.textContent = "Deck not found";
    return;
  }
  const deck = await res.json();
  deckTitleEl.textContent = deck.startup_name;
  container.innerHTML = "";
  deck.slides.forEach((slide) => container.appendChild(renderSlide(slide)));
}

exportBtn.addEventListener("click", () => {
  window.location.href = `/api/decks/${DECK_ID}/export`;
});

loadDeck();
