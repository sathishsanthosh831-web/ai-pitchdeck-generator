# AI-Based Pitch Deck Generator

Generates a structured, editable pitch deck (problem, solution, features, target
audience, market opportunity, business model, competitors, future scope) from a
one-paragraph startup idea, using an LLM — then exports it as a `.pptx` file.

## Stack
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Backend:** Python (Flask)
- **Database:** PostgreSQL
- **AI:** Anthropic Claude API (swappable for OpenAI/Gemini)
- **Export:** python-pptx

## Project structure
```
pitchdeck-generator/
├── app.py                  # Flask routes / API
├── requirements.txt
├── schema.sql               # PostgreSQL schema
├── .env.example              # copy to .env and fill in
├── models/
│   └── db.py                 # PostgreSQL queries
├── services/
│   ├── ai_generator.py        # calls the LLM, returns structured JSON
│   └── ppt_generator.py       # builds the .pptx with python-pptx
├── templates/
│   ├── index.html             # idea input form
│   └── editor.html            # slide review/edit screen
├── static/
│   ├── css/style.css
│   └── js/main.js, editor.js
└── exports/                  # generated .pptx files land here
```

## Setup

1. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL**
   ```bash
   psql -U postgres -d pitchdeck_db -f schema.sql
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # then edit .env with your DB credentials and ANTHROPIC_API_KEY
   ```

4. **Run the app**
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000`

## How it works

1. User enters their startup idea + industry on the home page.
2. `POST /api/generate` sends the idea to `services/ai_generator.py`, which
   prompts the LLM to return strict JSON: startup name, tagline, and 8 slides
   (problem, solution, key features, target audience, market opportunity,
   business model, competitors, future scope), each with a title and bullets.
3. The deck and slides are saved to PostgreSQL (`decks` and `slides` tables).
4. The user is redirected to `/editor/<deck_id>`, which loads the slides via
   `GET /api/decks/<id>` and renders them as editable cards. Edits auto-save
   via `PUT /api/slides/<id>` (debounced).
5. Clicking **Export as PPT** hits `GET /api/decks/<id>/export`, which builds
   the `.pptx` with `services/ppt_generator.py` (python-pptx) and downloads it.

## Notes / next steps
- Auth is stubbed out (`user_id` is nullable) — add login/signup and pass the
  real `user_id` into `create_deck()` when you're ready for multi-user support.
- `ai_generator.py` uses the Anthropic SDK; swap `_call_llm()` for OpenAI's
  `chat.completions.create()` if you'd rather use GPT — the rest of the app
  only depends on the JSON shape it returns.
- The pptx design in `ppt_generator.py` is intentionally simple — customize
  colors/fonts/layout in that file, or add a template picker so users choose
  a theme before export.
- Consider adding a "Regenerate this slide" button (call the AI for just one
  slide_type) instead of only whole-deck regeneration.
