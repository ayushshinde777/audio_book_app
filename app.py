from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from gtts import gTTS
from deep_translator import GoogleTranslator
import os
import io
import uuid

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-string" 

ALLOWED_EXTENSIONS = {"txt"}
DEFAULT_LANG = "en"
DEFAULT_TLD = "co.in"

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/synthesize", methods=["POST"])
def synthesize():

    input_text = request.form.get("text", "").strip()
    slow = request.form.get("slow") == "on"
    tld = request.form.get("tld", DEFAULT_TLD).strip() or DEFAULT_TLD

    tts_lang = request.form.get("tts_lang", DEFAULT_LANG).strip() or DEFAULT_LANG

    do_translate = request.form.get("do_translate") == "on"
    target_lang = request.form.get("target_lang", tts_lang).strip() or tts_lang

    uploaded_file = request.files.get("text_file")
    if uploaded_file and uploaded_file.filename:
        if not allowed_file(uploaded_file.filename):
            flash("Only .txt files are allowed.", "error")
            return redirect(url_for("index"))
        file_text = uploaded_file.read().decode("utf-8", errors="ignore")
        input_text = file_text.strip()

    if not input_text:
        flash("Please provide text or upload a .txt file.", "error")
        return redirect(url_for("index"))

    final_text = input_text
    final_lang = tts_lang
    if do_translate:
        try:

            source_lang = request.form.get("source_lang", "auto").strip() or "auto"
            final_text = GoogleTranslator(source=source_lang, target=target_lang).translate(input_text)
            final_lang = target_lang
        except Exception as e:
            flash(f"Translation failed: {e}", "error")
            return redirect(url_for("index"))


    try:
        tts = gTTS(text=final_text, lang=final_lang, slow=slow, tld=tld)
        mp3_bytes = io.BytesIO()
        tts.write_to_fp(mp3_bytes)
        mp3_bytes.seek(0)
    except Exception as e:
        flash(f"TTS failed: {e}", "error")
        return redirect(url_for("index"))


    base_name = request.form.get("file_basename", "audiobook").strip() or "audiobook"
    safe_base = "".join(c for c in base_name if c.isalnum() or c in ("-", "_")).rstrip()
    filename = f"{safe_base}_{uuid.uuid4().hex[:8]}.mp3"


    return send_file(
        mp3_bytes,
        as_attachment=True,
        download_name=filename,
        mimetype="audio/mpeg"
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)
