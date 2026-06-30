// Highlight low stock rows
document.querySelectorAll('tr[data-stock]').forEach(row => {
    const stock = parseInt(row.dataset.stock);
    const min = parseInt(row.dataset.min || 5);
    if (stock === 0) row.classList.add('out-of-stock');
    else if (stock <= min) row.classList.add('low-stock');
});
