import { useState } from "react";
import { useEffect } from "react";
import Recorder from "./components/Recorder";
import Dashboard from "./components/Dashboard";
import "./styles.css";
import Galaxy from "./components/Galaxy";
import Shuffle from "./components/shuffle";
import "./components/Shuffle.css";
import "./styles.css";

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="app">
      <Galaxy />

      <div className="aurora-wrap">
        <div className="aurora-blob blob-purple"></div>
        <div className="aurora-blob blob-indigo"></div>
        <div className="aurora-blob blob-violet"></div>
        <div className="aurora-blob blob-blue"></div>
        <div className="aurora-blob blob-cyan"></div>
        <div className="aurora-mask"></div>
      </div>

      {/* Navbar */}
      <div className="navbar">
        <Shuffle
          text="Voice Edge"
          className="logo"
          duration={0.5}
          stagger={0.04}
          ease="power3.out"
          shuffleDirection="right"
          triggerOnHover={true}
        />
      </div>

      {/* Hero */}
      <div className="hero">
        <h1>Master Your Interview Skills</h1>
        <p>AI-powered feedback on confidence, clarity & communication</p>
        <div className="glow"></div>
      </div>

      {/* Main */}
      <div className="container">
        <Recorder
          setResults={setResults}
          setLoading={setLoading}
          setError={setError}
        />

        {loading && (
          <div className="card center">⏳ Analyzing your response...</div>
        )}

        {error && !loading && <div className="error-box">❌ {error}</div>}

        {results && !loading && <Dashboard results={results} />}
      </div>
    </div>
  );
}
