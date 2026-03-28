import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  LineChart,
  Line,
} from "recharts";

import {
  FiTrendingUp,
  FiTarget,
  FiBarChart2,
  FiZap,
  FiMic,
  FiActivity,
  FiCheckCircle,
  FiAlertCircle,
  FiMessageSquare,
  FiAward,
} from "react-icons/fi";

const scoreColor = (v) =>
  v >= 75 ? "#00f5a0" : v >= 50 ? "#f08c00" : "#ff4d4f";

const ScoreCard = ({ label, value, icon }) => (
  <div className="glass-card small">
    <div className="score-icon">{icon}</div>
    <div className="score-value" style={{ color: scoreColor(value) }}>
      {value}%
    </div>
    <div className="score-label">{label}</div>
  </div>
);

const Section = ({ title, children }) => (
  <div className="glass-card section">
    <h3 className="section-heading">{title}</h3>
    {children}
  </div>
);

export default function Dashboard({ results }) {
  const {
    transcript,
    scores,
    feedback,
    textFeatures,
    audioFeatures,
    confidenceProbabilities,
    audioDuration,
  } = results;

  const radarData = [
    { subject: "Confidence", value: scores.confidence },
    { subject: "Clarity", value: scores.clarity },
    { subject: "Fluency", value: scores.fluency },
    { subject: "Delivery", value: scores.delivery },
    { subject: "Grammar", value: scores.grammar },
    { subject: "Relevance", value: scores.relevance },
  ];

  const barData = [
    { name: "Words", value: textFeatures.word_count },
    { name: "Sentences", value: textFeatures.sentence_count },
    { name: "Fillers", value: textFeatures.filler_count },
    { name: "Pos Words", value: textFeatures.pos_word_count },
  ];

  const waveformData = (audioFeatures?.rms_values || []).map((v, i) => ({
    t: i,
    energy: v * 1000,
  }));

  return (
    <div className="dashboard">
      {/* OVERALL */}
      <div className="glass-card hero-score">
        <p className="muted">OVERALL SCORE</p>
        <h1 className="big-score">{scores.overall}%</h1>
        <p className="muted">
          {scores.confidence_label} · {scores.wpm} WPM · {audioDuration}s
        </p>
      </div>

      {/* SCORE GRID */}
      <div className="score-grid">
        <ScoreCard
          label="Confidence"
          value={scores.confidence}
          icon={<FiTrendingUp />}
        />
        <ScoreCard label="Clarity" value={scores.clarity} icon={<FiTarget />} />
        <ScoreCard
          label="Fluency"
          value={scores.fluency}
          icon={<FiActivity />}
        />
        <ScoreCard label="Delivery" value={scores.delivery} icon={<FiZap />} />
        <ScoreCard
          label="Grammar"
          value={scores.grammar}
          icon={<FiCheckCircle />}
        />
        <ScoreCard
          label="Relevance"
          value={scores.relevance}
          icon={<FiAward />}
        />
      </div>

      {/* CHARTS */}
      <div className="chart-grid">
        <Section title={<><FiBarChart2 /> Performance Radar</>}>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#333" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "#aaa" }} />
              <Radar
                dataKey="value"
                stroke="#00f5a0"
                fill="#00f5a0"
                fillOpacity={0.2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title={<><FiBarChart2 /> Speech Stats</>}>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="name" tick={{ fill: "#aaa" }} />
              <YAxis tick={{ fill: "#aaa" }} />
              <Tooltip />
              <Bar dataKey="value" fill="#00f5a0" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      {/* WAVEFORM */}
      {waveformData.length > 0 && (
        <Section title={<><FiActivity /> Voice Energy</>}>
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={waveformData}>
              <Line
                type="monotone"
                dataKey="energy"
                stroke="#00f5a0"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      )}

      {/* TRANSCRIPT */}
      <Section title={<><FiMessageSquare /> Transcript</>}>
        <p className="text">{transcript || "No transcript available"}</p>
      </Section>

      {/* FEEDBACK */}
      <Section title={<><FiTrendingUp /> AI Feedback</>}>
        {feedback.map((tip, i) => (
          <div key={i} className="tip">
            {tip}
          </div>
        ))}
      </Section>
    </div>
  );
}
