import { useState, useRef } from "react";
import axios from "axios";

// ✅ FULL ORIGINAL QUESTIONS (unchanged)
const QUESTIONS = [
  {
    id: "tell_me_about_yourself",
    label: "Tell me about yourself",
    question: "Tell me about yourself and your background.",
    tip: "Cover your education, skills, and key experiences. Keep it to 90 seconds.",
  },
  {
    id: "greatest_strength",
    label: "Greatest Strength",
    question: "What is your greatest strength?",
    tip: "Pick one strong trait, back it up with a real example.",
  },
  {
    id: "greatest_weakness",
    label: "Greatest Weakness",
    question: "What is your greatest weakness?",
    tip: "Be honest but show you are actively working to improve it.",
  },
  {
    id: "why_this_role",
    label: "Why This Role?",
    question: "Why are you interested in this role?",
    tip: "Connect your skills and passion to what the role offers.",
  },
  {
    id: "where_five_years",
    label: "Where in 5 Years?",
    question: "Where do you see yourself in 5 years?",
    tip: "Show ambition but keep it realistic.",
  },
  {
    id: "challenging_situation",
    label: "Challenging Situation",
    question: "Describe a challenging situation and how you handled it.",
    tip: "Use STAR method.",
  },
  {
    id: "teamwork_example",
    label: "Teamwork Example",
    question: "Give an example of teamwork.",
    tip: "Focus on your contribution.",
  },
  {
    id: "why_should_hire",
    label: "Why Should We Hire You?",
    question: "Why should we hire you?",
    tip: "Highlight your unique value.",
  },
];

export default function Recorder({ setResults, setLoading, setError }) {
  const [recording, setRecording] = useState(false);
  const [audioURL, setAudioURL] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [timer, setTimer] = useState(0);
  const [selectedQuestion, setSelectedQuestion] = useState(QUESTIONS[0]);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    chunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (e) =>
      chunksRef.current.push(e.data);

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(chunksRef.current);
      setAudioBlob(blob);
      setAudioURL(URL.createObjectURL(blob));
    };

    mediaRecorderRef.current.start();
    setRecording(true);
    setTimer(0);

    timerRef.current = setInterval(() => setTimer((t) => t + 1), 1000);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    clearInterval(timerRef.current);
    setRecording(false);
  };

  const analyzeAudio = async () => {
    const formData = new FormData();
    formData.append("audio", audioBlob);
    formData.append("questionId", selectedQuestion.id);

    setLoading(true);
    setError(null);

    try {
      const res = await axios.post(
        "http://localhost:5000/api/analyze",
        formData
      );
      setResults({ ...res.data, questionLabel: selectedQuestion.question });
    } catch {
      setError("Server error");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setAudioURL(null);
    setAudioBlob(null);
    setTimer(0);
  };

  const formatTime = (s) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(
      2,
      "0"
    )}`;

  return (
    <div className="card">
      <h2 className="section-title"> Interview Practice</h2>

      {/* ✅ FULL QUESTION LIST (scrollable UI) */}
      <div className="question-list">
        {QUESTIONS.map((q) => (
          <button
            key={q.id}
            onClick={() => {
              setSelectedQuestion(q);
              reset();
            }}
            className={selectedQuestion.id === q.id ? "active" : ""}
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Question box */}
      <div className="question-box">
        <p>{selectedQuestion.question}</p>
        <span>{selectedQuestion.tip}</span>
      </div>

      {/* Recording */}
      {!recording ? (
        <button
          className={`btn green ${recording ? "recording" : ""}`}
          onClick={recording ? stopRecording : startRecording}
        >
          🎤 {recording ? "Recording..." : "Start Recording"}
        </button>
      ) : (
        <button className="btn red" onClick={stopRecording}>
          ⏹️ Stop Recording
        </button>
      )}

      {recording && <p className="rec">● REC {formatTime(timer)}</p>}

      {/* Audio */}
      {audioURL && (
        <div className="audio-box">
          <div className="audio-wrapper">
            <audio controls src={audioURL}></audio>
          </div>

          <div className="actions">
            <button className="btn blue" onClick={analyzeAudio}>
              Analyze
            </button>
            <button className="btn" onClick={reset}>
              Retry
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
