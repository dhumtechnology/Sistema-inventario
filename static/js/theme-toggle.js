(function () {
    'use strict';

    var STORAGE_KEY = 'jazzmin-theme-mode';

    function resolveMode(mode) {
        if (mode === 'auto') {
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'dark'
                : 'light';
        }
        return mode;
    }

    function getCurrentMode() {
        return resolveMode(localStorage.getItem(STORAGE_KEY) || 'light');
    }

    function applyMode(mode) {
        localStorage.setItem(STORAGE_KEY, mode);
        document.documentElement.setAttribute('data-bs-theme', mode);
        updateToggleButtons(mode);
    }

    function toggleMode() {
        applyMode(getCurrentMode() === 'dark' ? 'light' : 'dark');
    }

    function updateToggleButtons(mode) {
        document.querySelectorAll('[data-jazzmin-theme-toggle]').forEach(function (btn) {
            var icon = btn.querySelector('i');
            if (!icon) return;

            if (mode === 'dark') {
                icon.className = 'fas fa-sun';
                btn.title = 'Cambiar a modo claro';
                btn.setAttribute('aria-label', 'Cambiar a modo claro');
            } else {
                icon.className = 'fas fa-moon';
                btn.title = 'Cambiar a modo oscuro';
                btn.setAttribute('aria-label', 'Cambiar a modo oscuro');
            }
        });
    }

    function bindToggle(btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            toggleMode();
        });
    }

    function createNavbarToggle() {
        var nav = document.querySelector('.navbar-nav.ms-auto');
        if (!nav || document.querySelector('[data-jazzmin-theme-toggle]')) {
            return;
        }

        var li = document.createElement('li');
        li.className = 'nav-item';
        li.innerHTML =
            '<a class="nav-link" href="#" data-jazzmin-theme-toggle role="button" title="Cambiar a modo oscuro">' +
            '<i class="fas fa-moon"></i></a>';

        var toggle = li.querySelector('[data-jazzmin-theme-toggle]');
        bindToggle(toggle);
        nav.insertBefore(li, nav.firstChild);
        updateToggleButtons(getCurrentMode());
    }

    function createLoginToggle() {
        if (!document.body.classList.contains('login-page')) {
            return;
        }
        if (document.querySelector('[data-jazzmin-theme-toggle]')) {
            return;
        }

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline-secondary jazzmin-login-theme-toggle';
        btn.setAttribute('data-jazzmin-theme-toggle', '');
        btn.title = 'Cambiar a modo oscuro';
        btn.innerHTML = '<i class="fas fa-moon"></i>';
        bindToggle(btn);
        document.body.appendChild(btn);
        updateToggleButtons(getCurrentMode());
    }

    function init() {
        createNavbarToggle();
        createLoginToggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
