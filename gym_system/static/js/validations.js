// Real-time form validation
document.querySelectorAll('input[type="email"]').forEach(input => {
    input.addEventListener('blur', function() {
        const re = /^[^@]+@[^@]+\.[^@]+$/;
        this.classList.toggle('is-invalid', !re.test(this.value) && this.value);
    });
});

document.querySelectorAll('input[name="phone"]').forEach(input => {
    input.addEventListener('input', function() {
        this.value = this.value.replace(/[^0-9+]/g, '');
    });
});
