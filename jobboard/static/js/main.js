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
  const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return m ? decodeURIComponent(m[2]) : '';
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
  const href = applyHref || (slug ? `/applications/apply/${slug}/` : '#');
  if (link) link.href = href;
  openModalById('quickApplyModal');
}

// Onboarding gate (A5)
function getQAReady() {
  const el = document.getElementById('qa-state');
  return el && el.dataset && el.dataset.qar === '1';
}
function setQAReady(val) {
  const el = document.getElementById('qa-state');
  if (el) el.dataset.qar = val ? '1' : '0';
}
async function submitOnboarding() {
  const modal = document.getElementById('qa-onboarding');
  if (!modal) return false;
  const endpoint = modal.getAttribute('data-endpoint');
  const loc = document.getElementById('qa-loc')?.value?.trim() || '';
  const skills = document.getElementById('qa-skills')?.value?.trim() || '';
  if (!loc || !skills) { alert('Completează locația și aptitudinile.'); return false; }
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
    body: JSON.stringify({ location: loc, skills })
  });
  if (!res.ok) throw new Error('Onboarding failed');
  const data = await res.json();
  if (data.quick_apply_ready) { setQAReady(true); closeModalByEl(modal); return true; }
  return false;
}

// Events
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const action = btn.getAttribute('data-action');

  if (action === 'save') {
    e.preventDefault();
    const slug = btn.getAttribute('data-slug');
    const isSaved = btn.getAttribute('data-saved') === '1';
    const icon = btn.querySelector('.icon');
    btn.classList.toggle('saved', !isSaved);
    btn.setAttribute('data-saved', isSaved ? '0' : '1');
    if (icon) icon.textContent = isSaved ? '♡' : '♥';
    try { await toggleSaved(slug, isSaved); }
    catch (err) {
      btn.classList.toggle('saved', isSaved);
      btn.setAttribute('data-saved', isSaved ? '1' : '0');
      if (icon) icon.textContent = isSaved ? '♥' : '♡';
      alert('Nu am putut salva jobul. Încearcă din nou.');
    }
    return;
  }

  if (action === 'quick-apply') {
    e.preventDefault();
    if (!getQAReady() && document.getElementById('qa-onboarding')) {
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
          } finally { saveBtn.removeEventListener('click', once); }
        };
        saveBtn.addEventListener('click', once, { once: true });
      }
      const ob = document.getElementById('qa-onboarding');
      if (ob) { ob.style.display = 'block'; ob.setAttribute('aria-hidden','false'); }
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
    closeModalByEl(e.target.closest('.modal'));
  }
});

// Employer inbox: inline status change
document.addEventListener('change', async (e) => {
  const select = e.target.closest('select.status-select[data-action="status-change"]');
  if (!select) return;
  const row = select.closest('tr[data-app-id]');
  const appId = row?.getAttribute('data-app-id');
  const newStatus = select.value;
  const wrap = document.getElementById('inbox-table');
  const endpoint = wrap?.getAttribute('data-endpoint');
  if (!appId || !endpoint) return;

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
      body: JSON.stringify({ id: appId, status: newStatus }),
    });
    if (!res.ok) throw new Error('Status update failed');
    const data = await res.json().catch(() => ({}));
    const pill = row.querySelector('.pill');
    if (data.status_label && pill) pill.textContent = data.status_label;
  } catch (err) {
    alert('Nu am putut actualiza statusul.');
  }
});

// Close modals on ESC
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAllModals(); });