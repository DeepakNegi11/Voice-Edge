require("dotenv").config();
const express = require("express");
const cors    = require("cors");
const path    = require("path");
const fs      = require("fs");

const analyzeRoute = require("./routes/analyze");

const app  = express();
const PORT = process.env.PORT || 5000;

// ── Middleware ────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ── Create uploads folder if it doesn't exist ─────────────────
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

// ── Routes ────────────────────────────────────────────────────
app.use("/api/analyze", analyzeRoute);

app.get("/health", (req, res) => {
  res.json({ status: "Server is running ✅", port: PORT });
});

// ── Start server ──────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✅ Backend server running at http://localhost:${PORT}`);
  console.log(`🔑 AssemblyAI key loaded: ${process.env.ASSEMBLYAI_API_KEY ? "Yes" : "NO - check .env file!"}`);
});
