// ramtiin.ir static — vanilla JS for the Figma design behaviours.
document.addEventListener('DOMContentLoaded', function () {
  // mobile drawer (Figma: .overlay + .drawer with .is-open, body scroll lock)
  var drawer = document.querySelector('.drawer');
  var overlay = document.querySelector('.overlay');
  function openDrawer() {
    if (drawer) drawer.classList.add('is-open');
    if (overlay) overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
  function closeDrawer() {
    if (drawer) drawer.classList.remove('is-open');
    if (overlay) overlay.classList.remove('is-open');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-open-drawer]').forEach(function (b) {
    b.addEventListener('click', openDrawer);
  });
  document.querySelectorAll('[data-close-drawer]').forEach(function (b) {
    b.addEventListener('click', closeDrawer);
  });
  // desktop dropdowns: click toggles (touch), hover/focus handled by CSS
  document.querySelectorAll('.nav-drop').forEach(function (d) {
    var btn = d.querySelector('.nav-parent');
    if (!btn) return;
    btn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = d.classList.contains('is-open');
      document.querySelectorAll('.nav-drop.is-open').forEach(function (o) {
        o.classList.remove('is-open');
        var b = o.querySelector('.nav-parent');
        if (b) b.setAttribute('aria-expanded', 'false');
      });
      if (!open) {
        d.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', function () {
    document.querySelectorAll('.nav-drop.is-open').forEach(function (o) {
      o.classList.remove('is-open');
      var b = o.querySelector('.nav-parent');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  });
  // search modal (Figma: .search-modal with .open; the form submits to /search/?q=)
  var modal = document.querySelector('.search-modal');
  function openSearch() {
    if (!modal) return;
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    var i = modal.querySelector('input');
    if (i) i.focus();
  }
  function closeSearch() {
    if (!modal) return;
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-open-search]').forEach(function (b) {
    b.addEventListener('click', openSearch);
  });
  document.querySelectorAll('[data-close-search]').forEach(function (b) {
    b.addEventListener('click', closeSearch);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); closeSearch(); }
  });
  // generic copy buttons (donate wallet addresses)
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var done = function () { var t = b.textContent; b.textContent = 'کپی شد!'; setTimeout(function(){ b.textContent = t; }, 2000); };
      if (navigator.clipboard) navigator.clipboard.writeText(b.getAttribute('data-copy')).then(done);
      else { var ta = document.createElement('textarea'); ta.value = b.getAttribute('data-copy'); document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(); }
    });
  });
  // code blocks: a copy button on EVERY <pre> (design-system rule —
  // every code block on the blog must be copyable, no exceptions).
  document.querySelectorAll('pre').forEach(function (pre) {
    var wrap = document.createElement('div');
    wrap.className = 'codeblock';
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'copy-code';
    b.textContent = 'کپی';
    b.setAttribute('aria-label', 'کپی کد');
    b.addEventListener('click', function () {
      var text = pre.textContent.replace(/\n$/, '');
      var done = function () { b.textContent = 'کپی شد!'; setTimeout(function(){ b.textContent = 'کپی'; }, 2000); };
      var fallback = function () { var ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} document.body.removeChild(ta); done(); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    });
    wrap.appendChild(b);
});
});