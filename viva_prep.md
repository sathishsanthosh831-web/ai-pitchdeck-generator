# B.Sc Computer Science - Project Viva Questions & Answers

## Project Title: Pitchora — Smart Business Presentation Generator

---

### Q1: What is the main objective and problem statement of this project?
**Answer:**
Preparing a professional pitch deck manually takes founders and students days of effort to research market sizing (TAM/SAM/SOM), structure value propositions, build competitive matrices, and format slides.
**Objective:** The Pitchora — Smart Business Presentation Generator reduces this manual friction by taking simple business inputs (Company Name, Industry, Problem, Solution, Model) and automatically generating an 11-slide structured presentation that can be customized and exported directly as a native PowerPoint (`.pptx`) file.

---

### Q2: What is the tech stack used and why?
**Answer:**
- **Frontend:** HTML5, CSS3, JavaScript (Clean responsive layout, slide carousel, and live presentation preview).
- **Backend Framework:** Python with **Flask** (Lightweight WSGI web microframework ideal for microservices and API orchestration).
- **Presentation Engine:** **python-pptx** (Python library to programmatically manipulate Open XML PowerPoint files with custom layouts, colors, shapes, and speaker notes).
- **Database:** SQLite / MySQL with **SQLAlchemy ORM** for storing user profiles, business ideas, and versioned slides.
- **AI Processing:** Structured AI prompt engineering to synthesize market data, metrics, and bulleted slide content.

---

### Q3: How does the PowerPoint generation work technically?
**Answer:**
We use the `python-pptx` library in `app.py`:
1. It initializes a `Presentation()` instance with 16:9 widescreen dimensions (`Inches(13.333)` by `Inches(7.5)`).
2. Iterates through the generated slide data list.
3. Dynamically adds text frames for Title, Subtitle, Bullet points, and Metric boxes.
4. Adds Presenter Speaker Notes to the `slide.notes_slide`.
5. Writes the binary presentation to an in-memory `io.BytesIO()` buffer and sends it to the user with MIME type `application/vnd.openxmlformats-officedocument.presentationml.presentation`.

---

### Q4: What are the 11 typical pitch deck sections generated?
**Answer:**
1. Title & Tagline
2. Problem Statement
3. Proposed Solution
4. Target Customers / ICP
5. Key Product Features
6. Market Opportunity (TAM / SAM / SOM)
7. Business & Revenue Model
8. Competitors & Moat Matrix
9. Go-To-Market & Marketing Strategy
10. Product Roadmap & Milestones
11. Vision & Strategic Growth (Milestones, Resource Allocation & Execution)

---

### Q5: What is the database schema?
**Answer:**
Three relational tables managed by SQLAlchemy:
1. **`users`**: `id`, `username`, `email`, `password_hash`, `created_at`
2. **`pitch_decks`**: `id`, `user_id`, `title`, `industry`, `tagline`, `theme`, `created_at`
3. **`slides`**: `id`, `deck_id`, `category`, `title`, `subtitle`, `bullets_json`, `metrics_json`, `speaker_notes`, `order_index`
