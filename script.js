require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static('public'));

// Config
const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL;
const SAPLING_API_KEY = process.env.SAPLING_API_KEY;
const MAX_LOOPS = parseInt(process.env.MAX_LOOPS) || 10;
const TARGET_AI_SCORE = parseInt(process.env.TARGET_AI_SCORE) || 15;

// ==========================================
// HUMANIZER FUNCTION (calls your n8n)
// ==========================================
async function humanizeText(text) {
  try {
    const response = await axios.post(N8N_WEBHOOK_URL, {
      text: text
    }, {
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' }
    });
    
    // Try multiple possible response formats
    return response.data.humanized || 
           response.data.text || 
           response.data.output || 
           response.data.result ||
           (typeof response.data === 'string' ? response.data : null);
  } catch (error) {
    console.error('Humanizer error:', error.message);
    throw new Error('Humanizer service failed');
  }
}

// ==========================================
// AI DETECTOR 1: SAPLING (Primary)
// ==========================================
async function checkSapling(text) {
  try {
    const response = await axios.post(
      'https://api.sapling.ai/api/v1/aidetect',
      {
        key: SAPLING_API_KEY,
        text: text.substring(0, 2000) // Sapling free limit
      },
      { timeout: 15000 }
    );
    
    // Score is 0-1, convert to percentage
    return Math.round((response.data.score || 0) * 100);
  } catch (error) {
    console.error('Sapling failed:', error.message);
    return null;
  }
}

// ==========================================
// AI DETECTOR 2: ZEROGPT (Backup - Free)
// ==========================================
async function checkZeroGPT(text) {
  try {
    const response = await axios.post(
      'https://api.zerogpt.com/api/detect/detectText',
      { input_text: text },
      {
        timeout: 15000,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Mozilla/5.0'
        }
      }
    );
    
    return Math.round(response.data.data?.fakePercentage || 0);
  } catch (error) {
    console.error('ZeroGPT failed:', error.message);
    return null;
  }
}

// ==========================================
// SMART DETECTOR (Tries Sapling, falls back to ZeroGPT)
// ==========================================
async function detectAI(text) {
  let score = await checkSapling(text);
  let source = 'Sapling';
  
  if (score === null) {
    score = await checkZeroGPT(text);
    source = 'ZeroGPT';
  }
  
  if (score === null) {
    score = 50; // Default if both fail
    source = 'Unavailable';
  }
  
  return { score, source };
}

// ==========================================
// MAIN ENDPOINT: HUMANIZE WITH 10-LOOP
// ==========================================
app.post('/api/humanize', async (req, res) => {
  const { text } = req.body;
  
  if (!text || text.trim().length < 20) {
    return res.status(400).json({
      success: false,
      error: 'Text must be at least 20 characters'
    });
  }
  
  console.log(`\n🚀 Starting humanization (${text.length} chars)`);
  
  const attempts = [];
  let bestAttempt = null;
  let currentText = text;
  
  for (let i = 1; i <= MAX_LOOPS; i++) {
    console.log(`\n🔄 Attempt ${i}/${MAX_LOOPS}`);
    
    try {
      // Step 1: Humanize
      const humanized = await humanizeText(currentText);
      if (!humanized) {
        console.log('⚠️ Humanizer returned empty');
        continue;
      }
      
      // Step 2: Check AI score
      const { score, source } = await detectAI(humanized);
      console.log(`📊 AI Score: ${score}% (${source})`);
      
      const attempt = {
        attemptNumber: i,
        text: humanized,
        aiScore: score,
        source: source
      };
      
      attempts.push(attempt);
      
      // Track best attempt (lowest AI score)
      if (!bestAttempt || score < bestAttempt.aiScore) {
        bestAttempt = attempt;
      }
      
      // SUCCESS: AI score below target
      if (score <= TARGET_AI_SCORE) {
        console.log(`✅ Target reached! Stopping at attempt ${i}`);
        return res.json({
          success: true,
          finalText: humanized,
          aiScore: score,
          source: source,
          attempts: attempts.length,
          maxLoops: MAX_LOOPS,
          bestAttempt: i,
          targetReached: true,
          allAttempts: attempts
        });
      }
      
      // Use new text for next loop
      currentText = humanized;
      
    } catch (error) {
      console.error(`❌ Attempt ${i} failed:`, error.message);
    }
  }
  
  // After 10 loops, return BEST attempt
  if (bestAttempt) {
    console.log(`\n🏆 Returning best attempt: #${bestAttempt.attemptNumber} (${bestAttempt.aiScore}%)`);
    return res.json({
      success: true,
      finalText: bestAttempt.text,
      aiScore: bestAttempt.aiScore,
      source: bestAttempt.source,
      attempts: attempts.length,
      maxLoops: MAX_LOOPS,
      bestAttempt: bestAttempt.attemptNumber,
      targetReached: false,
      allAttempts: attempts
    });
  }
  
  return res.status(500).json({
    success: false,
    error: 'All attempts failed. Please try again.'
  });
});

// ==========================================
// HEALTH CHECK
// ==========================================
app.get('/api/health', (req, res) => {
  res.json({
    status: 'OK',
    service: 'Humanizer Pro',
    version: '1.0.0',
    maxLoops: MAX_LOOPS,
    targetScore: TARGET_AI_SCORE
  });
});

// Serve frontend
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`\n🚀 Humanizer Pro running on http://localhost:${PORT}`);
  console.log(`⚙️  Max loops: ${MAX_LOOPS} | Target AI score: ${TARGET_AI_SCORE}%\n`);
});
