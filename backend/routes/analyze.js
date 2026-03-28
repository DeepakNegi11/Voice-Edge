const express = require("express");
const multer  = require("multer");
const axios   = require("axios");
const fs      = require("fs");
const FormData = require("form-data");
const router  = express.Router();

const ML_SERVICE_URL = "http://localhost:8000/predict";

// ── Multer storage ─────────────────────────────────────────────
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, "uploads/"),
  filename:    (req, file, cb) => {
    const unique = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, `recording-${unique}.webm`);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 25 * 1024 * 1024 },
});

// ── Upload audio to AssemblyAI ─────────────────────────────────
async function uploadAudio(filePath) {
  const fileData = fs.readFileSync(filePath);
  if (fileData.length < 1000) {
    throw new Error("Audio file too small — please record at least 5 seconds.");
  }
  const response = await axios({
    method:  "post",
    url:     "https://api.assemblyai.com/v2/upload",
    headers: { authorization: process.env.ASSEMBLYAI_API_KEY,
               "content-type": "application/octet-stream" },
    data:    fileData,
    maxBodyLength:    Infinity,
    maxContentLength: Infinity,
  });
  return response.data.upload_url;
}

// ── Request transcription ──────────────────────────────────────
async function requestTranscription(audioUrl) {
  const response = await axios.post(
    "https://api.assemblyai.com/v2/transcript",
    {
      audio_url:     audioUrl,
      speech_models: ["universal-2"],
      language_code: "en",
      punctuate: true,             
      format_text: true,
    },
    { headers: { authorization: process.env.ASSEMBLYAI_API_KEY } }
  );
  console.log("📨 AssemblyAI response:", response.data);
  return response.data.id;
}

// ── Poll for transcript result ─────────────────────────────────
async function pollTranscription(transcriptId) {
  const url = `https://api.assemblyai.com/v2/transcript/${transcriptId}`;
  for (let i = 0; i < 30; i++) {
    const { data } = await axios.get(url, {
      headers: { authorization: process.env.ASSEMBLYAI_API_KEY },
    });
    console.log(`🔄 Poll ${i + 1}: ${data.status}`);
    if (data.status === "completed") return data.text || "";
    if (data.status === "error")     throw new Error(`AssemblyAI: ${data.error}`);
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("Transcription timed out.");
}

// ── Call Python ML service ─────────────────────────────────────
async function callMLService(filePath, transcript, questionId) {
  const form = new FormData();
  form.append("audio",       fs.createReadStream(filePath));
  form.append("transcript",  transcript);
  form.append("question_id", questionId || "tell_me_about_yourself");

  const response = await axios.post(ML_SERVICE_URL, form, {
    headers: { ...form.getHeaders() },
    timeout: 60000,  // 60 seconds
  });
  return response.data;
}

// ── POST /api/analyze ──────────────────────────────────────────
router.post("/", upload.single("audio"), async (req, res) => {
  const filePath = req.file?.path;

  try {
    if (!req.file) {
      return res.status(400).json({ error: "No audio file received." });
    }

    console.log(`\n📁 File: ${filePath} | Size: ${req.file.size} bytes`);

    if (req.file.size < 1000) {
      return res.status(400).json({
        error: "Recording too short — please record at least 5 seconds.",
      });
    }

    // ── Step 1: Transcribe with AssemblyAI ──────────────────
    console.log("📤 Uploading to AssemblyAI...");
    const audioUrl     = await uploadAudio(filePath);

    console.log("🎙️ Requesting transcription...");
    const transcriptId = await requestTranscription(audioUrl);

    console.log("⏳ Waiting for transcript...");
    const transcript   = await pollTranscription(transcriptId);
    console.log("✅ Transcript:", transcript);

    // ── Step 2: Send to Python ML service ───────────────────
    console.log("🤖 Sending to ML service...");
    const questionId = req.body.questionId || "tell_me_about_yourself";
    console.log("❓ Question ID:", questionId);
    const mlResult = await callMLService(filePath, transcript, questionId);
    console.log("✅ ML scores:", mlResult.scores);

    // ── Step 3: Return full result to frontend ───────────────
    res.json({
      transcript,
      scores:                   mlResult.scores,
      audioFeatures:            mlResult.audio_features,
      textFeatures:             mlResult.text_features,
      confidenceProbabilities:  mlResult.confidence_probabilities,
      feedback:                 mlResult.feedback,
      audioDuration:            mlResult.audio_features?.duration || 0,
    });

  } catch (err) {
    console.error("❌ Error:", err.response?.data || err.message);

    // Give specific error if ML service is not running
    if (err.code === "ECONNREFUSED") {
      return res.status(500).json({
        error: "Python ML service is not running! Start it with: python ml_service/app.py"
      });
    }

    res.status(500).json({
      error: err.response?.data?.error || err.message || "Analysis failed."
    });

  } finally {
    if (filePath && fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      console.log("🗑️ Temp file deleted.");
    }
  }
});

module.exports = router;
