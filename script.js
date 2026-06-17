// ==========================================
// HUMANIZER PRO - FRONTEND SCRIPT
// ==========================================

const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const humanizeBtn = document.getElementById('humanizeBtn');

// ==========================================
// MAIN HUMANIZE FUNCTION
// ==========================================
async function startHumanize() {
  const text = inputText.value.trim();
  
  if (text.length < 20) {
    alert('Please enter at least 20 characters');
    return;
  }

  // Disable button
  humanizeBtn.disabled = true;
  humanizeBtn.textContent = '⏳ Processing... (10 loops)';
  outputText.value = 'Humanizing your text... Please wait 30-60 seconds...';

  try {
    const response = await fetch('/smart-humanize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text: text,
        target_ai: 20,
        max_loops: 10
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to humanize');
    }

    // Show result
    outputText.value = data.humanized;
    
    // Show stats
    const stats = `
✅ DONE!
📊 AI Score: ${data.final_ai_score}%
👤 Human Score: ${data.human_score}%
🔄 Attempts: ${data.total_attempts}/10
🎯 Target Reached: ${data.target_reached ? 'YES' : 'NO (best attempt returned)'}
    `;
    
    console.log(stats);
    alert(stats);

  } catch (error) {
    console.error('Error:', error);
    outputText.value = '';
    alert('❌ Error: ' + error.message);
  } finally {
    humanizeBtn.disabled = false;
    humanizeBtn.textContent = '✨ Humanize Text';
  }
}

// ==========================================
// COPY OUTPUT
// ==========================================
function copyOutput() {
  if (!outputText.value) {
    alert('Nothing to copy!');
    return;
  }
  navigator.clipboard.writeText(outputText.value);
  alert('✅ Copied!');
}

// ==========================================
// CLEAR INPUT
// ==========================================
function clearInput() {
  inputText.value = '';
  outputText.value = '';
}

// ==========================================
// ATTACH EVENT LISTENERS
// ==========================================
if (humanizeBtn) {
  humanizeBtn.addEventListener('click', startHumanize);
}
