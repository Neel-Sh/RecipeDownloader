// Auto-detect system theme
if (window.matchMedia) {
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  document.documentElement.classList.toggle('dark', media.matches);
  media.addEventListener('change', e => {
    document.documentElement.classList.toggle('dark', e.matches);
  });
}

// Dark mode toggle
const toggle = document.getElementById('theme-toggle');
if (toggle) {
  toggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    toggle.textContent = document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
  });
}

// === Servings scaling helpers ===
const FRACTIONS = { '¼': 0.25, '½': 0.5, '¾': 0.75, '⅓': 1/3, '⅔': 2/3 };
function strToFloat(str) {
  return FRACTIONS[str] !== undefined ? FRACTIONS[str] : parseFloat(str);
}
function floatToStr(num) {
  // Round to max 2 decimals; strip trailing zeros
  return parseFloat(num.toFixed(2)).toString();
}
function scaleLine(text, factor) {
  return text.replace(/(\d+(?:\.\d+)?|[¼½¾⅓⅔])/g, (m) => {
    const v = strToFloat(m);
    return isNaN(v) ? m : floatToStr(v * factor);
  });
}

// Step progress tracker
function updateStepProgress() {
  const total = document.querySelectorAll('#steps-section input[type="checkbox"]').length;
  const completed = document.querySelectorAll('#steps-section input[type="checkbox"]:checked').length;
  const percent = total ? (completed / total) * 100 : 0;
  const completedSpan = document.getElementById('steps-completed');
  const bar = document.getElementById('steps-progress');
  if (completedSpan && bar) {
    completedSpan.textContent = completed;
    bar.style.width = percent + '%';
  }
}

// Ingredient progress tracker
function updateIngredientProgress() {
  const total = document.querySelectorAll('#ingredients-section input[type="checkbox"]').length;
  const completed = document.querySelectorAll('#ingredients-section input[type="checkbox"]:checked').length;
  const percent = total ? (completed / total) * 100 : 0;
  document.getElementById('ingredients-completed').textContent = completed;
  document.getElementById('ingredients-progress').style.width = percent + '%';
}

document.addEventListener('DOMContentLoaded', () => {
  const ingrSection = document.getElementById('ingredients-section');
  const stepSection = document.getElementById('steps-section');
  if (stepSection) {
    const stepCbs = stepSection.querySelectorAll('input[type="checkbox"]');
    stepCbs.forEach(cb => cb.addEventListener('change', updateStepProgress));
    updateStepProgress();
  }
  if (ingrSection) {
    const ingrCbs = ingrSection.querySelectorAll('input[type="checkbox"]');
    ingrCbs.forEach(cb => cb.addEventListener('change', updateIngredientProgress));
    updateIngredientProgress();
  }
  
  // --- Servings slider setup ---
  const slider = document.getElementById('servings-range');
  const countSpan = document.getElementById('servings-count');
  const ingredTexts = document.querySelectorAll('.ingredient-text');
  ingredTexts.forEach(span => span.setAttribute('data-original', span.textContent.trim()));
  if (slider) {
    slider.addEventListener('input', () => {
      const factor = parseFloat(slider.value);
      countSpan.textContent = factor;
      ingredTexts.forEach(span => {
        const orig = span.getAttribute('data-original');
        span.textContent = scaleLine(orig, factor);
      });
    });
  }
});

// Grocery list export
document.addEventListener('DOMContentLoaded', () => {
  const copyBtn = document.getElementById('copy-ingredients');
  const dlBtn = document.getElementById('download-ingredients');

  function getIngredientsText() {
  return Array.from(document.querySelectorAll('#ingredients-section .ingredient-text'))
    .map(span => span.textContent.trim())
    .filter(txt => txt.length)
    .join('\n');
}

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const text = getIngredientsText();
      function showCopied(ok) {
        copyBtn.textContent = ok ? 'Copied!' : 'Press ⌘+C / Ctrl+C';
        setTimeout(() => copyBtn.textContent = 'Copy Ingredients', 2000);
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => showCopied(true))
          .catch(() => showCopied(false));
      } else {
        // Fallback for non‑secure contexts
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        try {
          const ok = document.execCommand('copy');
          showCopied(ok);
        } finally {
          document.body.removeChild(ta);
        }
      }
    });
  }

  if (dlBtn) {
    dlBtn.addEventListener('click', () => {
      const text = getIngredientsText();
      const blob = new Blob([text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ingredients.txt';
      a.click();
      URL.revokeObjectURL(url);
    });
  }
});

// Manage recent recipes in LocalStorage
function renderHistory() {
  const list = document.getElementById('recent-list');
  list.innerHTML = '';
  const recents = JSON.parse(localStorage.getItem('recentRecipes') || '[]');
  recents.forEach(url => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.textContent = url;
    btn.className = 'history-link';
    btn.type = 'button';
    btn.addEventListener('click', () => {
      const input = document.querySelector('input[name="url"]');
      input.value = url;
      input.focus();
    });
    li.appendChild(btn);
    list.appendChild(li);
  });
}

function addToHistory(url) {
  const key = 'recentRecipes';
  const max = 5;
  let recents = JSON.parse(localStorage.getItem(key) || '[]');
  // Remove duplicates
  recents = recents.filter(u => u !== url);
  recents.unshift(url);
  if (recents.length > max) recents = recents.slice(0, max);
  localStorage.setItem(key, JSON.stringify(recents));
  renderHistory();
}

document.addEventListener('DOMContentLoaded', () => {
  renderHistory();
  // On form submit, store URL
  const form = document.querySelector('form');
  const input = document.querySelector('input[name="url"]');
  form.addEventListener('submit', () => {
    const url = input.value.trim();
    if (url) addToHistory(url);
  });
  // Clear history
  const clearBtn = document.getElementById('clear-history');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      localStorage.removeItem('recentRecipes');
      renderHistory();
    });
  }
});

// Update Read All and individual step handlers to use SpeechSynthesis
document.addEventListener('DOMContentLoaded', () => {
  // Read all steps
  const readAllBtn = document.getElementById('read-all-steps');
  if (readAllBtn) {
    readAllBtn.addEventListener('click', () => {
      window.speechSynthesis.cancel();
      document.querySelectorAll('#steps-section .step-text').forEach(el => {
        const u = new SpeechSynthesisUtterance(el.textContent);
        window.speechSynthesis.speak(u);
      });
    });
  }
  // Read individual step
  document.querySelectorAll('.speak-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      window.speechSynthesis.cancel();
      const text = btn.parentElement.querySelector('.step-text').textContent;
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
    });
  });
  // Stop speech
  const stopBtn = document.getElementById('stop-reading');
  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      window.speechSynthesis.cancel();
    });
  }

  // Progress persistence
  const recipeMeta = document.getElementById('recipe-meta');
  if (recipeMeta) {
    const recipeKey = 'recipe-progress:' + recipeMeta.dataset.url;
    const ingrCbs = document.querySelectorAll('#ingredients-section input[type="checkbox"]');
    const stepCbs = document.querySelectorAll('#steps-section input[type="checkbox"]');
    // Load state
    const saved = JSON.parse(localStorage.getItem(recipeKey) || '{}');
    ingrCbs.forEach((cb,i) => {
      cb.checked = saved['ingr-' + i] || false;
      cb.addEventListener('change', saveProg);
    });
    stepCbs.forEach((cb,i) => {
      cb.checked = saved['step-' + i] || false;
      cb.addEventListener('change', saveProg);
    });
    function saveProg() {
      const state = {};
      ingrCbs.forEach((cb,i) => state['ingr-' + i] = cb.checked);
      stepCbs.forEach((cb,i) => state['step-' + i] = cb.checked);
      localStorage.setItem(recipeKey, JSON.stringify(state));
      updateStepProgress();
      updateIngredientProgress();
    }
    // Clear progress
    const clearBtn = document.getElementById('clear-progress');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        localStorage.removeItem(recipeKey);
        ingrCbs.forEach(cb => cb.checked = false);
        stepCbs.forEach(cb => cb.checked = false);
        updateStepProgress();
        updateIngredientProgress();
      });
    }
  }
});
