// Helpers
function postJSON(url, data = {}, csrfToken) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken || getCSRF(),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify(data)
  });
}

function getCSRF() {
  const name = 'csrftoken';
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : '';
}

async function toggleSaved(slug, saved) {
  const url = saved ? `/jobs/${slug}/unsave/` : `/jobs/${slug}/save/`;
  const res = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': getCSRF() } });
  if (!res.ok) throw new Error('Save toggle failed');
}

// Modals
function openModalById(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.style.display = 'block';
  modal.setAttribute('aria-hidden', 'false');
}

function closeModalByEl(modal) {
  if (!modal) return;
  modal.style.display = 'none';
  modal.setAttribute('aria-hidden', 'true');
}

function closeAllModals() {
  document.querySelectorAll('.modal[aria-hidden="false"]').forEach(closeModalByEl);
}

// Quick Apply
function openQuickApply({ title, slug, applyHref }) {
  const modal = document.getElementById('quickApplyModal');
  if (!modal) return;
  const t = modal.querySelector('#qa-job-title');
  const h = modal.querySelector('#qa-title');
  const link = modal.querySelector('#qa-apply-link');
  if (t) t.textContent = title || '';
  if (h) h.textContent = 'Aplică rapid';
  // Prefer server-provided href if template added data-apply-href, else fallback
  const href = applyHref || (slug ? `/applications/apply/${slug}/` : '#');
  if (link) link.href = href;
  openModalById('quickApplyModal');
}

// Onboarding state
function getQAReady() {
  const el = document.getElementById('qa-state');
  return el && el.dataset && el.dataset.qar === '1';
}
function setQAReady(val) {
  const el = document.getElementById('qa-state');
  if (el) el.dataset.qar = val ? '1' : '0';
}
function openOnboarding() {
  openModalById('qa-onboarding');
}
async function submitOnboarding() {
  const modal = document.getElementById('qa-onboarding');
  if (!modal) return false;
  const endpoint = modal.getAttribute('data-endpoint');
  const loc = document.getElementById('qa-loc')?.value?.trim() || '';
  const skills = document.getElementById('qa-skills')?.value?.trim() || '';
  if (!loc || !skills) {
    alert('Completează locația și aptitudinile.');
    return false;
  }
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
    body: JSON.stringify({ location: loc, skills })
  });
  if (!res.ok) throw new Error('Onboarding failed');
  const data = await res.json();
  if (data.quick_apply_ready) {
    setQAReady(true);
    closeModalByEl(modal);
    return true;
  }
  return false;
}

// Single delegated click handler
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;

  const action = btn.getAttribute('data-action');

  if (action === 'save') {
    e.preventDefault();
    const slug = btn.getAttribute('data-slug');
    const isSaved = btn.getAttribute('data-saved') === '1';
    // optimistic UI
    btn.classList.toggle('saved', !isSaved);
    btn.setAttribute('data-saved', isSaved ? '0' : '1');
    const icon = btn.querySelector('.icon');
    if (icon) icon.textContent = isSaved ? '♡' : '♥';
    try {
      await toggleSaved(slug, isSaved);
    } catch (err) {
      // rollback on failure
      btn.classList.toggle('saved', isSaved);
      btn.setAttribute('data-saved', isSaved ? '1' : '0');
      if (icon) icon.textContent = isSaved ? '♥' : '♡';
      console.error(err);
      alert('Nu am putut salva jobul. Încearcă din nou.');
    }
    return;
  }

  if (action === 'quick-apply') {
    e.preventDefault();
    // If first time, gate with onboarding
    if (!getQAReady() && document.getElementById('qa-onboarding')) {
      openOnboarding();
      const saveBtn = document.getElementById('qa-save-continue');
      if (saveBtn) {
        const once = async () => {
          try {
            const ok = await submitOnboarding();
            if (ok) {
              openQuickApply({
                title: btn.getAttribute('data-title'),
                slug: btn.getAttribute('data-slug'),
                applyHref: btn.getAttribute('data-apply-href')
              });
            }
          } catch (err) {
            console.error(err);
            alert('Nu am putut salva. Încearcă din nou.');
          } finally {
            saveBtn.removeEventListener('click', once);
          }
        };
        // Add one-time listener
        saveBtn.addEventListener('click', once, { once: true });
      }
    } else {
      openQuickApply({
        title: btn.getAttribute('data-title'),
        slug: btn.getAttribute('data-slug'),
        applyHref: btn.getAttribute('data-apply-href')
      });
    }
    return;
  }

  if (action === 'modal-close') {
    e.preventDefault();
    const modal = e.target.closest('.modal');
    closeModalByEl(modal);
    return;
  }
});

// Optional: close modals on ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeAllModals();
});