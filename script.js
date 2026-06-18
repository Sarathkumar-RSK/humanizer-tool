const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const humanizeBtn = document.getElementById('humanizeBtn');
const wordCount = document.getElementById('wordCount');
const outputBadge = document.getElementById('outputBadge');
const resultsBox = document.getElementById('resultsBox');
const progressArea = document.getElementById('progressArea');
const progressBar = document.getElementById('progressBar');
const progressLabel = document.getElementById('progressLabel');
const progressAttempt = document.getElementById('progressAttempt');

// ==========================================
// WORD COUNTER
// ==========================================
inputText.addEventListener('input', () => {
  const text = inputText.value.trim();
  const words = text.length === 0 ? 0 : text.split(/\s+/).filter(w => w.length > 0).length;
  const chars = inputText.value.length;
  wordCount.textContent = `${words} words · ${chars}/5000`;

  if (chars > 5000) {
    wordCount.style.color = '#dc2626';
  } else if (chars > 4000) {
    wordCount.style.color = '#ca8a04';
  } else {
    wordCount.style.color = '#6b7280';
  }
});

// ==========================================
// PROGRESS SIMULATION
// ==========================================
let progressInterval = null;
let currentProgress = 0;
let currentPass = 1;

function startProgressSimulation() {
  currentProgress = 0;
  currentPass = 1;
  progressArea.classList.remove('hidden');
  progressBar.style.width = '0%';
  progressBar.style.background = 'linear-gradient(90deg, #6366f1, #8b5cf6)';
  updatePassDisplay(1);

  progressInterval = setInterval(() => {
    if (currentProgress < 15) {
      currentProgress += 2;
    } else if (currentProgress < 30) {
      currentProgress += 1;
    } else if (currentProgress < 50) {
      currentProgress += 0.8;
      if (currentProgress >= 35 && currentPass < 2) updatePassDisplay(2);
    } else if (currentProgress < 70) {
      currentProgress += 0.6;
      if (currentProgress >= 55 && currentPass < 3) updatePassDisplay(3);
    } else if (currentProgress < 85) {
      currentProgress += 0.4;
      if (currentProgress >= 70 && currentPass < 4) updatePassDisplay(4);
    } else if (currentProgress < 93) {
      currentProgress += 0.2;
      if (currentProgress >= 80 && currentPass < 5) updatePassDisplay(5);
    } else if (currentProgress < 97) {
      currentProgress += 0.1;
      if (currentProgress >= 90 && currentPass < 6) updatePassDisplay(6);
    }

    progressBar.style.width = currentProgress + '%';

    if (currentProgress > 60) {
      progressBar.style.background = 'linear-gradient(90deg, #8b5cf6, #06b6d4)';
    }
    if (currentProgress > 85) {
      progressBar.style.background = 'linear-gradient(90deg, #06b6d4, #10b981)';
    }
  }, 200);
}

function updatePassDisplay(pass) {
  currentPass = pass;
  progressAttempt.textContent = `Pass ${pass} of 6`;

  const step1 = document.getElementById('step1');
  const step2 = document.getElementById('step2');
  const step3 = document.getElementById('step3');

  if (pass <= 2) {
    progressLabel.textContent = '🔄 Standard Humanization...';
    step1.className = 'step active';
    step2.className = 'step';
    step3.className = 'step';
  } else if (pass <= 4) {
    progressLabel.textContent = '⚡ Aggressive Humanization...';
    step1.className = 'step done';
    step2.className = 'step active';
    step3.className = 'step';
  } else {
    progressLabel.textContent = '☢️ Nuclear Humanization...';
    step1.className = 'step done';
    step2.className = 'step done';
    step3.className = 'step active';
  }
}

function finishProgress(success) {
  clearInterval(progressInterval);

  if (success) {
    progressBar.style.width = '100%';
    progressBar.style.background = 'linear-gradient(90deg, #10b981, #06b6d4)';
    progressLabel.textContent = '✅ Complete!';
    document.getElementById('step1').className = 'step done';
    document.getElementById('step2').className = 'step done';
    document.getElementById('step3').className = 'step done';
  } else {
    progressBar.style.background = 'linear-gradient(90deg, #dc2626, #ef4444)';
    progressLabel.textContent = '❌ Failed';
  }

  setTimeout(() => {
    progressArea.classList.add('hidden');
  }, 2500);
}

// ==========================================
// MAIN HUMANIZE FUNCTION
// ==========================================
async function startHumanize() {
  const text = inputText.value.trim();

  if (text.length < 20) {
    showAlert('⚠️ Please enter at least 20 characters', 'warning');
    return;
  }
  if (text.length > 5000) {
    showAlert('⚠️ Text too long. Maximum 5000 characters.', 'warning');
    return;
  }

  // Reset UI
  humanizeBtn.disabled = true;
  humanizeBtn.innerHTML = '<span class="btn-spinner"></span> Processing...';
  outputText.value = '';
  outputBadge.textContent = 'Processing...';
  outputBadge.style.color = '#6366f1';
  resultsBox.classList.add('hidden');

  startProgressSimulation();

  try {
    const response = await fetch('/humanize-public', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to humanize text');
    }

    finishProgress(true);

    outputText.value = data.humanized;
    outputBadge.textContent = '✅ Done';
    outputBadge.style.color = '#16a34a';

    showResults(data);

    if (data.already_human) {
      showAlert('✅ Text was already human-like! Score: ' + data.original_ai_score + '%', 'success');
    } else {
      showAlert('✅ Done! Reduced AI score by ' + data.improvement + '% in ' + data.attempts_used + ' passes', 'success');
    }

  } catch (error) {
    console.error('Error:', error);
    finishProgress(false);
    outputText.value = '';
    outputBadge.textContent = '❌ Failed';
    outputBadge.style.color = '#dc2626';
    showAlert('❌ Error: ' + error.message, 'error');
  } finally {
    humanizeBtn.disabled = false;
    humanizeBtn.innerHTML = '✨ Humanize Text';
  }
}

// ==========================================
// SHOW RESULTS
// ==========================================
function showResults(data) {
  resultsBox.classList.remove('hidden');

  const originalScore = document.getElementById('originalScore');
  const scoreDisplay = document.getElementById('scoreDisplay');
  const scoreLabel = document.getElementById('scoreLabel');
  const humanDisplay = document.getElementById('humanDisplay');
  const improveDisplay = document.getElementById('improveDisplay');
  const attemptsDisplay = document.getElementById('attemptsDisplay');
  const targetDisplay = document.getElementById('targetDisplay');

  // Original score
  originalScore.textContent = data.original_ai_score + '%';
  setScoreColor(originalScore, data.original_ai_score);

  // Final AI score
  scoreDisplay.textContent = data.final_ai_score + '%';
  setScoreColor(scoreDisplay, data.final_ai_score);

  // Score label
  if (data.final_ai_score <= 15) {
    scoreLabel.textContent = '🟢 Excellent — Undetectable';
    scoreLabel.style.color = '#16a34a';
  } else if (data.final_ai_score <= 30) {
    scoreLabel.textContent = '🟢 Human-like';
    scoreLabel.style.color = '#16a34a';
  } else if (data.final_ai_score <= 50) {
    scoreLabel.textContent = '🟡 Mostly Human';
    scoreLabel.style.color = '#ca8a04';
  } else {
    scoreLabel.textContent = '🔴 Still AI-like';
    scoreLabel.style.color = '#dc2626';
  }

  // Human score
  humanDisplay.textContent = data.human_score + '%';
  humanDisplay.style.color = '#7c3aed';

  // Improvement
  const improvement = data.improvement;
  if (improvement > 0) {
    improveDisplay.textContent = '-' + improvement + '%';
    improveDisplay.style.color = '#16a34a';
  } else if (improvement < 0) {
    improveDisplay.textContent = '+' + Math.abs(improvement) + '%';
    improveDisplay.style.color = '#dc2626';
  } else {
    improveDisplay.textContent = '0%';
    improveDisplay.style.color = '#6b7280';
  }

  // Passes used
  if (data.already_human) {
    attemptsDisplay.textContent = '0 / 6';
    attemptsDisplay.style.color = '#16a34a';
    targetDisplay.textContent = '✅ Already human!';
    targetDisplay.style.color = '#16a34a';
  } else {
    const attempts = data.attempts_used;
    attemptsDisplay.textContent = attempts + ' / 6';
    attemptsDisplay.style.color = attempts <= 2 ? '#16a34a' : attempts <= 4 ? '#ca8a04' : '#dc2626';
    targetDisplay.textContent = data.target_reached ? '🎯 Target reached!' : '⚠️ Best result achieved';
    targetDisplay.style.color = data.target_reached ? '#16a34a' : '#ca8a04';
  }

  // Animate in
  resultsBox.style.opacity = '0';
  resultsBox.style.transform = 'translateY(10px)';
  setTimeout(() => {
    resultsBox.style.transition = 'all 0.4s ease';
    resultsBox.style.opacity = '1';
    resultsBox.style.transform = 'translateY(0)';
  }, 100);
}

// ==========================================
// HELPERS
// ==========================================
function setScoreColor(element, score) {
  if (score <= 20) {
    element.style.color = '#16a34a';
  } else if (score <= 50) {
    element.style.color = '#ca8a04';
  } else {
    element.style.color = '#dc2626';
  }
}

function showAlert(message, type = 'info') {
  const existing = document.querySelector('.custom-alert');
  if (existing) existing.remove();

  const alert = document.createElement('div');
  alert.className = `custom-alert alert-${type}`;
  alert.textContent = message;
  document.body.appendChild(alert);

  setTimeout(() => {
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 300);
  }, 3500);
}

function clearInput() {
  inputText.value = '';
  outputText.value = '';
  wordCount.textContent = '0 words · 0/5000';
  wordCount.style.color = '#6b7280';
  outputBadge.textContent = 'Waiting...';
  outputBadge.style.color = '#6b7280';
  resultsBox.classList.add('hidden');
  progressArea.classList.add('hidden');
}

async function pasteText() {
  try {
    const text = await navigator.clipboard.readText();
    inputText.value = text;
    inputText.dispatchEvent(new Event('input'));
  } catch (e) {
    showAlert('⚠️ Please paste manually using Ctrl+V', 'warning');
  }
}

function copyOutput() {
  if (!outputText.value) {
    showAlert('⚠️ Nothing to copy yet!', 'warning');
    return;
  }
  navigator.clipboard.writeText(outputText.value).then(() => {
    showAlert('✅ Copied to clipboard!', 'success');
  });
}

function downloadOutput() {
  if (!outputText.value) {
    showAlert('⚠️ Nothing to download yet!', 'warning');
    return;
  }
  const blob = new Blob([outputText.value], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'humanized-text.txt';
  a.click();
  URL.revokeObjectURL(url);
  showAlert('✅ Downloaded!', 'success');
}

// Ctrl+Enter shortcut
inputText.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    startHumanize();
  }
});
