const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const actionBtn = document.getElementById('actionBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const inputCount = document.getElementById('inputCount');
const outputCount = document.getElementById('outputCount');
const toast = document.getElementById('toast');
const btnText = actionBtn.querySelector('.btn-text');
const btnLoader = actionBtn.querySelector('.btn-loader');
const loaderText = document.getElementById('loaderText');
const scoreDisplay = document.getElementById('scoreDisplay');
const originalScore = document.getElementById('originalScore');
const finalScore = document.getElementById('finalScore');
const attemptsDisplay = document.getElementById('attemptsDisplay');
const modeBtns = document.querySelectorAll('.mode-btn');

let currentMode = 'smart';
let resultText = '';

// Mode switching
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentMode = btn.dataset.mode;
        
        if (currentMode === 'smart') {
            btnText.textContent = '🚀 Smart Humanize';
        } else if (currentMode === 'humanize') {
            btnText.textContent = '✨ Humanize';
        } else {
            btnText.textContent = '🔍 Detect AI';
        }
    });
});

// Word counter
function countWords(text) {
    return text.trim() ? text.trim().split(/\s+/).length : 0;
}

inputText.addEventListener('input', () => {
    inputCount.textContent = `${countWords(inputText.value)} words`;
});

function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

function getScoreColor(score) {
    if (score <= 20) return 'good';
    if (score <= 50) return 'medium';
    return 'bad';
}

// Main action button
actionBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    
    if (!text) {
        showToast('⚠️ Please enter some text first', 'error');
        return;
    }
    
    if (text.length < 50) {
        showToast('⚠️ Text too short. Minimum 50 characters.', 'error');
        return;
    }
    
    // Show loading
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';
    actionBtn.disabled = true;
    scoreDisplay.style.display = 'none';
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    
    try {
        let endpoint = '';
        let body = {};
        
        if (currentMode === 'smart') {
            endpoint = '/smart-humanize';
            body = { text: text, target_ai: 20, max_loops: 5 };
            loaderText.textContent = 'Smart processing... (may take 1-2 min)';
            outputText.innerHTML = '<div class="placeholder"><div class="spinner" style="width:40px;height:40px;margin-bottom:1rem;"></div><p>Auto-humanizing your text...</p><small>Looping until AI score is low</small></div>';
        } else if (currentMode === 'humanize') {
            endpoint = '/humanize-public';
            body = { text: text };
            loaderText.textContent = 'Humanizing... (30-60 sec)';
            outputText.innerHTML = '<div class="placeholder"><div class="spinner" style="width:40px;height:40px;margin-bottom:1rem;"></div><p>Humanizing your text...</p></div>';
        } else {
            endpoint = '/detect';
            body = { text: text };
            loaderText.textContent = 'Detecting...';
            outputText.innerHTML = '<div class="placeholder"><div class="spinner" style="width:40px;height:40px;margin-bottom:1rem;"></div><p>Analyzing text...</p></div>';
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (currentMode === 'detect') {
            // Show detection result
            resultText = `AI Score: ${data.ai_score}%\nHuman Score: ${data.human_score}%\nVerdict: ${data.verdict}`;
            outputText.innerHTML = `
                <div style="text-align:center;padding:2rem;">
                    <div style="font-size:5rem;margin-bottom:1rem;">${data.ai_score > 60 ? '🤖' : data.ai_score > 30 ? '🧐' : '👤'}</div>
                    <h2 style="font-size:3rem;color:${data.ai_score > 60 ? '#ef4444' : data.ai_score > 30 ? '#f59e0b' : '#10b981'};">${data.ai_score}%</h2>
                    <p style="font-size:1.2rem;margin-top:1rem;">${data.verdict}</p>
                    <p style="color:rgba(255,255,255,0.6);margin-top:0.5rem;">Human Score: ${data.human_score}%</p>
                </div>
            `;
            showToast(`✅ Detected: ${data.verdict}`);
        } else if (currentMode === 'humanize') {
            resultText = data.humanized;
            outputText.textContent = resultText;
            outputCount.textContent = `${countWords(resultText)} words`;
            
            // Show score
            scoreDisplay.style.display = 'block';
            originalScore.textContent = '~95%';
            finalScore.textContent = `${data.ai_score}%`;
            finalScore.className = `score-value ${getScoreColor(data.ai_score)}`;
            attemptsDisplay.innerHTML = '';
            
            showToast(`✅ Humanized! AI score: ${data.ai_score}%`);
        } else {
            // Smart mode
            resultText = data.humanized;
            outputText.textContent = resultText;
            outputCount.textContent = `${countWords(resultText)} words`;
            
            // Show scores
            scoreDisplay.style.display = 'block';
            originalScore.textContent = `${data.original_ai_score}%`;
            finalScore.textContent = `${data.final_ai_score}%`;
            finalScore.className = `score-value ${getScoreColor(data.final_ai_score)}`;
            
            // Show attempts
            let attemptsHTML = '<div class="attempts-list"><h4>📊 Attempt History:</h4>';
            data.attempts.forEach(a => {
                const color = getScoreColor(a.ai_score);
                attemptsHTML += `<div class="attempt-item ${color}">Attempt ${a.attempt}: ${a.ai_score}% AI</div>`;
            });
            attemptsHTML += `<div style="margin-top:0.8rem;color:${data.target_reached ? '#10b981' : '#f59e0b'};font-weight:600;">${data.target_reached ? '✅ Target reached!' : '⚠️ Max attempts reached'}</div>`;
            attemptsHTML += '</div>';
            attemptsDisplay.innerHTML = attemptsHTML;
            
            showToast(`✅ Done! Final AI score: ${data.final_ai_score}%`);
        }
        
        copyBtn.disabled = false;
        downloadBtn.disabled = false;
        
    } catch (error) {
        console.error('Error:', error);
        outputText.innerHTML = `<div class="placeholder"><div class="placeholder-icon">❌</div><p>Something went wrong</p><small>${error.message}</small></div>`;
        showToast('❌ Failed. Try again.', 'error');
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        actionBtn.disabled = false;
    }
});

clearBtn.addEventListener('click', () => {
    inputText.value = '';
    inputCount.textContent = '0 words';
    outputText.innerHTML = '<div class="placeholder"><div class="placeholder-icon">🚀</div><p>Result will appear here</p><small>Click button to start</small></div>';
    outputCount.textContent = '0 words';
    scoreDisplay.style.display = 'none';
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    resultText = '';
    showToast('🗑️ Cleared');
});

copyBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(resultText);
        showToast('📋 Copied!');
    } catch (err) {
        showToast('❌ Copy failed', 'error');
    }
});

downloadBtn.addEventListener('click', () => {
    const blob = new Blob([resultText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `result-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('💾 Downloaded!');
});
