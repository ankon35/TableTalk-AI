// --------------------- Authentication Logic -------------------
// Check if user is logged in
let isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';

// Show appropriate page based on login status
if (!isLoggedIn) {
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('dashboard-container').style.display = 'none';
} else {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('dashboard-container').style.display = 'flex';
}

// Login functionality
document.getElementById('login-button').addEventListener('click', function () {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Simple validation (in a real app, this would be more secure)
    if (username && password) {
        localStorage.setItem('isLoggedIn', 'true');
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('dashboard-container').style.display = 'flex';
    } else {
        alert('Please enter both username and password');
    }
});

// Logout functionality
document.getElementById('logout-button').addEventListener('click', function () {
    localStorage.setItem('isLoggedIn', 'false');
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('dashboard-container').style.display = 'none';
});

// --------------------- Navigation Logic -------------------
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', function () {
        // Remove active class from all menu items
        document.querySelectorAll('.menu-item').forEach(i => {
            i.classList.remove('active');
        });

        // Add active class to clicked menu item
        this.classList.add('active');

        // Hide all content sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Show the target section
        const target = this.getAttribute('data-target');
        document.getElementById(`${target}-section`).classList.add('active');
    });
});

// --------------------- Product Form Logic -------------------
document.getElementById('product-form').addEventListener('submit', function (e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById('product-name').value;
    const price = document.getElementById('product-price').value;
    const size = document.getElementById('product-size').value;
    const description = document.getElementById('product-description').value;

    // Create new product card
    const productList = document.getElementById('product-list');
    const colDiv = document.createElement('div');
    colDiv.className = 'col-md-4';

    colDiv.innerHTML = `
                <div class="product-card">
                    <div class="product-image">
                        <img src="https://images.unsplash.com/photo-1565299585323-38174c738b42?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80" alt="${name}">
                    </div>
                    <div class="product-info">
                        <h3 class="product-title">${name}</h3>
                        <div class="product-price">$${price}</div>
                        <div class="product-size">${size}</div>
                        <p class="product-description">${description}</p>
                        <button class="action-btn edit-btn">Edit</button>
                        <button class="action-btn delete-btn">Delete</button>
                    </div>
                </div>
            `;

    // Add to the list
    productList.appendChild(colDiv);

    // Reset form
    this.reset();

    // Show success message (in a real app, this would be more robust)
    alert('Product added successfully!');
});

// --------------------- Topping Form Logic -------------------
document.getElementById('topping-form').addEventListener('submit', function (e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById('topping-name').value;
    const price = document.getElementById('topping-price').value;

    // Create new table row
    const toppingsList = document.getElementById('toppings-list');
    const row = document.createElement('tr');

    row.innerHTML = `
                <td>${name}</td>
                <td>$${price}</td>
                <td>
                    <button class="action-btn edit-btn">Edit</button>
                    <button class="action-btn delete-btn">Delete</button>
                </td>
            `;

    // Add to the table
    toppingsList.appendChild(row);

    // Reset form
    this.reset();

    // Show success message
    alert('Topping added successfully!');
});

// --------------------- Settings Form Logic -------------------
document.getElementById('settings-form').addEventListener('submit', function (e) {
    e.preventDefault();

    // Get form values
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Validate passwords
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match!');
        return;
    }

    // In a real app, this would verify current password and update via API
    alert('Settings updated successfully!');

    // Reset password fields
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
});

// --------------------- Profile Image Upload Logic -------------------
document.getElementById('profile-image-upload').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (event) {
            document.getElementById('profile-image').src = event.target.result;
            document.getElementById('admin-profile-img').src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
});

// --------------------- Delete Functionality -------------------
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('delete-btn')) {
        if (confirm('Are you sure you want to delete this item?')) {
            // In a real app, this would make an API call
            // For demo, just remove the parent element
            if (e.target.closest('.col-md-4')) {
                e.target.closest('.col-md-4').remove();
            } else if (e.target.closest('tr')) {
                e.target.closest('tr').remove();
            }
        }
    }
});

// --------------------- Charts Initialization -------------------
document.addEventListener('DOMContentLoaded', function () {
    // Revenue Distribution Pie Chart
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');
    const revenueChart = new Chart(revenueCtx, {
        type: 'pie',
        data: {
            labels: ['Pizzas', 'Burgers', 'Drinks', 'Sides', 'Desserts'],
            datasets: [{
                data: [35, 25, 15, 15, 10],
                backgroundColor: [
                    '#ff6b6b',
                    '#4ecdc4',
                    '#ffa844',
                    '#6a89cc',
                    '#f368e0'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Orders Trend Line Chart
    const ordersCtx = document.getElementById('ordersChart').getContext('2d');
    const ordersChart = new Chart(ordersCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Orders This Week',
                data: [65, 59, 80, 81, 56, 120, 110],
                fill: false,
                borderColor: '#ff6b6b',
                tension: 0.1,
                pointBackgroundColor: '#ff6b6b',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Month selector change event
    document.getElementById('month-selector').addEventListener('change', function () {
        // In a real app, this would fetch data for the selected month
        alert(`Data updated for ${this.value}`);
    });
});