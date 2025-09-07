window.PMS=(function(){const prefersDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;const root=document.documentElement;const current=localStorage.getItem('pms-theme')||(prefersDark?'dark':'light');root.setAttribute('data-theme',current);function toggleTheme(){const now=root.getAttribute('data-theme')==='light'?'dark':'light';root.setAttribute('data-theme',now);localStorage.setItem('pms-theme',now);}function toast(text,level='info'){const wrap=document.getElementById('toastContainer');const el=document.createElement('div');el.className='toast '+(level||'info');el.innerHTML=`<span>${text}</span><button class="btn-close" aria-label="Close">×</button>`;wrap.appendChild(el);const timer=setTimeout(()=>el.remove(),4500);el.addEventListener('click',(e)=>{if(e.target.closest('.btn-close')){clearTimeout(timer);el.remove();}});}document.addEventListener('DOMContentLoaded',()=>{const t=document.getElementById('themeToggle');if(t){t.addEventListener('click',toggleTheme);}});return{toggleTheme,toast};})();(function () {
  // simple toast stub may already exist
  window.PMS = window.PMS || {};
  PMS.toast = PMS.toast || function (t) { try { alert(t); } catch(e) {} };

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-toggle');
    if (!btn) return;
    const sel = btn.getAttribute('data-target');
    const el = document.querySelector(sel);
    if (!el) return;

    const collapsed = el.classList.toggle('is-collapsed');
    btn.setAttribute('aria-expanded', (!collapsed).toString());
    btn.textContent = collapsed ? 'Show' : 'Hide';
  }, false);
})();
