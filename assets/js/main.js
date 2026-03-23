const API_BASE = '';

function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <span>${type === 'success' ? '✓' : '✕'}</span>
        <span>${message}</span>
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateY(-10px)';
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

function setLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="loading"></span> Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
}

function checkAuth() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        window.location.href = '/login-page';
        return false;
    }
    return userId;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPrice(price) {
    if (!price || price === '0' || price === 'N/A') return 'Price not available';
    return `₹${price}`;
}

async function addToCart(item, button) {
    const userId = checkAuth();
    if (!userId) return;

    setLoading(button, true);
    
    try {
        const response = await fetch(`${API_BASE}/cart/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                title: item.title,
                price: item.price,
                link: item.link
            })
        });

        const data = await response.json();
        if (response.ok) {
            showAlert('Added to cart successfully!', 'success');
        } else {
            showAlert(data.error || 'Failed to add to cart', 'error');
        }
    } catch (error) {
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        setLoading(button, false);
    }
}

async function addToFavorites(item, button) {
    const userId = checkAuth();
    if (!userId) return;

    setLoading(button, true);
    
    try {
        const response = await fetch(`${API_BASE}/favorite/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                title: item.title,
                price: item.price,
                link: item.link,
                site: item.site
            })
        });

        const data = await response.json();
        if (response.ok) {
            showAlert('Added to favorites!', 'success');
        } else {
            showAlert(data.error || 'Failed to add to favorites', 'error');
        }
    } catch (error) {
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        setLoading(button, false);
    }
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
        <div class="product-site">${product.site}</div>
        <div class="product-title">${product.title}</div>
        <div class="product-price">${formatPrice(product.price)}</div>
        <div class="product-actions">
            <a href="${product.link}" target="_blank" class="btn btn-primary btn-sm">
                🔗 View Product
            </a>
            <button onclick="addToCart(${JSON.stringify(product).replace(/"/g, '&quot;')}, this)" class="btn btn-secondary btn-sm">
                🛒 Add to Cart
            </button>
            <button onclick="addToFavorites(${JSON.stringify(product).replace(/"/g, '&quot;')}, this)" class="btn btn-danger btn-sm">
                ❤️ Favorite
            </button>
        </div>
    `;
    return card;
}

document.addEventListener('DOMContentLoaded', function() {
    const fileInputs = document.querySelectorAll('.file-upload-input');
    fileInputs.forEach(input => {
        const label = input.closest('.file-upload-wrapper').querySelector('.file-upload-label');
        
        input.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                label.classList.add('has-file');
                const fileName = this.files[0].name;
                label.innerHTML = `
                    <span style="font-size: 48px; margin-bottom: 12px;">📁</span>
                    <span style="font-weight: 600; color: var(--secondary);">${fileName}</span>
                    <span style="font-size: 14px; color: var(--gray); margin-top: 8px;">Click to change</span>
                `;
            }
        });
    });
});






