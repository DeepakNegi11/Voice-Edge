// ── Filler words to detect ─────────────────────────────────────
const FILLER_WORDS = [
  "um", "uh", "like", "you know", "basically",
  "literally", "actually", "so", "right", "okay"
];

// ── Analyze the text transcript ────────────────────────────────
function analyzeText(transcript) {
  if (!transcript || transcript.trim() === "") {
    return {
      wordCount: 0,
      sentenceCount: 0,
      fillerCount: 0,
      fillerRatio: 0,
      avgSentenceLength: 0,
      sentiment: 0,
    };
  }

  const textLower = transcript.toLowerCase();
  const words = textLower.split(/\s+/).filter(Boolean);
  const wordCount = words.length;

  // Count filler words
  let fillerCount = 0;
  FILLER_WORDS.forEach((fw) => {
    const regex = new RegExp(`\\b${fw}\\b`, "gi");
    const matches = transcript.match(regex);
    if (matches) fillerCount += matches.length;
  });
  const fillerRatio = fillerCount / Math.max(wordCount, 1);

  // Count sentences
  const sentences = transcript
    .split(/[.!?]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const sentenceCount = sentences.length;
  const avgSentenceLength =
    sentences.reduce((sum, s) => sum + s.split(/\s+/).length, 0) /
    Math.max(sentenceCount, 1);

  // Simple sentiment: count positive vs negative words
  const positiveWords = [
    "good", "great", "excellent", "strong", "confident", "experienced",
    "skilled", "passionate", "motivated", "achieved", "successfully",
    "improved", "led", "built", "created", "developed",
  ];
  const negativeWords = [
    "bad", "weak", "failed", "nervous", "unsure", "difficult",
    "struggled", "problem", "issue", "mistake", "wrong",
  ];

  let posCount = 0, negCount = 0;
  words.forEach((w) => {
    if (positiveWords.includes(w)) posCount++;
    if (negativeWords.includes(w)) negCount++;
  });

  const sentiment =
    (posCount - negCount) / Math.max(posCount + negCount, 1);

  return {
    wordCount,
    sentenceCount,
    fillerCount,
    fillerRatio: parseFloat(fillerRatio.toFixed(3)),
    avgSentenceLength: parseFloat(avgSentenceLength.toFixed(1)),
    sentiment: parseFloat(sentiment.toFixed(3)),
  };
}

// ── Calculate scores from text features ───────────────────────
function calculateScores(textFeatures, audioDuration) {
  const {
    fillerRatio,
    avgSentenceLength,
    sentiment,
    wordCount,
  } = textFeatures;

  // Speaking pace: words per minute (ideal: 120–160 wpm)
  const wpm = audioDuration > 0
    ? (wordCount / audioDuration) * 60
    : 0;
  const paceScore = wpm === 0 ? 50
    : wpm < 80  ? 40
    : wpm < 120 ? 65
    : wpm < 170 ? 100
    : wpm < 200 ? 75
    : 50;

  // Confidence score
  const sentimentBonus = (sentiment + 1) * 10; // maps -1..1 → 0..20
  const fillerPenalty  = fillerRatio * 100;
  const confidence = Math.max(0, Math.min(100,
    40 + paceScore * 0.3 - fillerPenalty * 0.4 + sentimentBonus
  ));

  // Clarity score
  const idealLen = 15;
  const lengthScore = Math.max(
    0, 100 - Math.abs(avgSentenceLength - idealLen) * 3
  );
  const clarity = Math.max(0, Math.min(100,
    lengthScore * 0.6 + (1 - fillerRatio) * 40
  ));

  // Fluency score
  const fluency = Math.max(0, Math.min(100,
    paceScore * 0.6 + (1 - fillerRatio) * 40
  ));

  // Overall score
  const overall = parseFloat(
    (confidence * 0.4 + clarity * 0.3 + fluency * 0.3).toFixed(1)
  );

  return {
    confidence: parseFloat(confidence.toFixed(1)),
    clarity:    parseFloat(clarity.toFixed(1)),
    fluency:    parseFloat(fluency.toFixed(1)),
    overall,
    wpm:        parseFloat(wpm.toFixed(1)),
  };
}

// ── Generate feedback tips ─────────────────────────────────────
function generateFeedback(scores, textFeatures, audioDuration) {
  const tips = [];

  if (textFeatures.fillerRatio > 0.05) {
    tips.push("=> Reduce filler words like 'um', 'uh', 'like' — pause silently instead.");
  }
  if (scores.wpm > 180) {
    tips.push("=> You're speaking too fast — slow down so the interviewer can follow.");
  }
  if (scores.wpm < 90 && scores.wpm > 0) {
    tips.push("=> Try speaking a bit faster — a slow pace can seem hesitant.");
  }
  if (textFeatures.sentiment < 0) {
    tips.push("=> Use more positive and assertive language to sound confident.");
  }
  if (textFeatures.avgSentenceLength > 25) {
    tips.push("=> Break long sentences into shorter ones for better clarity.");
  }
  if (textFeatures.avgSentenceLength < 5 && textFeatures.wordCount > 0) {
    tips.push("=> Elaborate more — very short answers may seem underprepared.");
  }
  if (scores.confidence < 60) {
    tips.push("=> Use stronger, more assertive words to project confidence.");
  }
  if (audioDuration < 20 && textFeatures.wordCount > 0) {
    tips.push("=> Your answer was quite short — try to give more detail (aim for 1–2 min).");
  }
  if (tips.length === 0) {
    tips.push("=> Great job! Your communication was clear, confident, and well-structured.");
  }

  return tips;
}

module.exports = { analyzeText, calculateScores, generateFeedback };