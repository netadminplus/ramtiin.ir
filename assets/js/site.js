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
  // contact form: interim mailto flow (no backend yet) + Figma success state.
  var cform = document.querySelector('.contact-form');
  if (cform) cform.addEventListener('submit', function (e) {
    e.preventDefault();
    var val = function (n) { var el = cform.querySelector('[name="' + n + '"]'); return el ? el.value : ''; };
    var subject = val('your-subject') || 'تماس از وب‌سایت';
    var body = val('your-message') + '\n\n— ' + val('your-name') + (val('your-email') ? ' (' + val('your-email') + ')' : '');
    window.location.href = 'mailto:ramtin.rahmani@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    cform.innerHTML = '<div class="success-message"><span><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 4 4L19 6"/></svg></span><h3>پیام شما آماده ارسال شد.</h3><p>برنامه ایمیل شما باز شد. اگر باز نشد، مستقیم به ramtin.rahmani@gmail.com ایمیل بزنید.</p><button type="button" id="contact-again">ارسال پیام دیگر</button></div>';
    var again = document.getElementById('contact-again');
    if (again) again.addEventListener('click', function () { window.location.reload(); });
  });
});
