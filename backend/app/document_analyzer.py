import os
import json
from typing import Dict, List
import google.generativeai as genai

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class DocumentAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_bank_statement(self, text: str, filename: str) -> Dict:
        """
        Analyze bank statement text and return detailed analysis
        """
        prompt = f"""You are an expert visa document consultant analyzing a bank statement for US B1/B2 visa application.

DOCUMENT TEXT:
{text[:3000]}  # First 3000 chars to avoid token limits

ANALYSIS REQUIREMENTS:

1. **Period Coverage**: Check if 6 months are covered (mandatory)
2. **Bank Stamp**: Look for mentions of "attested", "stamp", "certified" (critical if missing)
3. **Income Pattern**: Check for regular salary deposits (consistency matters)
4. **Balance**: Evaluate if adequate ($3000-5000 USD = ₹2.5L-4L INR)
5. **Red Flags**: Large unusual deposits, cash withdrawals, suspicious patterns

Provide response in this EXACT JSON format:
{{
  "score": 75,
  "status": "needs_work",
  "issues": [
    {{
      "type": "error",
      "severity": "critical",
      "item": "Bank Stamp",
      "details": "Description of issue"
    }},
    {{
      "type": "warning",
      "severity": "high",
      "item": "Large Deposit",
      "details": "Description"
    }},
    {{
      "type": "success",
      "severity": "none",
      "item": "Balance",
      "details": "What's good"
    }}
  ],
  "summary": "One sentence overall assessment",
  "actions": [
    "Specific action item 1",
    "Specific action item 2"
  ]
}}

Scoring guide:
- 90-100: Excellent, ready to submit
- 70-89: Good, minor improvements needed
- 50-69: Needs work, fixable issues
- Below 50: High risk, major problems

Be specific and actionable. Focus on what WILL cause rejection.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            analysis = json.loads(result_text)
            return analysis
            
        except Exception as e:
            print(f"Analysis error: {e}")
            # Fallback analysis
            return {
                "score": 70,
                "status": "needs_review",
                "issues": [
                    {
                        "type": "warning",
                        "severity": "medium",
                        "item": "Analysis Error",
                        "details": "Could not fully analyze document. Please review manually."
                    }
                ],
                "summary": "Document uploaded successfully but detailed analysis unavailable.",
                "actions": [
                    "Review document manually for 6-month coverage",
                    "Ensure all pages are bank-stamped",
                    "Verify consistent income pattern"
                ]
            }
    
    def load_sample_analysis(self, sample_id: str) -> Dict:
        """Load pre-made sample analysis"""
        samples_file = '/Users/akshu/Project/VisaGuideAI/public/samples/sample_documents.json'
        
        try:
            with open(samples_file, 'r') as f:
                data = json.load(f)
            
            for doc in data['bank_statements']:
                if doc['id'] == sample_id:
                    return {
                        'filename': doc['name'],
                        'analysis': doc['analysis']
                    }
            
            return None
        except Exception as e:
            print(f"Error loading sample: {e}")
            return None

document_analyzer = DocumentAnalyzer()
