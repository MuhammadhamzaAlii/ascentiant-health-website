(function () {
  function track(eventName, params) {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params || {});
    }
  }

  document.querySelectorAll('a[href^="tel:"]').forEach(function (link) {
    link.addEventListener('click', function () {
      track('phone_click', {
        event_category: 'contact',
        event_label: link.getAttribute('href'),
        value: 1
      });
    });
  });

  document.querySelectorAll('a[href^="mailto:"]').forEach(function (link) {
    link.addEventListener('click', function () {
      track('email_click', {
        event_category: 'contact',
        event_label: link.getAttribute('href'),
        value: 1
      });
    });
  });

  document.querySelectorAll('a[href*="calendly.com"]').forEach(function (link) {
    link.addEventListener('click', function () {
      track('calendly_click', {
        event_category: 'contact',
        event_label: link.getAttribute('href'),
        value: 1
      });
    });
  });

  document.querySelectorAll('form[action*="formspree.io"]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var interest = form.querySelector('[name="subject"]');
      track('form_submit', {
        event_category: 'lead',
        event_label: interest ? interest.value : 'contact_form',
        value: 1
      });
    });
  });

  window.addEventListener('message', function (e) {
    if (e.origin !== 'https://calendly.com') return;
    if (e.data && e.data.event === 'calendly.event_scheduled') {
      track('calendly_booking', {
        event_category: 'lead',
        event_label: 'calendly_embed',
        value: 1
      });
    }
  });
})();
