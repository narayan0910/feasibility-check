import React, { useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'feasibility_conversations_v1';
const AUTHOR_KEY = 'feasibility_author_id_v1';

const createAuthorId = () => `user_${Math.floor(Math.random() * 1000000)}`;

const parseAnalysisPayload = (analysis) => {
  if (!analysis) return { error: 'No analysis returned from backend.', raw: '' };

  try {
    return JSON.parse(analysis.replace('```json', '').replace('```', '').trim());
  } catch {
    try {
      return JSON.parse(analysis);
    } catch {
      return { error: 'LLM returned unstructured text.', raw: analysis };
    }
  }
};

const createConversation = (authorId) => ({
  local_id: crypto.randomUUID(),
  title: 'New Idea',
  appStep: 'initial',
  aiQuestion: '',
  reportData: null,
  loading: false,
  qaLoading: false,
  qaMessages: [],
  qaGraphMermaid: '',
  updatedAt: Date.now(),
  formData: {
    idea: '',
    user_name: '',
    ideal_customer: '',
    problem_solved: '',
    authorId,
    conversation_id: null,
    qaInput: '',
  },
});

function App() {
  const [authorId] = useState(() => {
    const existing = localStorage.getItem(AUTHOR_KEY);
    if (existing) return existing;
    const created = createAuthorId();
    localStorage.setItem(AUTHOR_KEY, created);
    return created;
  });

  const [conversations, setConversations] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [createConversation(authorId)];

      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || parsed.length === 0) return [createConversation(authorId)];

      return parsed.map((conv) => ({
        ...createConversation(authorId),
        ...conv,
        formData: {
          ...createConversation(authorId).formData,
          ...(conv.formData || {}),
          authorId,
        },
      }));
    } catch {
      return [createConversation(authorId)];
    }
  });

  const [activeConversationId, setActiveConversationId] = useState(() => {
    const first = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')[0];
    return first?.local_id || null;
  });

  const activeConversation = useMemo(
    () => conversations.find((c) => c.local_id === activeConversationId) || conversations[0],
    [conversations, activeConversationId]
  );

  useEffect(() => {
    if (!activeConversation && conversations.length > 0) {
      setActiveConversationId(conversations[0].local_id);
    }
  }, [activeConversation, conversations]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  const updateActiveConversation = (updater) => {
    if (!activeConversation) return;

    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.local_id !== activeConversation.local_id) return conv;
        const updated = typeof updater === 'function' ? updater(conv) : { ...conv, ...updater };
        return { ...updated, updatedAt: Date.now() };
      })
    );
  };

  const handleCreateConversation = () => {
    const next = createConversation(authorId);
    setConversations((prev) => [next, ...prev]);
    setActiveConversationId(next.local_id);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;

    updateActiveConversation((conv) => ({
      ...conv,
      formData: {
        ...conv.formData,
        [name]: value,
      },
      title:
        name === 'idea' && conv.appStep === 'initial' && value.trim()
          ? value.trim().slice(0, 45)
          : conv.title,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!activeConversation) return;

    updateActiveConversation({ loading: true });

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(activeConversation.formData),
      });

      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const data = await response.json();

      // Merge loading:false into the same update to avoid a race condition
      // where a separate finally-block update overwrites conversation_id.
      updateActiveConversation((conv) => {
        const nextForm = { ...conv.formData, conversation_id: data.conversation_id };

        if (data.response === 'Researching your idea...') {
          return {
            ...conv,
            loading: false,
            appStep: 'cross_question',
            aiQuestion: data.analysis,
            formData: { ...nextForm, idea: '' },
          };
        }

        return {
          ...conv,
          loading: false,
          appStep: 'report',
          reportData: parseAnalysisPayload(data.analysis),
          formData: nextForm,
        };
      });
    } catch (error) {
      console.error('Connection Error:', error);
      alert(`Backend Unavailable: ${error.message}`);
      updateActiveConversation({ loading: false });
    }
  };

  const handleSubmitQa = async (e) => {
    e.preventDefault();
    if (!activeConversation || !activeConversation.formData.qaInput.trim() || !activeConversation.formData.conversation_id) return;

    const question = activeConversation.formData.qaInput.trim();
    
    // Add user message to UI immediately
    updateActiveConversation((conv) => ({
      ...conv,
      qaMessages: [...conv.qaMessages, { role: 'user', content: question }],
      qaLoading: true,
      formData: { ...conv.formData, qaInput: '' }
    }));

    try {
      const response = await fetch('/api/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: activeConversation.formData.conversation_id,
          question: question
        }),
      });

      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const data = await response.json();

      // Merge qaLoading:false into the same update to prevent race
      updateActiveConversation((conv) => ({
        ...conv,
        qaLoading: false,
        qaMessages: [
          ...conv.qaMessages,
          {
            role: 'ai',
            content: data.answer,
            chunks: data.top_chunks,
            trace: data.trace,
          },
        ],
      }));
    } catch (error) {
      console.error('QA Error:', error);
      updateActiveConversation((conv) => ({
        ...conv,
        qaLoading: false,
        qaMessages: [...conv.qaMessages, { role: 'ai', content: `Error: ${error.message}` }],
      }));
    }
  };

  const handleLoadQaGraph = async () => {
    if (!activeConversation) return;
    try {
      const response = await fetch('/api/qa/graph');
      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const data = await response.json();
      updateActiveConversation({ qaGraphMermaid: data.mermaid || '' });
    } catch (error) {
      console.error('QA Graph Error:', error);
      alert(`Could not load QA graph: ${error.message}`);
    }
  };

  if (!activeConversation) return null;

  const { appStep, formData, aiQuestion, reportData, loading } = activeConversation;

  return (
    <div className="shell-layout">
      <aside className="sidebar card animate-in">
        <div className="sidebar-header">
          <h2>Ideas</h2>
          <button className="new-idea-btn" onClick={handleCreateConversation} type="button">
            + New Idea
          </button>
        </div>

        <div className="conversation-list">
          {conversations.map((conv) => (
            <button
              key={conv.local_id}
              className={`conversation-item ${conv.local_id === activeConversation.local_id ? 'active' : ''}`}
              onClick={() => setActiveConversationId(conv.local_id)}
              type="button"
            >
              <div className="conversation-title">{conv.title || 'New Idea'}</div>
              <div className="conversation-meta">{conv.appStep.replace('_', ' ')}</div>
            </button>
          ))}
        </div>
      </aside>

      <main className="main-content">
        <div className="app-container">
          <div className="card animate-in">
            <h1>Idea Feasibility</h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
              Evaluate your startup idea with multi-agent deep web research.
            </p>

            {appStep === 'initial' && (
              <form onSubmit={handleSubmit}>
                <div className="input-group">
                  <label>Idea Name / Concept</label>
                  <input
                    name="idea"
                    placeholder="e.g. AI-powered pet trainer"
                    value={formData.idea}
                    required
                    onChange={handleChange}
                  />
                </div>
                <div className="input-group">
                  <label>Your Name</label>
                  <input
                    name="user_name"
                    placeholder="Full Name"
                    value={formData.user_name}
                    required
                    onChange={handleChange}
                  />
                </div>
                <div className="input-group">
                  <label>Ideal Customer</label>
                  <input
                    name="ideal_customer"
                    placeholder="e.g. Busy pet owners"
                    value={formData.ideal_customer}
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
                    value={formData.problem_solved}
                    required
                    onChange={handleChange}
                  ></textarea>
                </div>
                <button type="submit" disabled={loading}>
                  {loading ? 'Initializing Agent...' : 'Start Analysis'}
                </button>
              </form>
            )}

            {appStep === 'cross_question' && (
              <div className="animate-in">
                <div className="ai-question">
                  <strong style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--primary)' }}>
                    Agent Clarification Needed:
                  </strong>
                  {aiQuestion}
                </div>

                <form onSubmit={handleSubmit}>
                  <div className="input-group">
                    <label>Your Reply</label>
                    <textarea
                      name="idea"
                      rows="4"
                      placeholder="Provide context for the agent..."
                      value={formData.idea}
                      onChange={handleChange}
                      required
                    />
                  </div>
                  <button type="submit" disabled={loading}>
                    {loading ? 'Compiling Report...' : 'Provide Context & Analyze'}
                  </button>
                </form>
              </div>
            )}

            {appStep === 'report' && (
              <div className="animate-in" style={{ textAlign: 'center', marginTop: '3rem' }}>
                <h2 style={{ color: 'var(--primary)' }}>Analysis Complete</h2>
                <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>
                  Review the detailed breakdown on the right pane.
                </p>
                <button
                  onClick={handleCreateConversation}
                  type="button"
                  style={{ marginTop: '2rem', background: 'transparent', border: '1px solid var(--glass-border)' }}
                >
                  Start New Analysis
                </button>
              </div>
            )}
          </div>

          <div className="result-section">
            {!loading && appStep === 'initial' && (
              <div className="card animate-in" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <p style={{ color: 'var(--text-muted)' }}>Fill in the details to deploy the feasibility agent.</p>
              </div>
            )}

            {loading && (
              <div className="card animate-in">
                <h2 style={{ marginBottom: '1rem' }}>
                  {appStep === 'initial' ? 'Evaluating Parameters...' : 'Running Deep Web Search & Market Analysis...'}
                </h2>
                <p style={{ color: 'var(--text-muted)' }}>This may take 15-30 seconds as the agent scrapes live data.</p>
                <div className="progress-bar-container">
                  <div className="progress-bar"></div>
                </div>
              </div>
            )}

            {!loading && appStep === 'cross_question' && (
              <div className="card animate-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤔</div>
                <h2>Awaiting Your Input</h2>
                <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  The agent requires clarification before it can execute the market scrape.
                </p>
              </div>
            )}

            {!loading && appStep === 'report' && reportData && !reportData.error && (
              <div className="card animate-in">
                <h2>Feasibility Dashboard</h2>

                <div className="dashboard-grid">
                  <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                    <div className="score-badge">{reportData.score}</div>
                  </div>

                  <div className="dashboard-card">
                    <div className="header">Idea Fit</div>
                    <div className="content">{reportData.idea_fit}</div>
                  </div>

                  <div className="dashboard-card">
                    <div className="header">Market Opportunity</div>
                    <div className="content">{reportData.opportunity}</div>
                  </div>

                  <div className="dashboard-card">
                    <div className="header">Targeting Focus</div>
                    <div className="content">{reportData.targeting}</div>
                  </div>

                  <div className="dashboard-card">
                    <div className="header">Competitor Landscape</div>
                    <div className="content">{reportData.competitors}</div>
                  </div>

                  <div className="dashboard-card">
                    <div className="header">Agent Reasoning Chain</div>
                    <ul style={{ marginLeft: '1.2rem', marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                      {reportData.chain_of_thought && reportData.chain_of_thought.map((step, idx) => (
                        <li key={idx} style={{ marginBottom: '0.5rem' }}>
                          {step}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="dashboard-card" style={{ borderColor: 'var(--secondary)' }}>
                    <div className="header" style={{ color: 'var(--secondary)' }}>
                      Recommended Next Step
                    </div>
                    <div className="content" style={{ fontWeight: '600' }}>
                      {reportData.next_step}
                    </div>
                  </div>
                </div>

                {/* ── Q&A RAG Chat Section ── */}
                <div style={{ marginTop: '2rem', borderTop: '1px solid var(--glass-border)', paddingTop: '2rem' }}>
                  <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Chat with your Report & Data</h3>
                  <div style={{ marginBottom: '1rem' }}>
                    <button
                      type="button"
                      onClick={handleLoadQaGraph}
                      style={{ width: 'auto', padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                    >
                      Load QA Graph
                    </button>
                  </div>

                  {activeConversation.qaGraphMermaid && (
                    <details style={{ marginBottom: '1rem' }}>
                      <summary style={{ cursor: 'pointer', color: 'var(--secondary)', fontWeight: 600 }}>
                        View QA Graph (Mermaid)
                      </summary>
                      <pre
                        style={{
                          whiteSpace: 'pre-wrap',
                          marginTop: '0.75rem',
                          padding: '0.75rem',
                          border: '1px solid var(--glass-border)',
                          borderRadius: '8px',
                          background: 'rgba(0,0,0,0.25)',
                          color: 'var(--text-muted)',
                          fontSize: '0.82rem',
                        }}
                      >
                        {activeConversation.qaGraphMermaid}
                      </pre>
                    </details>
                  )}
                  
                  <div className="qa-chat-box" style={{ 
                    maxHeight: '300px', 
                    overflowY: 'auto', 
                    marginBottom: '1rem',
                    padding: '1rem',
                    background: 'rgba(0,0,0,0.2)',
                    borderRadius: '8px'
                  }}>
                    {activeConversation.qaMessages.length === 0 ? (
                      <p style={{ color: 'var(--text-muted)', textAlign: 'center', margin: '2rem 0' }}>
                        Ask questions about the compiled data or competitors...
                      </p>
                    ) : (
                      activeConversation.qaMessages.map((msg, i) => (
                        <div key={i} style={{ 
                          marginBottom: '1rem', 
                          textAlign: msg.role === 'user' ? 'right' : 'left'
                        }}>
                          <div style={{
                            display: 'inline-block',
                            padding: '0.8rem 1rem',
                            borderRadius: '8px',
                            background: msg.role === 'user' ? 'rgba(97, 218, 251, 0.1)' : 'rgba(255,255,255,0.05)',
                            border: msg.role === 'user' ? '1px solid rgba(97, 218, 251, 0.3)' : '1px solid var(--glass-border)',
                            maxWidth: '90%',
                            whiteSpace: 'pre-wrap'
                          }}>
                            {msg.content}
                            {msg.chunks && msg.chunks.length > 0 && (
                               <details style={{ marginTop: '0.8rem', fontSize: '0.85em', color: 'var(--text-muted)' }}>
                                 <summary style={{ cursor: 'pointer', opacity: 0.8, fontWeight: 'bold' }}>View Sources ({msg.chunks.length})</summary>
                                 <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                   {msg.chunks.map((chunk, idx) => (
                                     <div key={idx} style={{ background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                       <div style={{ marginBottom: '0.2rem', color: 'var(--secondary)' }}><strong>Source:</strong> {chunk.source} ({chunk.score.toFixed(2)})</div>
                                       <div style={{ opacity: 0.8, fontStyle: 'italic' }}>{chunk.text.substring(0, 150)}...</div>
                                     </div>
                                   ))}
                                 </div>
                               </details>
                            )}
                            {msg.trace && msg.trace.length > 0 && (
                              <details style={{ marginTop: '0.8rem', fontSize: '0.85em', color: 'var(--text-muted)' }}>
                                <summary style={{ cursor: 'pointer', opacity: 0.8, fontWeight: 'bold' }}>
                                  View QA Trace ({msg.trace.length})
                                </summary>
                                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                  {msg.trace.map((step, idx) => (
                                    <div
                                      key={idx}
                                      style={{
                                        background: 'rgba(0,0,0,0.3)',
                                        padding: '0.5rem',
                                        borderRadius: '4px',
                                        border: '1px solid rgba(255,255,255,0.05)',
                                      }}
                                    >
                                      <div style={{ marginBottom: '0.2rem', color: 'var(--secondary)' }}>
                                        <strong>{step.step || `step_${idx + 1}`}</strong>
                                      </div>
                                      <div style={{ opacity: 0.85 }}>{step.message}</div>
                                    </div>
                                  ))}
                                </div>
                              </details>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                    {activeConversation.qaLoading && (
                      <div style={{ textAlign: 'left', color: 'var(--text-muted)' }}>
                        <span className="pulse">Agent is thinking...</span>
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleSubmitQa} style={{ display: 'flex', gap: '0.5rem' }}>
                    <input
                      name="qaInput"
                      placeholder="e.g. Which competitor has the lowest price?"
                      value={formData.qaInput || ''}
                      onChange={handleChange}
                      disabled={activeConversation.qaLoading}
                      style={{ flex: 1, padding: '0.8rem', borderRadius: '4px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                    />
                    <button 
                      type="submit" 
                      disabled={activeConversation.qaLoading || !formData.qaInput?.trim()}
                      style={{ width: 'auto', padding: '0 2rem' }}
                    >
                      Ask
                    </button>
                  </form>
                </div>
              </div>
            )}

            {!loading && appStep === 'report' && reportData && reportData.error && (
              <div className="card animate-in">
                <div className="dashboard-card" style={{ borderColor: 'red' }}>
                  <div className="header" style={{ color: 'red' }}>
                    {reportData.error}
                  </div>
                  <div className="content">{reportData.raw}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
