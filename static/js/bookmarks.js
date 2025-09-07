(function () {
  function toggleSection(id, btn) {
    var el = document.getElementById(id);
    if (!el) return;
    var collapsed = el.classList.toggle('is-collapsed');
    if (btn) {
      btn.setAttribute('aria-expanded', (!collapsed).toString());
      btn.textContent = collapsed ? 'Show' : 'Hide';
    }
  }

  function setup() {
    document.querySelectorAll('.btn-toggle').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var id = btn.getAttribute('data-target');
        toggleSection(id, btn);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();