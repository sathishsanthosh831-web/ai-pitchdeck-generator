import os
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv

from services.ai_generator import generate_pitch_content
from services.ppt_generator import build_pptx
from models import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
CORS(app)

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")


# ---------- Pages ----------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/editor/<int:deck_id>")
def editor(deck_id):
    return render_template("editor.html", deck_id=deck_id)


# ---------- API: generate deck content from an idea ----------

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True)
    idea = (data.get("idea_description") or "").strip()
    industry = (data.get("industry") or "").strip()

    if not idea:
        return jsonify({"error": "idea_description is required"}), 400

    try:
        ai_result = generate_pitch_content(idea, industry)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception as exc:  # covers auth/network errors from the LLM SDK
        return jsonify({"error": f"AI generation failed: {exc}"}), 502

    startup_name = ai_result.get("startup_name") or "Untitled Startup"

    deck_id = db.create_deck(
        startup_name=startup_name,
        idea_description=idea,
        industry=industry,
    )
    db.save_slides(deck_id, ai_result["slides"])

    return jsonify({"deck_id": deck_id, "startup_name": startup_name}), 201


# ---------- API: fetch a deck + its slides for the editor ----------

@app.route("/api/decks/<int:deck_id>", methods=["GET"])
def api_get_deck(deck_id):
    deck = db.get_deck_with_slides(deck_id)
    if not deck:
        return jsonify({"error": "deck not found"}), 404
    return jsonify(deck)


# ---------- API: edit a single slide's title/content ----------

@app.route("/api/slides/<int:slide_id>", methods=["PUT"])
def api_update_slide(slide_id):
    data = request.get_json(force=True)
    title = data.get("title", "")
    content = data.get("content", {})
    db.update_slide(slide_id, title, content)
    return jsonify({"status": "ok"})


# ---------- API: export deck as .pptx ----------

@app.route("/api/decks/<int:deck_id>/export", methods=["GET"])
def api_export_deck(deck_id):
    deck = db.get_deck_with_slides(deck_id)
    if not deck:
        return jsonify({"error": "deck not found"}), 404

    safe_name = "".join(c if c.isalnum() else "_" for c in deck["startup_name"])
    output_path = os.path.join(EXPORT_DIR, f"{safe_name}_{deck_id}.pptx")
    build_pptx(deck, output_path)
    db.mark_exported(deck_id)

    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"{safe_name}_Pitch_Deck.pptx",
    )


if __name__ == "__main__":
    os.makedirs(EXPORT_DIR, exist_ok=True)
    app.run(debug=os.getenv("FLASK_DEBUG", "True") == "True", port=5000)
