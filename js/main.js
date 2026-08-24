(function () {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', nav.classList.contains('open'));
    });
  }

  document.querySelectorAll('.nav-dropdown-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var dropdown = btn.closest('.nav-dropdown');
      var isOpen = dropdown.classList.contains('open');
      document.querySelectorAll('.nav-dropdown').forEach(function (d) {
        d.classList.remove('open');
        var t = d.querySelector('.nav-dropdown-toggle');
        if (t) t.setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        dropdown.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  document.addEventListener('click', function () {
    document.querySelectorAll('.nav-dropdown').forEach(function (d) {
      d.classList.remove('open');
      var t = d.querySelector('.nav-dropdown-toggle');
      if (t) t.setAttribute('aria-expanded', 'false');
    });
  });

  document.querySelectorAll('.faq-q').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const answer = btn.nextElementSibling;
      const isOpen = answer.classList.contains('open');
      document.querySelectorAll('.faq-a').forEach(function (a) { a.classList.remove('open'); });
      document.querySelectorAll('.faq-q').forEach(function (q) {
        q.textContent = q.textContent.replace('−', '+');
      });
      if (!isOpen) {
        answer.classList.add('open');
        btn.textContent = btn.textContent.replace('+', '−');
      }
    });
  });

  document.querySelectorAll('input[type="tel"]').forEach(function (input) {
    input.addEventListener('input', function () {
      var numbers = this.value.replace(/\D/g, '').slice(0, 10);
      if (numbers.length > 6) {
        this.value = '(' + numbers.slice(0, 3) + ') ' + numbers.slice(3, 6) + '-' + numbers.slice(6);
      } else if (numbers.length > 3) {
        this.value = '(' + numbers.slice(0, 3) + ') ' + numbers.slice(3);
      } else if (numbers.length > 0) {
        this.value = '(' + numbers;
      }
    });
  });

  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
