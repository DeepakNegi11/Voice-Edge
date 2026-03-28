from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import os, tempfile
from analyzer import (analyze_audio_features, analyze_text_features,
                      calculate_scores, generate_feedback)

app = Flask(__name__)
CORS(app)
recognizer = sr.Recognizer()

@app.route("/analyze", methods=["POST"])
def analyze():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file received"}), 400

    audio_file = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
        try:
            transcript = recognizer.recognize_google(audio_data)
        except:
            transcript = ""

        audio_feats = analyze_audio_features(tmp_path)
        text_feats = analyze_text_features(transcript) if transcript else {
            "word_count": 0, "filler_count": 0, "filler_ratio": 0,
            "sentiment": 0, "subjectivity": 0,
            "avg_sentence_length": 0, "sentence_count": 0
        }

        scores   = calculate_scores(audio_feats, text_feats)
        feedback = generate_feedback(scores, text_feats, audio_feats)

        return jsonify({
            "transcript":     transcript,
            "scores":         scores,
            "audio_features": audio_feats,
            "text_features":  text_feats,
            "feedback":       feedback
        })
    finally:
        os.unlink(tmp_path)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)