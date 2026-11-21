// ramtiin.ir static — vanilla replacements for the Veen theme behaviours.
document.addEventListener('DOMContentLoaded', function () {
  var header = document.getElementById('header');
  function onScroll() {
    if (header) header.classList.toggle('is-sticky', window.scrollY > 10);
    var btt = document.getElementById('back-to-top');
    if (btt) btt.style.display = window.scrollY > 400 ? 'block' : 'none';
  }
  window.addEventListener('scroll', onScroll); onScroll();
  // mobile menu (side drawer, theme pattern: body.menu-open + overlay)
  var burger = document.querySelector('.menu-mobile');
  function closeMenu() { document.body.classList.remove('menu-open'); }
  if (burger) burger.addEventListener('click', function () {
    document.body.classList.toggle('menu-open');
  });
  var overlay = document.querySelector('.menu-overlay');
  if (overlay) overlay.addEventListener('click', closeMenu);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
  // drawer sub-menus: first tap expands, second tap follows the link
  document.querySelectorAll('nav.mobile.main-nav li.menu-item-has-children > a').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var li = a.parentElement;
      if (!li.classList.contains('open')) { e.preventDefault(); li.classList.add('open'); }
    });
  });
  // generic copy buttons (donate wallet addresses)
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var done = function () { var t = b.textContent; b.textContent = 'کپی شد!'; setTimeout(function(){ b.textContent = t; }, 2000); };
      if (navigator.clipboard) navigator.clipboard.writeText(b.getAttribute('data-copy')).then(done);
      else { var ta = document.createElement('textarea'); ta.value = b.getAttribute('data-copy'); document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(); }
    });
  });
  // search lightbox
  var lightbox = document.getElementById('search-lightbox');
  document.querySelectorAll('.epcl-search-button').forEach(function (b) {
    b.addEventListener('click', function (e) { e.preventDefault(); if (lightbox) { lightbox.classList.add('open'); var i = lightbox.querySelector('input'); if (i) i.focus(); } });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && lightbox) lightbox.classList.remove('open'); });
  if (lightbox) lightbox.addEventListener('click', function (e) { if (e.target === lightbox) lightbox.classList.remove('open'); });
  // back to top
  var btt = document.getElementById('back-to-top');
  if (btt) btt.addEventListener('click', function (e) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
  // copy permalink
  var copyBtn = document.querySelector('.permalink .copy');
  var copyInput = document.getElementById('copy-link');
  if (copyBtn && copyInput) copyBtn.addEventListener('click', function () {
    var done = function () { copyBtn.setAttribute('title', 'کپی شد!'); setTimeout(function(){ copyBtn.removeAttribute('title'); }, 2000); };
    if (navigator.clipboard) navigator.clipboard.writeText(copyInput.value).then(done);
    else { copyInput.select(); document.execCommand('copy'); done(); }
  });
  // show comments
  var showBtn = document.getElementById('show-comments');
  var comments = document.querySelector('.epcl-comments');
  function openComments() { if (comments) comments.classList.remove('hidden'); if (showBtn) showBtn.style.display = 'none'; }
  if (showBtn) showBtn.addEventListener('click', openComments);
  if (window.location.hash === '#show-comments') openComments();
  // any '#show-comments' anchor (card meta, post meta pill) opens the section
  document.querySelectorAll('a[href$="#show-comments"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault(); openComments();
      if (comments) comments.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
});
