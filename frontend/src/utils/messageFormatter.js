export function formatMessage(text) {
  if (!text) return '';
  
  let html = text;
  
  // Convert **bold** to <strong>
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  
  // Convert numbered lists
  html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="numbered-item">$2</li>');
  
  // Convert bullet points (*, •, -)
  const lines = html.split('\n');
  let inList = false;
  let result = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Bullet point
    if (/^[*•\-]\s+/.test(line)) {
      if (!inList) {
        result.push('<ul class="bullet-list">');
        inList = true;
      }
      const content = line.replace(/^[*•\-]\s+/, '');
      result.push(`<li>${content}</li>`);
    } 
    // Empty line
    else if (line === '') {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      result.push('<br/>');
    }
    // Heading (### or **)
    else if (line.startsWith('###') || /^\*\*[A-Z]/.test(line)) {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      const heading = line.replace(/^###\s*/, '').replace(/^\*\*|\*\*$/g, '');
      result.push(`<h4 class="message-heading">${heading}</h4>`);
    }
    // Regular paragraph
    else {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      if (line.length > 0) {
        result.push(`<p class="message-paragraph">${line}</p>`);
      }
    }
  }
  
  if (inList) {
    result.push('</ul>');
  }
  
  return result.join('');
}
