let currentView = "dashboard";
let productCache = [];
let customerCache = [];
let invoiceRows = [];
let token = localStorage.getItem("astha_owner_token") || "";
let selectedProductId = "";
let selectedCustomerId = "";
let setupRequired = false;
let loadingView = false;
let appData = null;

const authPanel = document.getElementById("auth");
const appPanel = document.getElementById("app");
const content = document.getElementById("content");
const viewTitle = document.getElementById("viewTitle");
const setupHint = document.getElementById("setupHint");
const authMessage = document.getElementById("authMessage");

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (response.status === 401 || response.status === 403) {
    token = "";
    localStorage.removeItem("astha_owner_token");
    appPanel.classList.add("hidden");
    authPanel.classList.remove("hidden");
    authMessage.textContent = data.error || "Please login again.";
  }
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function refreshData(force = false) {
  if (appData && !force) return appData;
  appData = await api("/api/bootstrap");
  productCache = appData.products || [];
  customerCache = appData.customers || [];
  return appData;
}

async function openPdf(invoiceNo) {
  const popup = window.open("", "_blank");
  try {
    const result = await api(`/api/invoices/${invoiceNo}/share`, { method: "POST" });
    const url = new URL(result.url, window.location.origin).href;
    if (popup) {
      popup.location.href = url;
    } else {
      window.location.href = url;
    }
  } catch (error) {
    if (popup) popup.close();
    alert(error.message);
  }
}

async function shareInvoice(invoiceNo, mobile = "") {
  const popup = window.open("", "_blank");
  try {
    const result = await api(`/api/invoices/${invoiceNo}/share`, { method: "POST" });
    const url = new URL(result.url, window.location.origin).href;
    const message = `Your invoice ${invoiceNo} PDF is ready: ${url}`;
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(url);
    }
    if (mobile) {
      const phone = String(mobile).replace(/\D/g, "").replace(/^(\d{10})$/, "91$1");
      const whatsappUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
      if (popup) popup.location.href = whatsappUrl;
      else window.location.href = whatsappUrl;
    } else {
      const mailUrl = `mailto:?subject=Invoice ${invoiceNo}&body=${encodeURIComponent(message)}`;
      if (popup) popup.location.href = mailUrl;
      else window.location.href = mailUrl;
    }
    alert("Invoice PDF link copied and share window opened.");
  } catch (error) {
    if (popup) popup.close();
    alert(error.message);
  }
}

async function deleteInvoice(invoiceNo) {
  if (!confirm(`Delete invoice ${invoiceNo}?`)) return;
  try {
    await api(`/api/invoices/${invoiceNo}`, { method: "DELETE" });
    await loadView("invoices");
  } catch (error) {
    alert(error.message);
  }
}

function formatRs(value) {
  return `Rs. ${Number(value || 0).toFixed(2)}`;
}

function table(headers, rows) {
  return `
    <table>
      <thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
      <tbody>${rows.join("")}</tbody>
    </table>
  `;
}

function formInput(id, placeholder, type = "text") {
  const step = type === "number" ? ' step="any"' : "";
  return `<input id="${id}" type="${type}"${step} placeholder="${placeholder}">`;
}

async function saveProduct() {
  try {
    const payload = {
      name: document.getElementById("productName").value,
      hsn: document.getElementById("productHsn").value,
      purchase_price: document.getElementById("productPurchase").value,
      sale_price: document.getElementById("productSale").value,
      unit: document.getElementById("productUnit").value || "Pcs",
      quantity: document.getElementById("productQty").value,
      gst: document.getElementById("productGst").value,
    };
    await api(selectedProductId ? `/api/products/${selectedProductId}` : "/api/products", {
      method: selectedProductId ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    selectedProductId = "";
    await refreshData(true);
    await loadView("products");
  } catch (error) {
    alert(error.message);
  }
}

async function deleteSelectedProduct() {
  if (!selectedProductId) {
    alert("Select a product first");
    return;
  }
  if (!confirm("Delete selected product?")) return;
  try {
    await api(`/api/products/${selectedProductId}`, { method: "DELETE" });
    selectedProductId = "";
    await refreshData(true);
    await loadView("products");
  } catch (error) {
    alert(error.message);
  }
}

function clearProductForm() {
  selectedProductId = "";
  ["productName", "productHsn", "productPurchase", "productSale", "productQty", "productGst"].forEach((id) => {
    const element = document.getElementById(id);
    if (element) element.value = "";
  });
  const unit = document.getElementById("productUnit");
  if (unit) unit.value = "Pcs";
}

function selectProduct(id) {
  const product = productCache.find((row) => Number(row.id) === Number(id));
  if (!product) return;
  selectedProductId = product.id;
  document.getElementById("productName").value = product.name || "";
  document.getElementById("productHsn").value = product.hsn || "";
  document.getElementById("productPurchase").value = product.purchase_price || 0;
  document.getElementById("productSale").value = product.sale_price || product.price || 0;
  document.getElementById("productUnit").value = product.unit || "Pcs";
  document.getElementById("productQty").value = product.quantity || 0;
  document.getElementById("productGst").value = product.gst || 0;
  document.getElementById("productFormTitle").textContent = "Edit Product";
}

async function saveCustomer() {
  try {
    const payload = {
      name: document.getElementById("customerName").value,
      mobile: document.getElementById("customerMobile").value,
      email: document.getElementById("customerEmail").value,
      address: document.getElementById("customerAddress").value,
      gst: document.getElementById("customerGst").value,
    };
    await api(selectedCustomerId ? `/api/customers/${selectedCustomerId}` : "/api/customers", {
      method: selectedCustomerId ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    selectedCustomerId = "";
    await refreshData(true);
    await loadView("customers");
  } catch (error) {
    alert(error.message);
  }
}

async function deleteSelectedCustomer() {
  if (!selectedCustomerId) {
    alert("Select a customer first");
    return;
  }
  if (!confirm("Delete selected customer?")) return;
  try {
    await api(`/api/customers/${selectedCustomerId}`, { method: "DELETE" });
    selectedCustomerId = "";
    await refreshData(true);
    await loadView("customers");
  } catch (error) {
    alert(error.message);
  }
}

function clearCustomerForm() {
  selectedCustomerId = "";
  ["customerName", "customerMobile", "customerEmail", "customerAddress", "customerGst"].forEach((id) => {
    const element = document.getElementById(id);
    if (element) element.value = "";
  });
}

function selectCustomer(id) {
  const customer = customerCache.find((row) => Number(row.id) === Number(id));
  if (!customer) return;
  selectedCustomerId = customer.id;
  document.getElementById("customerName").value = customer.name || "";
  document.getElementById("customerMobile").value = customer.mobile || "";
  document.getElementById("customerEmail").value = customer.email || "";
  document.getElementById("customerAddress").value = customer.address || "";
  document.getElementById("customerGst").value = customer.gst || "";
  document.getElementById("customerFormTitle").textContent = "Edit Customer";
}

function renderInvoiceRows() {
  const rows = invoiceRows.map((row, index) => `
    <tr>
      <td>${row.product}</td>
      <td>${row.quantity}</td>
      <td>${formatRs(row.price)}</td>
      <td><button onclick="removeInvoiceRow(${index})">Remove</button></td>
    </tr>
  `);
  document.getElementById("invoiceItems").innerHTML = table(["Product", "Qty", "Price", ""], rows);
}

function addInvoiceRow() {
  const productName = document.getElementById("invoiceProduct").value;
  const product = productCache.find((item) => item.name === productName);
  if (!product) {
    alert("Select a valid product");
    return;
  }
  const quantity = Number(document.getElementById("invoiceQty").value || 0);
  if (quantity <= 0) {
    alert("Quantity must be greater than zero");
    return;
  }
  invoiceRows.push({
    product: product.name,
    quantity,
    price: Number(document.getElementById("invoicePrice").value || product.sale_price || 0),
  });
  document.getElementById("invoiceQty").value = "";
  renderInvoiceRows();
}

function removeInvoiceRow(index) {
  invoiceRows.splice(index, 1);
  renderInvoiceRows();
}

async function createInvoice() {
  try {
    const result = await api("/api/invoices", {
      method: "POST",
      body: JSON.stringify({
        customer: document.getElementById("invoiceCustomer").value,
        mobile: document.getElementById("invoiceMobile").value,
        address: document.getElementById("invoiceAddress").value,
        items: invoiceRows,
      }),
    });
    invoiceRows = [];
    await refreshData(true);
    const publicUrl = new URL(result.public_pdf, window.location.origin).href;
    alert(`Invoice created: ${result.invoice_no}\nPDF link: ${publicUrl}`);
    await loadView("invoices");
  } catch (error) {
    alert(error.message);
  }
}

async function loadView(view) {
  if (loadingView) return;
  loadingView = true;
  try {
  currentView = view;
  viewTitle.textContent = view[0].toUpperCase() + view.slice(1);
  if (!appData) content.innerHTML = `<div class="card">Loading ${view}...</div>`;
  document.querySelectorAll(".sidebar button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === view);
  });
  const dataBundle = await refreshData();

  if (view === "dashboard") {
    const data = dataBundle.dashboard;
    content.innerHTML = `
      <div class="grid">
        <div class="card"><div class="label">Sales</div><div class="value">${formatRs(data.sales_total)}</div></div>
        <div class="card"><div class="label">Profit</div><div class="value">${formatRs(data.profit_total)}</div></div>
        <div class="card"><div class="label">Invoices</div><div class="value">${data.invoice_count}</div></div>
        <div class="card"><div class="label">Outstanding</div><div class="value">${formatRs(data.due_total)}</div></div>
      </div>`;
  }

  if (view === "invoices") {
    const data = { invoices: dataBundle.invoices || [] };
    const productOptions = productCache.map((row) => `<option value="${row.name}">${row.name} - stock ${row.quantity || 0}</option>`).join("");
    content.innerHTML = `
      <div class="card form-card">
        <h2>Create Invoice</h2>
        <div class="form-grid">
          ${formInput("invoiceCustomer", "Customer name")}
          ${formInput("invoiceMobile", "Mobile")}
          ${formInput("invoiceAddress", "Address")}
        </div>
        <div class="form-grid">
          <select id="invoiceProduct">${productOptions}</select>
          ${formInput("invoiceQty", "Qty", "number")}
          ${formInput("invoicePrice", "Sale price override", "number")}
          <button onclick="addInvoiceRow()">Add Item</button>
        </div>
        <div id="invoiceItems"></div>
        <button onclick="createInvoice()">Generate Invoice</button>
      </div>
    ` + table(["Invoice", "Customer", "Mobile", "Total", "Balance", "Status", "PDF", "Send", "Delete"], data.invoices.map((row) => `
      <tr>
        <td>${row.invoice_no}</td><td>${row.customer || ""}</td><td>${row.mobile || ""}</td>
        <td>${formatRs(row.total)}</td><td>${formatRs(row.balance)}</td><td>${row.payment_status || ""}</td>
        <td><button onclick="openPdf('${row.invoice_no}')">Open</button></td>
        <td><button onclick="shareInvoice('${row.invoice_no}', '${row.mobile || ""}')">Send PDF</button></td>
        <td><button onclick="deleteInvoice('${row.invoice_no}')">Delete</button></td>
      </tr>`));
    renderInvoiceRows();
  }

  if (view === "products") {
    const data = { products: dataBundle.products || [] };
    productCache = data.products;
    selectedProductId = "";
    content.innerHTML = `
      <div class="card form-card">
        <h2 id="productFormTitle">Add Product</h2>
        <div class="form-grid">
          ${formInput("productName", "Product name")}
          ${formInput("productHsn", "HSN")}
          ${formInput("productPurchase", "Purchase price", "number")}
          ${formInput("productSale", "Sale price", "number")}
          ${formInput("productUnit", "Unit")}
          ${formInput("productQty", "Quantity", "number")}
          ${formInput("productGst", "GST %", "number")}
          <button onclick="saveProduct()">Save Product</button>
          <button onclick="deleteSelectedProduct()">Delete Selected</button>
          <button onclick="clearProductForm()">Clear</button>
        </div>
      </div>
    ` + table(["Select", "Name", "Purchase", "Sale", "Unit", "Qty", "GST"], data.products.map((row) => `
      <tr>
        <td><button onclick="selectProduct(${row.id})">Edit</button></td>
        <td>${row.name}</td><td>${formatRs(row.purchase_price)}</td><td>${formatRs(row.sale_price)}</td>
        <td>${row.unit || ""}</td><td>${row.quantity || 0}</td><td>${row.gst || 0}%</td>
      </tr>`));
  }

  if (view === "customers") {
    const data = { customers: dataBundle.customers || [] };
    customerCache = data.customers;
    selectedCustomerId = "";
    content.innerHTML = `
      <div class="card form-card">
        <h2 id="customerFormTitle">Add Customer</h2>
        <div class="form-grid">
          ${formInput("customerName", "Customer name")}
          ${formInput("customerMobile", "Mobile")}
          ${formInput("customerEmail", "Email")}
          ${formInput("customerAddress", "Address")}
          ${formInput("customerGst", "GSTIN")}
          <button onclick="saveCustomer()">Save Customer</button>
          <button onclick="deleteSelectedCustomer()">Delete Selected</button>
          <button onclick="clearCustomerForm()">Clear</button>
        </div>
      </div>
    ` + table(["Select", "Name", "Mobile", "Email", "Balance"], data.customers.map((row) => `
      <tr>
        <td><button onclick="selectCustomer(${row.id})">Edit</button></td>
        <td>${row.name}</td><td>${row.mobile || ""}</td><td>${row.email || ""}</td><td>${formatRs(row.balance)}</td>
      </tr>`));
  }
  } catch (error) {
    content.innerHTML = `<div class="card">${error.message}</div>`;
  } finally {
    loadingView = false;
  }
}

function canAutoRefresh() {
  if (appPanel.style.display === "none" || loadingView) return false;
  const active = document.activeElement;
  if (!active) return true;
  return !["INPUT", "TEXTAREA", "SELECT"].includes(active.tagName);
}

setInterval(() => {
  if (canAutoRefresh()) {
    refreshData(true).then(() => loadView(currentView)).catch((error) => console.warn(error.message));
  }
}, 30000);

async function checkSetup() {
  const health = await api("/api/health");
  setupRequired = Boolean(health.setup_required);
  setupHint.textContent = health.setup_required
    ? "First time setup: create owner username, email, and password."
    : "Enter username/email and password to continue.";
  document.getElementById("setupBtn").style.display = "none";
  document.getElementById("loginBtn").textContent = health.setup_required ? "Set Owner & Login" : "Login";
  document.getElementById("ownerUsername").style.display = health.setup_required ? "block" : "none";
  document.getElementById("securityQuestion").style.display = health.setup_required ? "block" : "none";
  document.getElementById("securityAnswer").style.display = health.setup_required ? "block" : "none";
  document.getElementById("ownerEmail").placeholder = health.setup_required ? "Main account email" : "Username or email";
  document.getElementById("forgotBtn").style.display = health.setup_required ? "none" : "inline-block";
}

async function setupOwnerPassword() {
  try {
    await api("/api/setup", {
      method: "POST",
      body: JSON.stringify({
        username: document.getElementById("ownerUsername").value,
        email: document.getElementById("ownerEmail").value,
        password: document.getElementById("ownerPassword").value,
        security_question: document.getElementById("securityQuestion").value,
        security_answer: document.getElementById("securityAnswer").value,
      }),
    });
    authMessage.textContent = "Owner password saved. Now login.";
    await checkSetup();
  } catch (error) {
    authMessage.textContent = error.message;
  }
}

async function login() {
  try {
    if (setupRequired) {
      await api("/api/setup", {
        method: "POST",
        body: JSON.stringify({
          username: document.getElementById("ownerUsername").value,
          email: document.getElementById("ownerEmail").value,
          password: document.getElementById("ownerPassword").value,
          security_question: document.getElementById("securityQuestion").value,
          security_answer: document.getElementById("securityAnswer").value,
        }),
      });
      setupRequired = false;
    }
    const result = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({
        identifier: document.getElementById("ownerEmail").value,
        password: document.getElementById("ownerPassword").value,
      }),
    });
    token = result.token;
    localStorage.setItem("astha_owner_token", token);
    showApp();
  } catch (error) {
    authMessage.textContent = error.message;
  }
}

async function forgotPassword() {
  try {
    const identifier = prompt("Enter your ASTHA ERP username or email:");
    if (!identifier) return;
    const result = await api("/api/security-question", {
      method: "POST",
      body: JSON.stringify({ identifier }),
    });
    const answer = prompt(result.question);
    if (!answer) return;
    const newPassword = prompt("Enter your new password or PIN:");
    if (!newPassword) return;
    await api("/api/reset-password", {
      method: "POST",
      body: JSON.stringify({
        identifier,
        security_answer: answer,
        new_password: newPassword,
      }),
    });
    authMessage.textContent = "Password reset done. Login with your new password.";
  } catch (error) {
    authMessage.textContent = error.message;
  }
}

function showApp() {
  authPanel.classList.add("hidden");
  appPanel.classList.remove("hidden");
  loadView(currentView).catch((error) => {
    content.innerHTML = `<div class="card">${error.message}</div>`;
  });
}

function logout() {
  token = "";
  localStorage.removeItem("astha_owner_token");
  appPanel.classList.add("hidden");
  authPanel.classList.remove("hidden");
}

document.querySelectorAll(".sidebar button").forEach((btn) => {
  btn.addEventListener("click", () => loadView(btn.dataset.view));
});

document.getElementById("setupBtn").addEventListener("click", setupOwnerPassword);
document.getElementById("loginBtn").addEventListener("click", login);
document.getElementById("forgotBtn").addEventListener("click", forgotPassword);
document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("ownerPassword").addEventListener("keydown", (event) => {
  if (event.key === "Enter") login();
});

checkSetup().then(() => {
  if (token) showApp();
});
