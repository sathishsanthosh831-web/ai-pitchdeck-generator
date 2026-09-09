# AI-Based Pitch Deck Generator (B.Sc CS Final Year Project)

A complete web-based application built with **Python, Flask, HTML, CSS, JavaScript, and python-pptx** to automatically generate, customize, and export professional startup pitch decks using Artificial Intelligence.

---

## 🚀 How to Run in Visual Studio Code (Windows / Linux / Mac)

### Step 1: Open in VS Code
1. Extract the downloaded ZIP file.
2. Open **Visual Studio Code** and choose **File > Open Folder**, then select this extracted folder.

### Step 2: Open Terminal in VS Code
- Press `Ctrl + `` (backtick) or go to **Terminal > New Terminal**.

### Step 3: Install Required Dependencies
Run:
```bash
pip install -r requirements.txt
```
*(If you have multiple Python versions installed, use `python -m pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt`)*

### Step 4: Run the Flask Web Server
Run:
```bash
python app.py
```

### Step 5: Open in Your Browser
Open your web browser and visit:
```
http://127.0.0.1:5000
```

---

## 🏗️ Project Architecture & Modules

1. **User Login & Registration:** Session management and saved decks per user account.
2. **Business Idea Input:** Startup name, industry, problem, solution, target audience, business model, and key competitors.
3. **AI Content Generation:** Generates 11 structured slides (Title, Problem, Solution, Target Customers, Key Features, TAM/SAM/SOM, Business Model, Competitors, Marketing Strategy, Roadmap, and Vision & Strategic Growth).
4. **Pitch Deck Preview:** Interactive slide carousel with live responsive rendering.
5. **Edit & Customize:** In-place editing of slide titles, bullet points, and presenter notes.
6. **PowerPoint (.pptx) Generation:** Uses Python's `python-pptx` library to create native 16:9 widescreen PowerPoint files.
7. **Download & History:** Local database persistence via SQLite / MySQL.

---

## 🎓 Viva Questions & External Examiner Preparation

See `viva_prep.md` in this folder for the full list of examiner questions with answers!