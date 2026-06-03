/**
 * Base JavaScript - Global functionality
 * - Lucide icons initialization
 * - GSAP animations
 * - Toast notifications
 */

(function() {
  'use strict';

  // =========================================
  // LUCIDE ICONS INITIALIZATION
  // =========================================
  function initLucideIcons() {
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  }

  // =========================================
  // GSAP ANIMATIONS
  // =========================================
  function initGSAPAnimations() {
    if (typeof gsap === 'undefined') return;

    // Register ScrollTrigger plugin
    if (typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);
    }

    // Все анимации отключены - они вызывают мерцание при переходах между страницами
  }

  // =========================================
  // TOAST NOTIFICATIONS
  // =========================================
  function initToastClose() {
    document.querySelectorAll('.toast-close').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var toast = this.closest('.toast');
        var wrap = document.querySelector('.toast-wrap');
        
        // Animate out
        if (toast && typeof gsap !== 'undefined') {
          gsap.to(toast, {
            x: 100,
            opacity: 0,
            duration: 0.3,
            ease: 'power2.in',
            onComplete: function() {
              toast.remove();
              if (wrap && !wrap.querySelector('.toast')) wrap.remove();
            }
          });
        } else {
          if (toast) toast.remove();
          if (wrap && !wrap.querySelector('.toast')) wrap.remove();
        }
      });
    });

    // Auto-hide toasts after 5 seconds
    document.querySelectorAll('.toast').forEach(function(toast) {
      setTimeout(function() {
        if (toast && toast.parentNode) {
          if (typeof gsap !== 'undefined') {
            gsap.to(toast, {
              x: 100,
              opacity: 0,
              duration: 0.3,
              ease: 'power2.in',
              onComplete: function() {
                toast.remove();
                var wrap = document.querySelector('.toast-wrap');
                if (wrap && !wrap.querySelector('.toast')) wrap.remove();
              }
            });
          } else {
            toast.remove();
            var wrap = document.querySelector('.toast-wrap');
            if (wrap && !wrap.querySelector('.toast')) wrap.remove();
          }
        }
      }, 5000);
    });
  }

  // =========================================
  // SMOOTH SCROLL FOR ANCHOR LINKS
  // =========================================
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          
          if (typeof gsap !== 'undefined') {
            gsap.to(window, {
              duration: 0.8,
              scrollTo: {
                y: target,
                offsetY: 80
              },
              ease: 'power2.inOut'
            });
          } else {
            target.scrollIntoView({
              behavior: 'smooth',
              block: 'start'
            });
          }
        }
      });
    });
  }

  // =========================================
  // BUTTON RIPPLE EFFECT
  // =========================================
  function initButtonEffects() {
    document.querySelectorAll('.btn').forEach(btn => {
      btn.addEventListener('click', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const ripple = document.createElement('span');
        ripple.className = 'btn-ripple';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
      });
    });
  }

  // =========================================
  // NAVBAR FOCUS FIX
  // =========================================
  function initNavbarFocusFix() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    // Remove focus from all navbar elements on click
    navbar.addEventListener('click', function(e) {
      // Use setTimeout to run after browser's focus handling
      setTimeout(function() {
        if (document.activeElement) {
          document.activeElement.blur();
        }
      }, 0);
    });
  }

  // =========================================
  // SMOOTH PAGE TRANSITIONS
  // =========================================
  function initSmoothPageTransitions() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    // Находим все ссылки навбара (исключаем якоря и внешние ссылки)
    const navLinks = navbar.querySelectorAll('a[href]:not([href^="#"]):not([href^="http"]):not([target="_blank"])');
    
    navLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        
        // Пропускаем если это текущая страница
        if (href === window.location.pathname || href === window.location.href) {
          e.preventDefault();
          return;
        }

        // Пропускаем если ссылка ведет на внешний ресурс
        if (href.startsWith('http') || href.startsWith('//')) {
          return;
        }

        e.preventDefault();
        
        const mainContent = document.querySelector('.main-content');
        
        if (mainContent && typeof gsap !== 'undefined') {
          // GSAP анимация ухода - только opacity
          gsap.to(mainContent, {
            opacity: 0,
            duration: 0.15,
            ease: 'power2.out',
            onComplete: function() {
              window.location.href = href;
            }
          });
        } else if (mainContent) {
          // CSS анимация ухода (fallback)
          mainContent.classList.add('page-leaving');
          setTimeout(function() {
            window.location.href = href;
          }, 150);
        } else {
          window.location.href = href;
        }
      });
    });
  }

  // =========================================
  // MOBILE MENU TOGGLE
  // =========================================
  function initMobileMenu() {
    const menuBtn = document.querySelector('.nav-mobile-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navbar = document.querySelector('.navbar');
    if (!menuBtn || !navLinks || !navbar) return;

    function setMenuOpen(isOpen) {
      navLinks.classList.toggle('mobile-open', isOpen);
      menuBtn.innerHTML = isOpen
        ? '<i data-lucide="x"></i>'
        : '<i data-lucide="menu"></i>';
      menuBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      menuBtn.setAttribute('aria-label', isOpen ? 'Закрыть меню' : 'Открыть меню');
      initLucideIcons();
    }

    menuBtn.addEventListener('click', function(event) {
      event.preventDefault();
      event.stopPropagation();
      setMenuOpen(!navLinks.classList.contains('mobile-open'));
    });

    navLinks.addEventListener('click', function(event) {
      if (event.target.closest('a')) {
        setMenuOpen(false);
      }
    });

    document.addEventListener('click', function(event) {
      if (!navbar.contains(event.target)) {
        setMenuOpen(false);
      }
    });

    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') {
        setMenuOpen(false);
      }
    });

    // При увеличении окна выше мобильной границы — закрываем меню принудительно
    window.addEventListener('resize', function() {
      if (window.innerWidth > 768 && navLinks.classList.contains('mobile-open')) {
        setMenuOpen(false);
      }
    });
  }

  // =========================================
  // INITIALIZE ALL
  // =========================================
  function init() {
    initLucideIcons();
    initGSAPAnimations();
    initToastClose();
    initSmoothScroll();
    initButtonEffects();
    initNavbarFocusFix();
    initSmoothPageTransitions();
    initMobileMenu();
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Re-init Lucide icons after HTMX/turbo navigation (if used)
  document.addEventListener('htmx:afterSwap', initLucideIcons);
  document.addEventListener('turbo:render', initLucideIcons);
})();
