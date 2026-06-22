document.addEventListener('DOMContentLoaded', function () {
    // ---------------------------------------------------------------
    // Мобильное меню
    // ---------------------------------------------------------------
    var navToggle = document.getElementById('navToggle');
    var mobileNav = document.getElementById('mobileNav');

    if (navToggle && mobileNav) {
        navToggle.addEventListener('click', function () {
            var isOpen = mobileNav.classList.toggle('is-open');
            navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
    }

    // ---------------------------------------------------------------
    // Автосабмит сортировки на странице списка автомобилей
    // ---------------------------------------------------------------
    var sortSelect = document.querySelector('[data-auto-submit]');
    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            sortSelect.form.submit();
        });
    }

    // ---------------------------------------------------------------
    // Плавное появление карточек при загрузке (без лишней анимации
    // при каждом скролле — один спокойный заход при первом рендере)
    // ---------------------------------------------------------------
    var revealItems = document.querySelectorAll('.car-card, .category-card');
    revealItems.forEach(function (el, index) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(6px)';
        setTimeout(function () {
            el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 30 + index * 25);
    });

    // ---------------------------------------------------------------
    // Подтверждение удаления из сравнения / избранного — не обязательно,
    // но предотвращает случайные клики на мобильных устройствах
    // ---------------------------------------------------------------
    var dangerForms = document.querySelectorAll('[data-confirm]');
    dangerForms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            var message = form.getAttribute('data-confirm');
            if (message && !window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
