import sys
import os

# ── Must be first — define paths before anything else ─────────
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.abspath(os.path.join(_THIS_DIR, "models"))

print(f"📂 ML service directory : {_THIS_DIR}")
print(f"📁 Models directory     : {MODELS_DIR}")
print(f"📋 Files in ml_service  : {os.listdir(_THIS_DIR)}")
print(f"📋 Files in models/     : {os.listdir(MODELS_DIR) if os.path.exists(MODELS_DIR) else 'FOLDER MISSING'}")

# ── Add this folder to Python path ────────────────────────────
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# ── Standard imports ───────────────────────────────────────────
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import tempfile
import traceback

# ── Local module imports ───────────────────────────────────────
try:
    from audio_features import extract_features
    print("✅ audio_features loaded")
except ImportError as e:
    print(f"❌ Cannot import audio_features: {e}")
    sys.exit(1)

try:
    from text_features import analyze_text
    print("✅ text_features loaded")
except ImportError as e:
    print(f"❌ Cannot import text_features: {e}")
    sys.exit(1)

try:
    from scorer import calculate_scores, generate_feedback
    print("✅ scorer loaded")
except ImportError as e:
    print(f"❌ Cannot import scorer: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# ── Load trained models ────────────────────────────────────────
clf_path = os.path.join(MODELS_DIR, "confidence_classifier.pkl")
reg_path = os.path.join(MODELS_DIR, "confidence_regressor.pkl")

if not os.path.exists(clf_path) or not os.path.exists(reg_path):
    print("⚠️  Models not found! Run training first:")
    print("    python training/generate_training_data.py")
    print("    python training/train_model.py")
    classifier = None
    regressor  = None
else:
    print("✅ Loading ML models...")
    classifier = joblib.load(clf_path)
    regressor  = joblib.load(reg_path)
    print("✅ Models loaded successfully!")

ML_FEATURES = [
    "speaking_rate", "pause_ratio", "pitch_mean", "pitch_std",
    "energy_mean",   "energy_std",  "filler_ratio", "sentiment",
    "avg_sent_length", "word_count",
]

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":        "running",
        "models_loaded": classifier is not None,
        "ml_service_dir": _THIS_DIR,
        "models_dir":     MODELS_DIR,
    })

@app.route("/predict", methods=["POST"])
def predict():
    audio_file = request.files.get("audio")
    transcript  = request.form.get("transcript", "")
    question_id = request.form.get("question_id", "tell_me_about_yourself")
    print(f"❓ Question ID: {question_id}")

    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400
    if not classifier or not regressor:
        return jsonify({"error": "Models not loaded. Run training scripts first."}), 500

    suffix = os.path.splitext(audio_file.filename)[-1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=_THIS_DIR) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # ── Step 1: Extract audio features ────────────────────
        print(f"🎵 Extracting audio features...")
        audio_feats = extract_features(tmp_path)
        print(f"   pitch={audio_feats['pitch_mean']} "
              f"energy={audio_feats['energy_mean']} "
              f"pause={audio_feats['pause_ratio']}")

        # ── Step 2: Extract text features ─────────────────────
        print(f"📝 Analyzing transcript ({len(transcript)} chars)...")
        text_feats = analyze_text(transcript, question_id)
        print(f"   words={text_feats['word_count']} "
              f"fillers={text_feats['filler_count']} "
              f"sentiment={text_feats['sentiment']}")

        # ── Step 3: Build ML feature vector ───────────────────
        feature_vector = np.array([[
            audio_feats["speaking_rate"],
            audio_feats["pause_ratio"],
            audio_feats["pitch_mean"],
            audio_feats["pitch_std"],
            audio_feats["energy_mean"],
            audio_feats["energy_std"],
            text_feats["filler_ratio"],
            text_feats["sentiment"],
            text_feats["avg_sent_length"],
            text_feats["word_count"],
        ]])

        # ── Step 4: ML Predictions ─────────────────────────────
        confidence_class = int(classifier.predict(feature_vector)[0])
        confidence_proba = classifier.predict_proba(feature_vector)[0].tolist()
        confidence_score = float(regressor.predict(feature_vector)[0])
        confidence_score = max(0, min(100, confidence_score))

        label = ["Low", "Medium", "High"][confidence_class]
        print(f"🤖 ML → class={label}, score={confidence_score:.1f}")

        # ── Step 5: Final scores + feedback ───────────────────
        scores   = calculate_scores(
            confidence_class, confidence_score,
            audio_feats, text_feats
        )
        feedback = generate_feedback(scores, audio_feats, text_feats)

        return jsonify({
            "scores":          scores,
            "audio_features":  audio_feats,
            "text_features":   text_feats,
            "confidence_probabilities": {
                "low":    round(confidence_proba[0], 3),
                "medium": round(confidence_proba[1], 3),
                "high":   round(confidence_proba[2], 3),
            },
            "feedback": feedback,
        })

    except Exception as e:
        print(f"❌ Error:\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    app.run(debug=False, port=8000)
