// ==========================================
// HUMANIZER PRO - WATERFALL EDITION
// ==========================================

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
  outputText.value = '🌊 Running waterfall: Light → Medium → Heavy...\nStopping as soon as AI score drops below 15%';

  try {
    const response = await fetch('/smart-humanize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text: text,
        target_ai: 15,
        max_loops: 3
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to humanize');
    }

    outputText.value = data.humanized;
    
    let attemptsLog = data.attempts.map(a => 
      `  Level ${a.level} (${a.method}): ${a.ai_score}% AI`
    ).join('\n');
    
    const stats = `✅ DONE!

📊 RESULTS:
   Original AI Score: ${data.original_ai_score}%
   Final AI Score:    ${data.final_ai_score}%
   Human Score:       ${data.human_score}%
   
🌊 WATERFALL ATTEMPTS:
${attemptsLog}

🏆 Best Method: ${data.best_method}
🎯 Target Reached: ${data.target_reached ? 'YES ✅' : 'NO (best returned)'}
💰 Tokens Used: ${data.tokens_used}`;
    
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

function copyOutput() {
  if (!outputText.value) {
    alert('Nothing to copy!');
    return;
  }
  navigator.clipboard.writeText(outputText.value);
  alert('✅ Copied!');
}

function clearInput() {
  inputText.value = '';
  outputText.value = '';
}

if (humanizeBtn) {
  humanizeBtn.addEventListener('click', startHumanize);
}
