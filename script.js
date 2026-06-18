const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const humanizeBtn = document.getElementById('humanizeBtn');
const wordCount = document.getElementById('wordCount');
const outputBadge = document.getElementById('outputBadge');
const resultsBox = document.getElementById('resultsBox');

// Word counter
inputText.addEventListener('input', () => {
  const words = inputText.value.trim().split(/\s+/).filter(w => w.length > 0).length;
  wordCount.textContent = words + ' words';
});

async function startHumanize() {
  const text = inputText.value.trim();
  
  if (text.length < 20) {
    alert('⚠️ Please enter at least 20 characters');
    return;
  }
  
  if (text.length > 5000) {
    alert('⚠️ Text too long. Maximum 5000 characters.');
    return;
  }

  humanizeBtn.disabled = true;
  humanizeBtn.textContent = '⏳ Humanizing...';
  outputText.value = 'Processing... please wait 5-15 seconds';
  outputBadge.textContent = 'Processing...';
  outputBadge.style.color = '#2563eb';
  resultsBox.classList.add('hidden');

  try {
    const response = await fetch('/humanize-public', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to humanize');
    }

    // Show humanized text
    outputText.value = data.humanized;
    outputBadge.textContent = '✅ Done';
    outputBadge.style.color = '#16a34a';

    // Show stats
    resultsBox.classList.remove('hidden');
    
    const scoreDisplay = document.getElementById('scoreDisplay');
    const scoreLabel = document.getElementById('scoreLabel');
    const humanDisplay = document.getElementById('humanDisplay');
    const improveDisplay = document.getElementById('improveDisplay');
    
    scoreDisplay.textContent = data.final_ai_score + '%';
    humanDisplay.textContent = data.human_score + '%';
    
    const improvement = data.improvement;
    improveDisplay.textContent = (improvement > 0 ? '-' : '+') + Math.abs(improvement) + '%';
    
    if (data.final_ai_score <= 20) {
      scoreDisplay.style.color = '#16a34a';
      scoreLabel.textContent = '🟢 Human-like';
      scoreLabel.style.color = '#16a34a';
    } else if (data.final_ai_score <= 50) {
      scoreDisplay.style.color = '#ca8a04';
      scoreLabel.textContent = '🟡 Mostly Human';
      scoreLabel.style.color = '#ca8a04';
    } else {
      scoreDisplay.style.color = '#dc2626';
      scoreLabel.textContent = '🔴 Still AI-like';
      scoreLabel.style.color = '#dc2626';
    }
    
    humanDisplay.style.color = '#7c3aed';
    improveDisplay.style.color = improvement > 0 ? '#16a34a' : '#6b7280';
    
  } catch (error) {
    console.error('Error:', error);
    outputText.value = '';
    outputBadge.textContent = '❌ Failed';
    outputBadge.style.color = '#dc2626';
    alert('❌ Error: ' + error.message);
  } finally {
    humanizeBtn.disabled = false;
    humanizeBtn.textContent = '✨ Humanize Text';
  }
}

function clearInput() {
  inputText.value = '';
  outputText.value = '';
  wordCount.textContent = '0 words';
  outputBadge.textContent = 'Waiting...';
  outputBadge.style.color = '#6b7280';
  resultsBox.classList.add('hidden');
}

async function pasteText() {
  try {
    const text = await navigator.clipboard.readText();
    inputText.value = text;
    inputText.dispatchEvent(new Event('input'));
  } catch (e) {
    alert('Please paste manually using Ctrl+V');
  }
}

function copyOutput() {
  if (!outputText.value || outputText.value.includes('Processing')) {
    alert('⚠️ Nothing to copy yet!');
    return;
  }
  navigator.clipboard.writeText(outputText.value);
  alert('✅ Copied to clipboard!');
}

function downloadOutput() {
  if (!outputText.value || outputText.value.includes('Processing')) {
    alert('⚠️ Nothing to download yet!');
    return;
  }
  const blob = new Blob([outputText.value], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'humanized-text.txt';
  a.click();
  URL.revokeObjectURL(url);
}
