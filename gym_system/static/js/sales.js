let cart = [];

function addToCart(productId, name, price) {
    const existing = cart.find(i => i.id === productId);
    if (existing) existing.qty++;
    else cart.push({ id: productId, name, price, qty: 1 });
    renderCart();
}

function renderCart() {
    const tbody = document.getElementById('cartBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    let total = 0;
    cart.forEach(item => {
        const sub = item.price * item.qty;
        total += sub;
        tbody.innerHTML += '<tr><td>' + item.name + '</td><td>' + item.qty + '</td><td>$' + sub.toLocaleString('es-CO') + '</td></tr>';
    });
    const totalEl = document.getElementById('cartTotal');
    if (totalEl) totalEl.textContent = '$' + total.toLocaleString('es-CO');
}
