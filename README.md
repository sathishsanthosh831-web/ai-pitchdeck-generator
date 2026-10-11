# Pitchora — Turning Business Ideas into Professional Presentations (B.Sc CS Final Year Project)

A complete web-based application built with **Python, Flask, HTML, CSS, JavaScript, and python-pptx** to generate, customize, and export structured business pitch decks with topic-aware slide content and distinct slide illustrations.

---

## 🚀 How to Run in Visual Studio Code (Windows / Linux / Mac)

This package contains the 8-slide version of Pitchora. The title slide uses bold styling, and each key slide category has its own illustration design. Generated content is a proposal and should be checked for accuracy before presentation.

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
2. **Business Idea Input:** Startup name, industry, tagline, problem statement, and proposed solution.
3. **AI Content Generation:** Generates 11 structured slides (Title, Problem, Solution, Target Customers, Key Features, TAM/SAM/SOM, Business Model, Competitors, Marketing Strategy, Roadmap, and Vision & Strategic Growth).
4. **Pitch Deck Preview:** Interactive slide carousel with live responsive rendering.
5. **Edit & Customize:** In-place editing of slide titles, bullet points, and presenter notes.
6. **PowerPoint (.pptx) Generation:** Uses Python's `python-pptx` library to create native 16:9 widescreen PowerPoint files.
7. **Download & History:** Local database persistence via SQLite / MySQL.

---

## 🎓 Viva Questions & External Examiner Preparation

See `viva_prep.md` in this folder for the full list of examiner questions with answers!
## Render deployment

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- The project root contains `app.py`, `templates/`, and `static/` directly.
- Set `DATABASE_URL` to your Render PostgreSQL database URL. The app normalizes PostgreSQL URLs for psycopg 3 automatically.


## Content accuracy and presentation themes

- Enter a specific problem statement, proposed solution, and target audience for more relevant slides.
- The target-audience field is optional, but adding it improves the audience, value, future-opportunity, and roadmap slides.
- The generator builds a structured presentation from the supplied text. It does not currently call a hosted AI model, so it does not invent market statistics, revenue figures, or competitor claims.
- The Professional, Startup, and Dark presentation themes affect the browser slide preview and PowerPoint export.
- Decks saved in history retain their selected theme.


## Windows setup (important for PDF export)

1. Extract the ZIP completely.
2. Double-click `INSTALL_AND_RUN.bat` once. It installs all packages in `requirements.txt`, including `reportlab` for PDF export. Wait until it finishes.
3. Open PowerShell in this folder and run `python app.py`.
4. Visit `http://127.0.0.1:5000`.
5. To export a PDF, generate a deck first, then choose **Export → PDF Document**.

If the browser says `No module named 'reportlab'`, the dependency installation was not completed in the same Python environment used to run `app.py`. Run `python -m pip install reportlab==4.2.5` using that same Python, stop the server with Ctrl+C, and restart `python app.py`.


## Build a Windows desktop EXE

This ZIP includes `BUILD_WINDOWS_EXE.bat`, which builds a Windows desktop launcher using PyInstaller. The EXE opens Pitchora in your default browser at `http://127.0.0.1:5000`; it is a locally running app, not a standalone native window.

1. Extract the whole ZIP to a normal folder (not inside the ZIP preview).
2. Install Python 3.11 or 3.12 for Windows from python.org and select **Add Python to PATH**.
3. Double-click `BUILD_WINDOWS_EXE.bat` and wait for the build to finish. An internet connection is needed to install Python packages.
4. Run `dist\Pitchora\Pitchora.exe`. Keep the entire `dist\Pitchora` folder together.
5. To stop the local server, close the console window opened by Pitchora.

**Important:** This is a build kit, not a precompiled EXE. Build it on a Windows laptop because PyInstaller builds for the operating system on which it runs. Do not delete the `templates`/`static` assets from the project before building. The current project does not require a hosted AI API for its slide generation; internet may still be needed for package installation.


## Accounts and sharing across devices
This version includes Sign Up, Login and Logout. See `AUTH_AND_SHARED_DATABASE_SETUP.md` for local testing and online shared-database deployment. A local EXE uses local storage; shared accounts across laptops require deploying the Flask app with a shared PostgreSQL `DATABASE_URL`.


## Desktop app (no browser address bar)

The project includes `desktop_launcher.py`, which opens Pitchora in a native desktop window using pywebview. The internal Flask server is used only behind that window; the user does not see a browser address bar or localhost URL.

To build a Windows executable on a Windows computer with Python installed:

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller==6.11.1
python -m PyInstaller --noconfirm --clean --onedir --name Pitchora --add-data "templates;templates" --add-data "static;static" --hidden-import flask_cors --hidden-import flask_sqlalchemy --hidden-import sqlalchemy.dialects.sqlite --hidden-import pptx --hidden-import reportlab --hidden-import webview --collect-all webview desktop_launcher.py
```

The executable is created under `dist/Pitchora/Pitchora.exe`. Share the entire `dist/Pitchora` folder (or zip that folder), not only the EXE. AI features may require internet access and a valid API key. A desktop window hides the localhost address; Flask still uses an internal local server.


## Google-only sign-in

Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `FLASK_SECRET_KEY` in Render Environment Variables. In Google Cloud Console, add the deployed callback URL `https://YOUR-RENDER-SERVICE.onrender.com/auth/google/callback` to **Authorized redirect URIs** (replace the hostname with your actual Render hostname). Keep the Google client secret private and never commit it to GitHub. The app now uses Google OAuth for sign-in; username/password login and sign-up forms are disabled.
