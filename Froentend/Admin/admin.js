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
// Hardcoded admin credentials
const ADMIN_EMAIL = 'ankon35744@gmail.com';
const ADMIN_PASSWORD = '123';

// Check if user is logged in
let isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';

// Show appropriate page based on login status
if (!isLoggedIn) {
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('dashboard-container').style.display = 'none';
} else {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('dashboard-container').style.display = 'flex';
    // Load products and toppings when dashboard is shown
    loadProducts();
    loadToppings();
}

// Login functionality
document.getElementById('login-button').addEventListener('click', function () {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Validate against hardcoded credentials
    if (username === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
        localStorage.setItem('isLoggedIn', 'true');
        isLoggedIn = true;
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('dashboard-container').style.display = 'flex';
        // Load products and toppings after login
        loadProducts();
        loadToppings();
    } else {
        alert('Invalid username or password. Please use:\nEmail: ankon35744@gmail.com\nPassword: 123');
    }
});

// Logout functionality
document.getElementById('logout-button').addEventListener('click', function () {
    localStorage.setItem('isLoggedIn', 'false');
    isLoggedIn = false;
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
        
        // Load appropriate data when switching sections
        if (target === 'products') {
            console.log('Switching to products section, loading products...');
            setTimeout(loadProducts, 100);
        } else if (target === 'toppings') {
            console.log('Switching to toppings section, loading toppings...');
            setTimeout(loadToppings, 100);
        } else if (target === 'dashboard' || target === 'orders') {
            // Re-initialize month selector for dashboard and orders pages
            setTimeout(initializeMonthSelector, 100);
        }
    });
});

// --------------------- Supabase Table Configuration -------------------
const PRODUCT_TABLE = 'product';
const TOPPING_TABLE = 'Toppings';

// Product column mappings
const PRODUCT_COLUMN_MAPPING = {
    name: '"p.name"',
    price: '"p.price"',
    size: '"p.size"',
    description: '"p.description"',
    image: '"p.image"'
};

// Topping column mappings
const TOPPING_COLUMN_MAPPING = {
    name: 'Topping_name',
    price: 'Topping_price'
};

// --------------------- Currency Formatting Functions -------------------
// Function to format price in BDT Taka format
function formatPriceBDT(price) {
    if (price === null || price === undefined) return '৳0';
    
    const numericPrice = parseFloat(price);
    if (isNaN(numericPrice)) return '৳0';
    
    return `৳${numericPrice.toFixed(2)}`;
}

// Function to parse BDT price input (remove currency symbol and convert to number)
function parsePriceBDT(priceString) {
    if (!priceString) return 0;
    
    // Remove BDT symbol and any non-numeric characters except decimal point
    const numericString = priceString.replace(/[^\d.]/g, '');
    const price = parseFloat(numericString);
    
    return isNaN(price) ? 0 : price;
}

// Function to validate price input (BDT format)
function validatePriceInput(input) {
    const value = input.value;
    // Allow only numbers and decimal point
    const sanitizedValue = value.replace(/[^\d.]/g, '');
    
    // Ensure only one decimal point
    const decimalCount = sanitizedValue.split('.').length - 1;
    if (decimalCount > 1) {
        input.value = sanitizedValue.replace(/\.+$/, '');
    } else {
        input.value = sanitizedValue;
    }
}

// --------------------- Product Functions -------------------
// Function to add product to Supabase
async function addProductToSupabase(productData) {
    try {
        if (!supabase) {
            throw new Error('Supabase not initialized');
        }

        const insertData = {
            'p.name': productData.name,
            'p.price': parseFloat(productData.price),
            'p.size': productData.size,
            'p.description': productData.description,
            'p.image': productData.image
        };

        console.log('Attempting to insert product data:', insertData);

        const { data, error } = await supabase
            .from(PRODUCT_TABLE)
            .insert([insertData])
            .select();

        if (error) {
            console.error('Supabase error details:', error);
            throw error;
        }

        return data[0];
    } catch (error) {
        console.error('Error adding product:', error);
        
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
        if (!supabase) {
            console.log('Supabase not initialized yet');
            return;
        }

        const { data, error } = await supabase
            .from(PRODUCT_TABLE)
            .select('*')
            .order('id', { ascending: false });

        if (error) {
            console.error('Supabase error details:', error);
            throw error;
        }

        displayProducts(data || []);
    } catch (error) {
        console.error('Error loading products:', error);
        
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
    if (!productList) {
        console.log('Product list element not found');
        return;
    }
    
    productList.innerHTML = ''; // Clear existing products

    if (products.length === 0) {
        productList.innerHTML = '<div class="col-12 text-center"><p>No products found. Add your first product!</p></div>';
        return;
    }

    products.forEach(product => {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-4 mb-4';
        colDiv.setAttribute('data-product-id', product.id);

        colDiv.innerHTML = `
            <div class="product-card">
                <div class="product-image">
                    <img src="${product['p.image'] || 'https://images.unsplash.com/photo-1565299585323-38174c738b42?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80'}" alt="${product['p.name']}">
                </div>
                <div class="product-info">
                    <h3 class="product-title">${product['p.name']}</h3>
                    <div class="product-price">${formatPriceBDT(product['p.price'])}</div>
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
            .from(PRODUCT_TABLE)
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

// --------------------- Topping Functions -------------------
// Function to add topping to Supabase
async function addToppingToSupabase(toppingData) {
    try {
        if (!supabase) {
            throw new Error('Supabase not initialized');
        }

        const insertData = {
            [TOPPING_COLUMN_MAPPING.name]: toppingData.name,
            [TOPPING_COLUMN_MAPPING.price]: parseFloat(toppingData.price)
        };

        console.log('Attempting to insert topping data:', insertData);

        const { data, error } = await supabase
            .from(TOPPING_TABLE)
            .insert([insertData])
            .select();

        if (error) {
            console.error('Supabase error details:', error);
            throw error;
        }

        return data[0];
    } catch (error) {
        console.error('Error adding topping:', error);
        
        if (error.message.includes('404')) {
            alert('Table "Toppings" not found. Please check your table name in Supabase.');
        } else if (error.message.includes('column')) {
            alert('Column not found. Error: ' + error.message);
        } else {
            alert('Error adding topping: ' + error.message);
        }
        return null;
    }
}

// Function to load toppings from Supabase
async function loadToppings() {
    try {
        if (!supabase) {
            console.log('Supabase not initialized yet');
            return;
        }

        const { data, error } = await supabase
            .from(TOPPING_TABLE)
            .select('*')
            .order('id', { ascending: false });

        if (error) {
            console.error('Supabase error details:', error);
            throw error;
        }

        displayToppings(data || []);
    } catch (error) {
        console.error('Error loading toppings:', error);
        
        if (error.message.includes('404')) {
            console.log('Table "Toppings" not found. Please create the table in Supabase.');
            // Show message in UI
            const toppingsList = document.getElementById('toppings-list');
            if (toppingsList) {
                toppingsList.innerHTML = '<tr><td colspan="3" class="text-center">Table "Toppings" not found. Please create the table in Supabase.</td></tr>';
            }
        } else {
            console.log('Error loading toppings: ' + error.message);
        }
    }
}

// Function to display toppings in the UI
function displayToppings(toppings) {
    const toppingsList = document.getElementById('toppings-list');
    if (!toppingsList) {
        console.log('Toppings list element not found');
        return;
    }
    
    toppingsList.innerHTML = ''; // Clear existing toppings

    if (toppings.length === 0) {
        toppingsList.innerHTML = '<tr><td colspan="3" class="text-center">No toppings found. Add your first topping!</td></tr>';
        return;
    }

    toppings.forEach(topping => {
        const row = document.createElement('tr');
        row.setAttribute('data-topping-id', topping.id);

        row.innerHTML = `
            <td>${topping[TOPPING_COLUMN_MAPPING.name]}</td>
            <td>${formatPriceBDT(topping[TOPPING_COLUMN_MAPPING.price])}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editTopping(${topping.id})">Edit</button>
                <button class="action-btn delete-btn" onclick="deleteTopping(${topping.id})">Delete</button>
            </td>
        `;

        toppingsList.appendChild(row);
    });
}

// Function to delete topping from Supabase
async function deleteTopping(toppingId) {
    if (!confirm('Are you sure you want to delete this topping?')) {
        return;
    }

    try {
        const { error } = await supabase
            .from(TOPPING_TABLE)
            .delete()
            .eq('id', toppingId);

        if (error) {
            throw error;
        }

        // Remove from UI
        const toppingElement = document.querySelector(`[data-topping-id="${toppingId}"]`);
        if (toppingElement) {
            toppingElement.remove();
        }

        alert('Topping deleted successfully!');
    } catch (error) {
        console.error('Error deleting topping:', error);
        alert('Error deleting topping: ' + error.message);
    }
}

// Function to edit topping (placeholder)
async function editTopping(toppingId) {
    alert('Edit functionality can be implemented with a modal or form. Topping ID: ' + toppingId);
}

// Function to edit product (placeholder)
async function editProduct(productId) {
    alert('Edit functionality can be implemented with a modal or form. Product ID: ' + productId);
}

// --------------------- Image Handling Functions -------------------
// Function to handle image upload
function handleImageUpload(file) {
    return new Promise((resolve, reject) => {
        if (!file) {
            resolve('');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(event) {
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

// --------------------- Form Submission Logic -------------------
// Product Form Submission
document.getElementById('product-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById('product-name').value;
    const price = document.getElementById('product-price').value;
    const size = document.getElementById('product-size').value;
    const description = document.getElementById('product-description').value;
    const imageFile = document.getElementById('product-image').files[0];

    // Validate required fields
    if (!name || !price || !size) {
        alert('Please fill in all required fields: Name, Price, and Size');
        return;
    }

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

// Topping Form Submission
document.getElementById('topping-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById('topping-name').value;
    const price = document.getElementById('topping-price').value;

    // Validate required fields
    if (!name || !price) {
        alert('Please fill in all required fields: Name and Price');
        return;
    }

    // Show loading state
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Adding Topping...';
    submitBtn.disabled = true;

    try {
        // Prepare topping data
        const toppingData = {
            name: name,
            price: price
        };

        // Add to Supabase
        const newTopping = await addToppingToSupabase(toppingData);

        if (newTopping) {
            // Reset form
            this.reset();
            
            // Reload toppings to show the new one
            await loadToppings();
            
            alert('Topping added successfully!');
        }
    } catch (error) {
        console.error('Error in topping submission:', error);
        alert('Error adding topping. Please try again.');
    } finally {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
});

// Settings Form Submission
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

// --------------------- Utility Functions -------------------
// Function to test Supabase connection
async function testSupabaseConnection() {
    try {
        if (!supabase) {
            alert('Supabase not initialized');
            return;
        }

        // Test products connection
        const { data: products, error: productsError } = await supabase
            .from(PRODUCT_TABLE)
            .select('count')
            .limit(1);

        // Test toppings connection
        const { data: toppings, error: toppingsError } = await supabase
            .from(TOPPING_TABLE)
            .select('count')
            .limit(1);

        let message = 'Connection Test Results:\n\n';
        message += `Products Table: ${productsError ? 'ERROR - ' + productsError.message : 'SUCCESS'}\n`;
        message += `Toppings Table: ${toppingsError ? 'ERROR - ' + toppingsError.message : 'SUCCESS'}`;

        alert(message);
    } catch (error) {
        alert('Connection test failed: ' + error.message);
    }
}

// Function to initialize month selector (only for dashboard and orders)
function initializeMonthSelector() {
    const monthSelector = document.getElementById('month-selector');
    if (monthSelector) {
        // Remove existing event listeners to avoid duplicates
        monthSelector.replaceWith(monthSelector.cloneNode(true));
        
        // Get the new reference
        const newMonthSelector = document.getElementById('month-selector');
        
        newMonthSelector.addEventListener('change', function () {
            // Only show alert if we're on dashboard or orders page
            const activeSection = document.querySelector('.content-section.active');
            if (activeSection && (activeSection.id === 'dashboard-section' || activeSection.id === 'orders-section')) {
                alert(`Data updated for ${this.value}`);
                
                // Here you can add actual data update logic
                updateChartData(this.value);
            }
        });
    }
}

// Function to update chart data based on selected month
function updateChartData(month) {
    console.log(`Updating charts for month: ${month}`);
    
    // Example: You would fetch new data from Supabase based on the month
    // and update the charts accordingly
    // This is where you'd implement actual data fetching and chart updates
}

// --------------------- Price Input Validation -------------------
// Add price input validation to product and topping forms
document.addEventListener('DOMContentLoaded', function() {
    // Product price input validation
    const productPriceInput = document.getElementById('product-price');
    if (productPriceInput) {
        productPriceInput.addEventListener('input', function() {
            validatePriceInput(this);
        });
        
        // Add BDT symbol placeholder
        productPriceInput.placeholder = 'Enter price in BDT';
    }

    // Topping price input validation
    const toppingPriceInput = document.getElementById('topping-price');
    if (toppingPriceInput) {
        toppingPriceInput.addEventListener('input', function() {
            validatePriceInput(this);
        });
        
        // Add BDT symbol placeholder
        toppingPriceInput.placeholder = 'Enter price in BDT';
    }
});

// --------------------- Charts Initialization -------------------
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Content Loaded');
    console.log('Is logged in:', isLoggedIn);
    
    // Add image preview functionality to product image input
    const productImageInput = document.getElementById('product-image');
    if (productImageInput) {
        productImageInput.addEventListener('change', function() {
            previewImage(this);
        });
    }

    // Wait for Supabase to be fully initialized and load data
    setTimeout(() => {
        console.log('Delayed initialization check - Supabase client:', supabase);
        
        // Load products and toppings when page is ready and user is logged in
        if (isLoggedIn && supabase) {
            console.log('User is logged in and Supabase ready, loading data...');
            loadProducts();
            loadToppings();
        } else {
            console.log('Conditions not met - isLoggedIn:', isLoggedIn, 'supabase:', !!supabase);
        }
    }, 1000);

    // Add simple test button for products only
    setTimeout(() => {
        const productSection = document.getElementById('products-section');
        if (productSection && !document.getElementById('products-test-button')) {
            const testButton = document.createElement('button');
            testButton.id = 'products-test-button';
            testButton.innerHTML = 'Reload Products';
            testButton.style.cssText = 'background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin: 10px; cursor: pointer;';
            testButton.onclick = () => {
                console.log('Manual reload products clicked');
                loadProducts();
            };
            productSection.appendChild(testButton);
        }
    }, 1500);

    // Initialize month selector on page load if we're on dashboard or orders
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection && (activeSection.id === 'dashboard-section' || activeSection.id === 'orders-section')) {
        initializeMonthSelector();
    }

    // Revenue Distribution Pie Chart - only initialize if chart element exists
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx) {
        const revenueChart = new Chart(revenueCtx.getContext('2d'), {
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
    }

    // Orders Trend Line Chart - only initialize if chart element exists
    const ordersCtx = document.getElementById('ordersChart');
    if (ordersCtx) {
        const ordersChart = new Chart(ordersCtx.getContext('2d'), {
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
    }
});