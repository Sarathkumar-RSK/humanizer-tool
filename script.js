const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const humanizeBtn = document.getElementById('humanizeBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const inputCount = document.getElementById('inputCount');
const outputCount = document.getElementById('outputCount');
const toast = document.getElementById('toast');
const btnText = humanizeBtn.querySelector('.btn-text');
const btnLoader = humanizeBtn.querySelector('.btn-loader');

let humanizedResult = '';

// Word counter
function countWords(text) {
    return text.trim() ? text.trim().split(/\s+/).length : 0;
}

inputText.addEventListener('input', () => {
    inputCount.textContent = `${countWords(inputText.value)} words`;
});

// Toast notification
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// Humanize button
humanizeBtn.addEventListener('click', async () => {
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
    humanizeBtn.disabled = true;
    outputText.innerHTML = '<div class="placeholder"><div class="spinner" style="width:40px;height:40px;margin-bottom:1rem;"></div><p>Humanizing your text...</p><small>This may take 30-60 seconds</small></div>';
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    
    try {
        const response = await fetch('/humanize-public', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        humanizedResult = data.humanized || data.content || data.text || '';
        
        outputText.textContent = humanizedResult;
        outputCount.textContent = `${countWords(humanizedResult)} words`;
        copyBtn.disabled = false;
        downloadBtn.disabled = false;
        showToast('✅ Text humanized successfully!');
        
    } catch (error) {
        console.error('Error:', error);
        outputText.innerHTML = `<div class="placeholder"><div class="placeholder-icon">❌</div><p>Something went wrong</p><small>${error.message}</small></div>`;
        showToast('❌ Failed to humanize. Try again.', 'error');
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        humanizeBtn.disabled = false;
    }
});

// Clear button
clearBtn.addEventListener('click', () => {
    inputText.value = '';
    inputCount.textContent = '0 words';
    outputText.innerHTML = '<div class="placeholder"><div class="placeholder-icon">🚀</div><p>Your humanized text will appear here</p><small>Click "Humanize Text" to start</small></div>';
    outputCount.textContent = '0 words';
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    humanizedResult = '';
    showToast('🗑️ Cleared');
});

// Copy button
copyBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(humanizedResult);
        showToast('📋 Copied to clipboard!');
    } catch (err) {
        showToast('❌ Failed to copy', 'error');
    }
});

// Download button
downloadBtn.addEventListener('click', () => {
    const blob = new Blob([humanizedResult], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `humanized-text-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('💾 Downloaded!');
});