/************************************
 ⭐ GLOBAL CART (used everywhere)
************************************/
let cart = JSON.parse(localStorage.getItem("cart")) || {};


/************************************
 ⭐ SAVE CART SAFELY
************************************/
function saveCart() {
    localStorage.removeItem("cartData");
    localStorage.removeItem("Cart");
    localStorage.removeItem("oldCart");
    localStorage.removeItem("items");
    localStorage.removeItem("data");
}
// If cart is corrupted, reset it
try {
    let c = JSON.parse(localStorage.getItem("cart"));
    if (typeof c !== "object" || Array.isArray(c)) {
        localStorage.removeItem("cart");
    }
} catch (e) { 
    localStorage.removeItem("cart");
};
   


/************************************
 ⭐ CHANGE QUANTITY (HOME PAGE)
************************************/
function changeQty(name, val) {
    let q = document.getElementById("qty-" + name);
    let num = parseInt(q.innerHTML) + val;
    if (num < 0) num = 0;
    q.innerHTML = num;
}


/************************************
 ⭐ ADD TO CART (HOME PAGE)
************************************/
function addToCart(name, price) {
    let qty = parseInt(document.getElementById("qty-" + name).innerHTML);

    if (qty <= 0) {
        alert("Please select quantity!");
        return;
    }

    if (cart[name]) {
        cart[name] += qty;
    } else {
        cart[name] = qty;
    }

    saveCart();
    alert(name + " added to cart!");
}


/************************************
 ⭐ PRODUCT MODAL FUNCTIONS (DETAIL PAGE)
************************************/
let currentItem = "";

function openDetails(item) {
    currentItem = item;

    let data = allItems[item];

    document.getElementById("detail-img").src = `/static/images/${data.image}`;
    document.getElementById("detail-name").innerText = item;
    document.getElementById("detail-price").innerText = "₹" + data.price;
    document.getElementById("detail-desc").innerText = data.description;

    document.getElementById("modal-qty").value = 1;

    document.getElementById("productModal").style.display = "flex";
}

function closeDetails() {
    document.getElementById("productModal").style.display = "none";
}

function modalIncrease() {
    let qty = document.getElementById("modal-qty");
    qty.value = parseInt(qty.value) + 1;
}

function modalDecrease() {
    let qty = document.getElementById("modal-qty");
    if (parseInt(qty.value) > 1) {
        qty.value = parseInt(qty.value) - 1;
    }
}

function modalAddToCart() {
    let qty = parseInt(document.getElementById("modal-qty").value);

    if (qty <= 0) return;

    cart[currentItem] = (cart[currentItem] || 0) + qty;

    saveCart();
    alert(currentItem + " added to cart!");
    closeDetails();
}


/************************************
 ⭐ RENDER CART PAGE
************************************/
function renderCart(backendData) {
    let container = document.getElementById("cart-items");
    if (!container) return; // Only run on cart page

    container.innerHTML = "";
    let total = 0;

    for (let name in cart) {
        let qty = cart[name];
        let item = backendData[name];

        if (item) {
            let subtotal = qty * item.price;
            total += subtotal;

            container.innerHTML += `
            <div class="item-box">
                <img src="/static/${item.image}">
                <h3>${name}</h3>

                <div class="qty-controls">
                    <button onclick="decreaseQty('${name}')">-</button>
                    <span><b>${qty}</b></span>
                    <button onclick="increaseQty('${name}')">+</button>
                </div>

                <p>Subtotal: ₹${subtotal}</p>

                <button class="remove-btn" onclick="removeItem('${name}')">Remove</button>
            </div>`;
        }
    }

    document.getElementById("total-field").value = total;
}


/************************************
 ⭐ INCREASE QUANTITY (CART PAGE)
************************************/
function increaseQty(name) {
    cart[name]++;
    saveCart();
    location.reload();
}


/************************************
 ⭐ DECREASE QUANTITY (CART PAGE)
************************************/
function decreaseQty(name) {
    if (cart[name] > 1) {
        cart[name]--;
    } else {
        delete cart[name];
    }
    saveCart();
    location.reload();
}


/************************************
 ⭐ REMOVE ITEM COMPLETELY
************************************/
function removeItem(name) {
    delete cart[name];
    saveCart();
    location.reload();
}


/************************************
 ⭐ SUBMIT CART TO BILLING
************************************/
function submitCart(backendData) {
    let cartArray = [];
    let total = 0;

    for (let name in cart) {
        let item = backendData[name];
        let subtotal = cart[name] * item.price;

        total += subtotal;

        cartArray.push({
            name: name,
            qty: cart[name],
            total: subtotal
        });
    }

    document.getElementById("items-field").value = JSON.stringify(cartArray);
    document.getElementById("total-field").value = total;
}
