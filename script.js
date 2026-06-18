const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const humanizeBtn = document.getElementById('humanizeBtn');

async function startHumanize() {
  const text = inputText.value.trim();
  
  if (text.length < 20) {
    alert('Please enter at least 20 characters');
    return;
  }

  humanizeBtn.disabled = true;
  humanizeBtn.textContent = '⏳ Processing...';
  outputText.value = '🌊 Smart Waterfall: Light → Medium → Heavy\nStops when AI score < 15%';

  try {
    const response = await fetch('/smart-humanize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, target_ai: 15, max_loops: 3 })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to humanize');

    outputText.value = data.humanized;
    
    const log = data.attempts.map(a => 
      `   Attempt ${a.attempt} (${a.method}): ${a.ai_score}% AI`
    ).join('\n');
    
    alert(`✅ DONE!

📊 RESULTS:
   Original: ${data.original_ai_score}% AI
   Final:    ${data.final_ai_score}% AI
   Human:    ${data.human_score}%

🌊 ATTEMPTS (${data.total_attempts}/3):
${log}

🏆 Winner: ${data.best_method}
🎯 Target Reached: ${data.target_reached ? 'YES ✅' : 'NO (best returned)'}`);

  } catch (error) {
    outputText.value = '';
    alert('❌ Error: ' + error.message);
  } finally {
    humanizeBtn.disabled = false;
    humanizeBtn.textContent = '✨ Humanize Text';
  }
}

function copyOutput() {
  if (!outputText.value) { alert('Nothing to copy!'); return; }
  navigator.clipboard.writeText(outputText.value);
  alert('✅ Copied!');
}

function clearInput() {
  inputText.value = '';
  outputText.value = '';
}

if (humanizeBtn) humanizeBtn.addEventListener('click', startHumanize);
