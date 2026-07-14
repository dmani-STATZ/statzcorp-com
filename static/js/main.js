/**
 * STATZ Corporation — Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {

  // ── MOBILE NAV TOGGLE ──────────────────────────────────────────────────────
  const navToggle = document.querySelector('.nav-toggle');
  const navMenu   = document.querySelector('.nav-menu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', function () {
      navMenu.classList.toggle('open');
      navToggle.classList.toggle('open');
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
        navMenu.classList.remove('open');
        navToggle.classList.remove('open');
      }
    });
  }

  // ── ACTIVE NAV ITEM ────────────────────────────────────────────────────────
  const currentPage = window.location.pathname.split('/').filter(Boolean).pop() || 'index.html';
  document.querySelectorAll('.nav-menu a').forEach(function (link) {
    const href = link.getAttribute('href').split('/').filter(Boolean).pop() || 'index.html';
    if (href === currentPage) {
      link.closest('li').classList.add('active');
    }
  });

  // ── HERO SLIDER ────────────────────────────────────────────────────────────
  const slider = document.getElementById('hero-slider');
  if (slider) {
    const slides = slider.querySelectorAll('.slide');

    // Single slide (or none): leave the first .active as-is; no arrows/dots/timer.
    if (slides.length >= 2) {
      const dots    = slider.querySelectorAll('.slider-dot');
      const prevBtn = slider.querySelector('.slider-arrow.prev');
      const nextBtn = slider.querySelector('.slider-arrow.next');
      let current   = 0;
      let timer;

      function goTo(index) {
        slides[current].classList.remove('active');
        dots[current] && dots[current].classList.remove('active');
        current = (index + slides.length) % slides.length;
        slides[current].classList.add('active');
        dots[current] && dots[current].classList.add('active');
      }

      function startAuto() {
        clearInterval(timer);
        timer = setInterval(function () { goTo(current + 1); }, 5000);
      }

      goTo(0);
      startAuto();

      if (prevBtn) prevBtn.addEventListener('click', function () { goTo(current - 1); startAuto(); });
      if (nextBtn) nextBtn.addEventListener('click', function () { goTo(current + 1); startAuto(); });

      dots.forEach(function (dot, i) {
        dot.addEventListener('click', function () { goTo(i); startAuto(); });
      });
    }
  }

  // ── BACK TO TOP ────────────────────────────────────────────────────────────
  const btt = document.getElementById('back-to-top');
  if (btt) {
    window.addEventListener('scroll', function () {
      btt.classList.toggle('visible', window.scrollY > 400);
    });
    btt.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ── CONTACT FORM ───────────────────────────────────────────────────────────
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();

      // Client-side validation
      let valid = true;
      contactForm.querySelectorAll('[required]').forEach(function (field) {
        if (!field.value.trim()) {
          field.classList.add('field-error');
          valid = false;
        } else {
          field.classList.remove('field-error');
        }
      });

      if (!valid) return;

      // Loading state
      const submitBtn = document.getElementById('submit-btn');
      const successEl = document.getElementById('form-success');
      const errorEl   = document.getElementById('form-error');

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending\u2026';
      }
      if (errorEl)   errorEl.style.display   = 'none';
      if (successEl) successEl.style.display = 'none';

      // Collect form data
      var payload = {
        name:    document.getElementById('contact-name').value.trim(),
        company: document.getElementById('contact-company').value.trim(),
        email:   document.getElementById('contact-email').value.trim(),
        phone:   document.getElementById('contact-phone').value.trim(),
        message: document.getElementById('contact-message').value.trim()
      };

      // POST to PHP handler
      fetch('php/send-mail.php', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload)
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          contactForm.reset();
          if (successEl) successEl.style.display = 'block';
          setTimeout(function () {
            if (successEl) successEl.style.display = 'none';
          }, 8000);
        } else {
          if (errorEl) {
            errorEl.textContent = data.message || 'Something went wrong. Please try again.';
            errorEl.style.display = 'block';
          }
        }
      })
      .catch(function () {
        if (errorEl) {
          errorEl.textContent = 'Network error. Please call us directly at 608-798-4500.';
          errorEl.style.display = 'block';
        }
      })
      .finally(function () {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Send Message';
        }
      });
    });
  }

  // ── SMOOTH SCROLL FOR ANCHOR LINKS ─────────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── SCROLL ANIMATION (fade-in on scroll) ───────────────────────────────────
  const animEls = document.querySelectorAll('.animate-on-scroll');
  if ('IntersectionObserver' in window && animEls.length) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    animEls.forEach(function (el) { observer.observe(el); });
  } else {
    animEls.forEach(function (el) { el.classList.add('in-view'); });
  }
});
