// Auto-fill amount from selected membership
const membershipSelect = document.getElementById('membership_id');
const amountInput = document.getElementById('amount');
if (membershipSelect && amountInput) {
    membershipSelect.addEventListener('change', function() {
        const option = this.options[this.selectedIndex];
        if (option.dataset.price) amountInput.value = option.dataset.price;
    });
}
