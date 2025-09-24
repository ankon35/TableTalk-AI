// --------------------- Supabase Configuration -------------------
const supabaseUrl = 'https://etfahccxxrgqvhrhvphf.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0ZmFoY2N4eHJncXZocmh2cGhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg1Njg4MTQsImV4cCI6MjA3NDE0NDgxNH0.mpyCoSSsff95-sRimkTNKl4MgrUTOFDK0pgkno6tXvY';

// Initialize Supabase client with better error handling
let supabase;

function initializeSupabase() {
    try {
        if (typeof window.supabase !== 'undefined') {
            supabase = window.supabase.createClient(supabaseUrl, supabaseKey);
            console.log('Supabase initialized successfully');
        } else {
            console.error('Supabase library not found. Please include: <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>');
        }
    } catch (error) {
        console.error('Error initializing Supabase:', error);
    }
}

// Initialize immediately or wait for DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSupabase);
} else {
    initializeSupabase();
}

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
    // Load products when dashboard is shown
    loadProducts();
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
        // Load products after login
        loadProducts();
        // Load products after login
        loadProducts();
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
        
        // If switching to products section, load products
        if (target === 'products') {
            console.log('Switching to products section, loading products...');
            setTimeout(loadProducts, 100); // Small delay to ensure UI is ready
        }
    });
});

// --------------------- Supabase Product Functions -------------------
// *** IMPORTANT: Update these table name and column mappings ***
const TABLE_NAME = 'product'; // Your actual table name (singular)
// Column names with dots need to be quoted in PostgreSQL
const COLUMN_MAPPING = {
    name: '"p.name"',        // Quoted column name
    price: '"p.price"',      // Quoted column name
    size: '"p.size"',        // Quoted column name
    description: '"p.description"', // Quoted column name
    image: '"p.image"'       // Quoted column name
};

// Function to add product to Supabase
async function addProductToSupabase(productData) {
    try {
        // Check if supabase is initialized
        if (!supabase) {
            throw new Error('Supabase not initialized');
        }

        // For INSERT operations, we need to use the raw column names
        const insertData = {
            'p.name': productData.name,
            'p.price': parseFloat(productData.price),
            'p.size': productData.size,
            'p.description': productData.description,
            'p.image': productData.image
        };

        console.log('Attempting to insert data:', insertData);

        const { data, error } = await supabase
            .from(TABLE_NAME)
            .insert([insertData])
            .select();

        if (error) {
            console.error('Supabase error details:', error);
            throw error;
        }

        return data[0];
    } catch (error) {
        console.error('Error adding product:', error);
        
        // More detailed error message
        if (error.message.includes('404')) {
            alert('Table "product" not found. Please check your table name in Supabase.');
        } else if (error.message.includes('column')) {
            alert('Column not found. Error: ' + error.message);
        } else {
            alert('Error adding product: ' + error.message);
        }
        return null;
    }
}

// Function to load products from Supabase
async function loadProducts() {
    try {
        // Check if supabase is initialized
        if (!supabase) {
            console.log('Supabase not initialized yet');
            return;
        }

        const { data, error } = await supabase
            .from(TABLE_NAME)
            .select('*')
            .order('id', { ascending: false }); // Using 'id' instead of 'created_at'

        if (error) {
            console.error('Supabase error details:', error);
            throw error;
        }

        displayProducts(data || []);
    } catch (error) {
        console.error('Error loading products:', error);
        
        // More detailed error message
        if (error.message.includes('404')) {
            console.log('Table "products" not found. Please create the table in Supabase.');
        } else {
            console.log('Error loading products: ' + error.message);
        }
    }
}

// Function to display products in the UI
function displayProducts(products) {
    const productList = document.getElementById('product-list');
    productList.innerHTML = ''; // Clear existing products

    products.forEach(product => {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-4';
        colDiv.setAttribute('data-product-id', product.id);

        colDiv.innerHTML = `
            <div class="product-card">
                <div class="product-image">
                    <img src="${product['p.image'] || 'https://images.unsplash.com/photo-1565299585323-38174c738b42?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80'}" alt="${product['p.name']}">
                </div>
                <div class="product-info">
                    <h3 class="product-title">${product['p.name']}</h3>
                    <div class="product-price">$${product['p.price']}</div>
                    <div class="product-size">${product['p.size']}</div>
                    <p class="product-description">${product['p.description']}</p>
                    <button class="action-btn edit-btn" onclick="editProduct(${product.id})">Edit</button>
                    <button class="action-btn delete-btn" onclick="deleteProduct(${product.id})">Delete</button>
                </div>
            </div>
        `;

        productList.appendChild(colDiv);
    });
}

// Function to delete product from Supabase
async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) {
        return;
    }

    try {
        const { error } = await supabase
            .from(TABLE_NAME)
            .delete()
            .eq('id', productId);

        if (error) {
            throw error;
        }

        // Remove from UI
        const productElement = document.querySelector(`[data-product-id="${productId}"]`);
        if (productElement) {
            productElement.remove();
        }

        alert('Product deleted successfully!');
    } catch (error) {
        console.error('Error deleting product:', error);
        alert('Error deleting product: ' + error.message);
    }
}

// Function to edit product (placeholder for now)
async function editProduct(productId) {
    // This is a simple implementation - you can enhance it with a modal or inline editing
    alert('Edit functionality can be implemented with a modal or form. Product ID: ' + productId);
    // You can implement a more sophisticated edit functionality here
}

// Function to handle image upload
function handleImageUpload(file) {
    return new Promise((resolve, reject) => {
        if (!file) {
            resolve('');
            return;
        }

        // For demo purposes, we'll use a placeholder image URL
        // In a real application, you would upload to Supabase Storage
        const reader = new FileReader();
        reader.onload = function(event) {
            // In production, upload to Supabase Storage and get the public URL
            resolve(event.target.result);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Function to preview uploaded image
function previewImage(input) {
    const file = input.files[0];
    const previewContainer = document.getElementById('image-preview-container') || createImagePreviewContainer(input);
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewContainer.innerHTML = `
                <div class="image-preview">
                    <img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; object-fit: cover; border-radius: 8px; border: 2px solid #ddd;">
                    <button type="button" onclick="removeImagePreview()" style="display: block; margin-top: 10px; padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">Remove Image</button>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    } else {
        previewContainer.innerHTML = '';
    }
}

// Function to create image preview container if it doesn't exist
function createImagePreviewContainer(inputElement) {
    const container = document.createElement('div');
    container.id = 'image-preview-container';
    container.style.marginTop = '10px';
    
    // Insert after the file input
    inputElement.parentNode.insertBefore(container, inputElement.nextSibling);
    return container;
}

// Function to remove image preview
function removeImagePreview() {
    const previewContainer = document.getElementById('image-preview-container');
    const fileInput = document.getElementById('product-image');
    
    if (previewContainer) {
        previewContainer.innerHTML = '';
    }
    if (fileInput) {
        fileInput.value = '';
    }
}

// --------------------- Product Form Logic -------------------
// --------------------- Product Form Logic -------------------
document.getElementById('product-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById('product-name').value;
    const price = document.getElementById('product-price').value;
    const size = document.getElementById('product-size').value;
    const description = document.getElementById('product-description').value;
    const imageFile = document.getElementById('product-image').files[0];

    // Show loading state
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Adding Product...';
    submitBtn.disabled = true;

    try {
        // Handle image upload
        const imageUrl = await handleImageUpload(imageFile);

        // Prepare product data
        const productData = {
            name: name,
            price: price,
            size: size,
            description: description,
            image: imageUrl
        };

        // Add to Supabase
        const newProduct = await addProductToSupabase(productData);

        if (newProduct) {
            // Reset form
            this.reset();
            
            // Reset image preview to default
            removeImagePreview();
            
            // Reload products to show the new one
            await loadProducts();
            
            alert('Product added successfully!');
        }
    } catch (error) {
        console.error('Error in product submission:', error);
        alert('Error adding product. Please try again.');
    } finally {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
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
    if (e.target.classList.contains('delete-btn') && !e.target.hasAttribute('onclick')) {
        if (confirm('Are you sure you want to delete this item?')) {
            // This handles non-product delete buttons (like toppings)
            if (e.target.closest('tr')) {
                e.target.closest('tr').remove();
            }
        }
    }
});

// --------------------- Charts Initialization -------------------
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Content Loaded');
    console.log('Is logged in:', isLoggedIn);
    
    // Wait for Supabase to be fully initialized
    setTimeout(() => {
        console.log('Delayed initialization check - Supabase client:', supabase);
        
        // Load products when page is ready and user is logged in
        if (isLoggedIn && supabase) {
            console.log('User is logged in and Supabase ready, loading products...');
            loadProducts();
        } else {
            console.log('Conditions not met - isLoggedIn:', isLoggedIn, 'supabase:', !!supabase);
        }
    }, 1000);

    // Add manual load products button for testing
    setTimeout(() => {
        const productSection = document.getElementById('products-section');
        if (productSection && !document.getElementById('test-buttons-added')) {
            const testContainer = document.createElement('div');
            testContainer.id = 'test-buttons-added';
            testContainer.style.cssText = 'margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 2px solid #007bff;';
            
            const testButton = document.createElement('button');
            testButton.innerHTML = 'Reload Products (Test)';
            testButton.style.cssText = 'background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin-right: 10px; cursor: pointer;';
            testButton.onclick = () => {
                console.log('Manual reload products clicked');
                loadProducts();
            };
            
            // Add test connection button
            const testConnButton = document.createElement('button');
            testConnButton.innerHTML = 'Test Connection';
            testConnButton.style.cssText = 'background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin-right: 10px; cursor: pointer;';
            testConnButton.onclick = testSupabaseConnection;
            
            // Add debug button
            const debugButton = document.createElement('button');
            debugButton.innerHTML = 'Debug Info';
            debugButton.style.cssText = 'background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;';
            debugButton.onclick = () => {
                console.log('=== DEBUG INFO ===');
                console.log('Supabase client:', supabase);
                console.log('Table name:', TABLE_NAME);
                console.log('Is logged in:', isLoggedIn);
                console.log('Product list element:', document.getElementById('product-list'));
                alert('Debug info logged to console. Press F12 to view.');
            };
            
            testContainer.appendChild(testConnButton);
            testContainer.appendChild(testButton);
            testContainer.appendChild(debugButton);
            
            const title = document.createElement('h4');
            title.textContent = 'Testing Tools';
            title.style.cssText = 'margin: 0 0 10px 0; color: #007bff;';
            testContainer.insertBefore(title, testContainer.firstChild);
            
            productSection.insertBefore(testContainer, productSection.firstChild);
            console.log('Test buttons added to products section');
        }
    }, 1500);

    // Add image preview functionality to product image input
    const productImageInput = document.getElementById('product-image');
    if (productImageInput) {
        productImageInput.addEventListener('change', function() {
            previewImage(this);
        });
    }

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




