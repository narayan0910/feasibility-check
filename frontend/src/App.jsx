import React, { useState } from 'react';

function App() {
  const [formData, setFormData] = useState({
    idea: '',
    user_name: '',
    ideal_customer: '',
    problem_solved: '',
    authorId: 'user_' + Math.floor(Math.random() * 1000),
    conversation_id: null
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const data = await response.json();
      setResult(data);
      setFormData(prev => ({ ...prev, conversation_id: data.conversation_id }));
    } catch (error) {
      console.error('Connection Error Details:', error);
      alert(`Backend Unavailable: ${error.message}. Checking port 8080...`);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="app-container">
      <div className="card">
        <h1>Idea Feasibility</h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
          Analyze your business idea with our AI agent using web research and market analysis.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Idea Name / Concept</label>
            <input 
              name="idea" 
              placeholder="e.g. AI-powered pet trainer" 
              required 
              onChange={handleChange}
            />
          </div>

          <div className="input-group">
            <label>Your Name</label>
            <input 
              name="user_name" 
              placeholder="Full Name" 
              required 
              onChange={handleChange}
            />
          </div>

          <div className="input-group">
            <label>Ideal Customer</label>
            <input 
              name="ideal_customer" 
              placeholder="e.g. Busy pet owners" 
              required 
              onChange={handleChange}
            />
          </div>

          <div className="input-group">
            <label>What Problem it Solves</label>
            <textarea 
              name="problem_solved" 
              rows="3" 
              placeholder="Describe the pain point..." 
              required 
              onChange={handleChange}
            ></textarea>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Analyzing...' : 'Start Analysis'}
          </button>
        </form>
      </div>

      <div className="result-section">
        {!result && !loading && (
          <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p style={{ color: 'var(--text-muted)' }}>Fill in the details to see the analysis</p>
          </div>
        )}

        {loading && (
          <div className="card">
            <div className="status-badge" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary)' }}>
              Agent working
            </div>
            <h2 style={{ marginBottom: '1rem' }}>Researching Market Trends...</h2>
            <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ 
                width: '60%', 
                height: '100%', 
                background: 'var(--gradient)', 
                animation: 'progress 2s infinite linear' 
              }}></div>
            </div>
            <style>{`
              @keyframes progress {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(200%); }
              }
            `}</style>
          </div>
        )}

        {result && (
          <div className="card">
            <div className="status-badge">Analysis Complete</div>
            <h2 style={{ marginBottom: '1.5rem' }}>Feasibility Report</h2>
            
            <div className="analysis-card" style={{ background: '#f8fafc', borderLeft: '4px solid var(--primary)' }}>
              <div className="analysis-header" style={{ color: 'var(--primary)', fontSize: '1rem' }}>AI Overview</div>
              <div className="analysis-content" style={{ fontSize: '0.9rem' }}>{result.response}</div>
            </div>

            {result.analysis && result.analysis.split(/\d\.\s/).filter(Boolean).map((section, index) => {
              const lines = section.trim().split('\n');
              const title = lines[0];
              const content = lines.slice(1).join('\n');
              
              return (
                <div key={index} className="analysis-card">
                  <div className="analysis-header">
                    {index + 1}. {title}
                  </div>
                  <div className="analysis-content">
                    {content}
                  </div>
                </div>
              );
            })}
            
            <p style={{ marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              Conversation ID: {result.conversation_id}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
