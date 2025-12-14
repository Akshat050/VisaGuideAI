import { useState } from 'react'
import axios from 'axios'
import './DocumentAnalyzer.css'

const API_URL = 'http://localhost:8000'

const SAMPLES = [
  { id: 'good', label: '✅ Good Example', description: 'Well-prepared statement (95/100)' },
  { id: 'medium', label: '⚠️ Needs Work', description: 'Common fixable issues (68/100)' },
  { id: 'poor', label: '❌ High Risk', description: 'Multiple problems (42/100)' }
]

function DocumentAnalyzer() {
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const analyzeSample = async (sampleId) => {
    setAnalyzing(true)
    setError(null)
    
    try {
      const { data } = await axios.get(`${API_URL}/api/samples/${sampleId}`)
      
      // Simulate analysis delay for effect
      setTimeout(() => {
        setResult(data)
        setAnalyzing(false)
      }, 1500)
      
    } catch (err) {
      setError('Failed to load sample')
      setAnalyzing(false)
    }
  }

  const analyzeFile = async (file) => {
    setAnalyzing(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const { data } = await axios.post(`${API_URL}/api/analyze-document`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      })
      
      setResult(data)
      setAnalyzing(false)
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
      setAnalyzing(false)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      analyzeFile(file)
    } else {
      setError('Please upload a PDF file')
    }
  }

  const getScoreColor = (score) => {
    if (score >= 90) return '#10b981'
    if (score >= 70) return '#f59e0b'
    return '#ef4444'
  }

  const getStatusLabel = (status) => {
    const labels = {
      'excellent': '✅ Excellent',
      'needs_work': '⚠️ Needs Work',
      'high_risk': '❌ High Risk',
      'needs_review': '⚠️ Needs Review'
    }
    return labels[status] || status
  }

  return (
    <div className="document-analyzer">
      <div className="analyzer-header">
        <h2>📄 Bank Statement Analyzer</h2>
        <p>Upload your bank statement or try a sample to see instant analysis</p>
      </div>

      {!result && !analyzing && (
        <div className="analyzer-options">
          <div className="samples-section">
            <h3>Try Sample Documents</h3>
            <div className="sample-buttons">
              {SAMPLES.map(sample => (
                <button
                  key={sample.id}
                  onClick={() => analyzeSample(sample.id)}
                  className="sample-button"
                >
                  <span className="sample-label">{sample.label}</span>
                  <span className="sample-desc">{sample.description}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="divider">
            <span>OR</span>
          </div>

          <div className="upload-section">
            <h3>Upload Your Document</h3>
            <div className="privacy-note">
              <span className="privacy-icon">🔒</span>
              <div>
                <strong>Privacy First</strong>
                <p>Your document is analyzed securely and not stored on our servers</p>
              </div>
            </div>
            <label className="file-upload">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
              />
              <span className="upload-button">
                📤 Choose PDF File
              </span>
            </label>
          </div>
        </div>
      )}

      {analyzing && (
        <div className="analyzing">
          <div className="spinner"></div>
          <h3>Analyzing your document...</h3>
          <p>Checking completeness, stamps, balance, and red flags</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <span>❌</span>
          <p>{error}</p>
          <button onClick={() => setError(null)}>Try Again</button>
        </div>
      )}

      {result && !analyzing && (
        <div className="analysis-result">
          <div className="result-header">
            <h3>{result.filename}</h3>
            <button onClick={() => setResult(null)} className="new-analysis">
              ← Analyze Another
            </button>
          </div>

          <div className="score-card">
            <div className="score-circle" style={{ borderColor: getScoreColor(result.analysis.score) }}>
              <div className="score-number">{result.analysis.score}</div>
              <div className="score-label">/ 100</div>
            </div>
            <div className="score-status">
              <div className="status-badge">{getStatusLabel(result.analysis.status)}</div>
              <p className="score-summary">{result.analysis.summary}</p>
            </div>
          </div>

          <div className="issues-section">
            <h4>Detailed Analysis</h4>
            <div className="issues-list">
              {result.analysis.issues.map((issue, idx) => (
                <div key={idx} className={`issue-item ${issue.type}`}>
                  <div className="issue-icon">
                    {issue.type === 'success' ? '✓' : issue.type === 'error' ? '✗' : '⚠'}
                  </div>
                  <div className="issue-content">
                    <div className="issue-title">{issue.item}</div>
                    <div className="issue-details">{issue.details}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {result.analysis.actions && result.analysis.actions.length > 0 && (
            <div className="actions-section">
              <h4>Action Items</h4>
              <ol className="actions-list">
                {result.analysis.actions.map((action, idx) => (
                  <li key={idx}>{action}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default DocumentAnalyzer
