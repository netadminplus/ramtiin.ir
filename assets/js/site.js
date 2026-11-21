// ramtiin.ir static — vanilla replacements for the Veen theme behaviours.
document.addEventListener('DOMContentLoaded', function () {
  var header = document.getElementById('header');
  function onScroll() {
    if (header) header.classList.toggle('is-sticky', window.scrollY > 10);
    var btt = document.getElementById('back-to-top');
    if (btt) btt.style.display = window.scrollY > 400 ? 'block' : 'none';
  }
  window.addEventListener('scroll', onScroll); onScroll();
  // mobile menu
  var burger = document.querySelector('.menu-mobile');
  if (burger) burger.addEventListener('click', function () {
    document.body.classList.toggle('menu-open');
    var nav = document.querySelector('#header nav.main-nav');
    if (nav) nav.classList.toggle('open');
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
});
