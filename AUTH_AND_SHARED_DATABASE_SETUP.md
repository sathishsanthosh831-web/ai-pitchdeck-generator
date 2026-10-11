# Pitchora: Sign Up, Login, Logout and shared accounts

## Included in this build
- Sign Up with username, email and password confirmation.
- Login and Logout.
- Passwords are stored as Werkzeug password hashes, not readable passwords.
- Pitch deck history is scoped to the logged-in account; users cannot open another user's deck by changing the deck ID.
- The app supports a shared PostgreSQL database through `DATABASE_URL` and falls back to local SQLite for offline/local testing.

## Important: local EXE versus shared accounts
The EXE runs a local server and normally uses a local SQLite database. Accounts created in one laptop's EXE are therefore stored on that laptop and will NOT automatically appear on another laptop.

For the SAME accounts and pitch-deck history to work on multiple laptops, deploy this updated Flask app as an online web app and connect it to one shared PostgreSQL database. Users on all laptops then open the same website URL in their browsers. The EXE can still be used for local/offline testing, but it is not the shared-account version unless it is specifically configured to connect to the hosted database (not recommended for a public desktop build).

## Local test
1. Install Python 3.11 or 3.12.
2. Open this project folder in Command Prompt.
3. Run `INSTALL_AND_RUN.bat` or install the packages in `requirements.txt` and run `python app.py`.
4. Open `http://127.0.0.1:5000`, choose **Create an account**, then test Log out and Log in.
5. To make a new EXE, run `BUILD_WINDOWS_EXE.bat`; share the entire `dist\Pitchora` folder, not only `Pitchora.exe`.

## Online deployment requirements
1. Push this updated project to the Git repository used by your web host (or create a new web service from this project).
2. Attach/create a PostgreSQL database and set the web service's `DATABASE_URL` to its connection URL.
3. Set `FLASK_SECRET_KEY` to a long random secret value in the host's environment settings. Do not use the fallback development value in a public deployment.
4. Use the start command `gunicorn app:app`.
5. Redeploy, then test Sign Up on one browser/device and Log in with the same account on a second device.
6. Keep database credentials and AI API keys in the host's environment settings; never put them in public source files or the EXE.

## Existing data
The app calls `db.create_all()` at startup. This creates missing tables but does not migrate arbitrary old schemas. Back up any important database before deployment. Existing decks created before login may have no `user_id` and will not show in an account's history automatically.
