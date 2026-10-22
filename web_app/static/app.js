
"use strict";

// ============================================
// 1. Глобальні змінні
// ============================================

let showAllOperations = false;
let clustersChart = null;
let activityChart = null;


// ============================================
// 2. Helper: отримання JSON із сервера
// ============================================

async function fetchJSON(url) {
    const response = await fetch(url);

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Сервер повернув некоректну відповідь.");
    }

    if (!response.ok) {
        throw new Error(
            data.error || `Помилка сервера: ${response.status}`
        );
    }

    return data;
}


// ============================================
// 3. Допоміжні функції
// ============================================

function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString("uk-UA");
}


function escapeHTML(value) {
    const characters = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    };

    return String(value ?? "").replace(
        /[&<>"']/g,
        character => characters[character]
    );
}


function showError(container, message, colspan = null) {
    if (!container) {
        return;
    }

    const safeMessage = escapeHTML(message);

    if (colspan !== null) {
        container.innerHTML = `
            <tr>
                <td colspan="${colspan}" class="loading-cell">
                    ${safeMessage}
                </td>
            </tr>
        `;
    } else {
        container.innerHTML = `
            <p class="loading-cell">${safeMessage}</p>
        `;
    }
}


// ============================================
// 4. Перевірка статусу Flask API
// ============================================

async function checkServerStatus() {
    const statusElement = document.getElementById("server-status");

    if (!statusElement) {
        return;
    }

    statusElement.innerHTML = `
        <span class="status-dot"></span>
        Checking server...
    `;

    try {
        await fetchJSON("/api/health");

        statusElement.innerHTML = `
            <span
                class="status-dot"
                style="background: #16a36a;"
            ></span>
            Server Online
        `;
    } catch (error) {
        console.error("Помилка перевірки сервера:", error);

        statusElement.innerHTML = `
            <span
                class="status-dot"
                style="background: #dc3545;"
            ></span>
            Server Offline
        `;
    }
}


// ============================================
// 5. Dashboard: статистика та графіки
// ============================================

async function loadDashboardStats() {
    try {
        const stats = await fetchJSON("/api/dashboard-stats");

        // Оновлюємо картки статистики.

        const productsCount = document.getElementById("products-count");
        const usersCount = document.getElementById("users-count");
        const viewsCount = document.getElementById("views-count");
        const purchasesCount = document.getElementById("purchases-count");

        if (productsCount) {
            productsCount.textContent = formatNumber(stats.products);
        }

        if (usersCount) {
            usersCount.textContent = formatNumber(stats.users);
        }

        if (viewsCount) {
            viewsCount.textContent = formatNumber(stats.views);
        }

        if (purchasesCount) {
            purchasesCount.textContent = formatNumber(stats.purchases);
        }

        // Будуємо графіки, якщо Chart.js підключено.

        if (typeof Chart === "undefined") {
            console.error(
                "Chart.js не завантажився. Перевір його підключення в index.html."
            );
            return;
        }

        createClustersChart(stats.clusters || {});
        createActivityChart(stats);

    } catch (error) {
        console.error("Помилка завантаження Dashboard:", error);

        [
            "products-count",
            "users-count",
            "views-count",
            "purchases-count"
        ].forEach(id => {
            const element = document.getElementById(id);

            if (element) {
                element.textContent = "Помилка";
            }
        });
    }
}


// ============================================
// 5.1. Doughnut chart: розподіл кластерів
// ============================================

function createClustersChart(clusters) {
    const canvas = document.getElementById("clusters-chart");

    if (!canvas) {
        return;
    }

    const clusterEntries = Object.entries(clusters)
        .sort((a, b) => Number(a[0]) - Number(b[0]));

    const labels = clusterEntries.map(
        ([cluster]) => `Cluster ${cluster}`
    );

    const values = clusterEntries.map(
        ([, count]) => Number(count)
    );

    if (clustersChart) {
        clustersChart.destroy();
    }

    clustersChart = new Chart(canvas, {
        type: "doughnut",

        data: {
            labels: labels,

            datasets: [{
                label: "Users",
                data: values,
                borderWidth: 2,
                hoverOffset: 8
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: true,

            plugins: {
                legend: {
                    position: "bottom"
                },

                tooltip: {
                    callbacks: {
                        label(context) {
                            const total = values.reduce(
                                (sum, value) => sum + value,
                                0
                            );

                            const value = Number(context.raw);

                            const percentage = total > 0
                                ? (value / total * 100).toFixed(2)
                                : "0.00";

                            return (
                                `${context.label}: ` +
                                `${formatNumber(value)} користувачів ` +
                                `(${percentage}%)`
                            );
                        }
                    }
                }
            }
        }
    });
}


// ============================================
// 5.2. Bar chart: активність користувачів
// ============================================

function createActivityChart(stats) {
    const canvas = document.getElementById("activity-chart");

    if (!canvas) {
        return;
    }

    if (activityChart) {
        activityChart.destroy();
    }

    activityChart = new Chart(canvas, {
        type: "bar",

        data: {
            labels: [
                "Views",
                "Carts",
                "Purchases"
            ],

            datasets: [{
                label: "Кількість подій",

                data: [
                    Number(stats.views) || 0,
                    Number(stats.carts) || 0,
                    Number(stats.purchases) || 0
                ],

                borderWidth: 1
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: true,

            scales: {
                y: {
                    beginAtZero: true,

                    ticks: {
                        callback(value) {
                            return formatNumber(value);
                        }
                    }
                }
            },

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    callbacks: {
                        label(context) {
                            return formatNumber(context.raw);
                        }
                    }
                }
            }
        }
    });
}


// ============================================
// 6. Завантаження рекомендацій
// ============================================



async function loadRecommendations() {
    const tableBody = document.getElementById("recommendations-body");
    const refreshButton = document.getElementById("refresh-recommendations");
    const clusterFilter = document.getElementById("cluster-filter");
    const userIdInput = document.getElementById("recommendation-user-id");
    const typicalCheckFilter = document.getElementById("typical-check-filter");
    const maxPriceInput = document.getElementById("recommendation-max-price");
    const statusElement = document.getElementById("recommendation-filter-status");

    if (!tableBody) return;

    if (refreshButton) refreshButton.disabled = true;

    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="loading-cell">
                Завантаження рекомендацій...
            </td>
        </tr>
    `;

    if (statusElement) statusElement.textContent = "";

    try {
        const params = new URLSearchParams();

        const cluster = clusterFilter?.value || "all";
        const userId = userIdInput?.value.trim() || "";
        const useTypicalCheck = typicalCheckFilter?.checked || false;
        const maxPriceText = maxPriceInput?.value.trim() || "";

        if (cluster !== "all") {
            params.set("cluster", cluster);
        }

        if (userId) {
            params.set("user_id", userId);
        }

        if (useTypicalCheck) {
            params.set("use_typical_check", "true");
        }

        if (maxPriceText !== "") {
            params.set("max_price", maxPriceText);
        }

        const query = params.toString();
        const url = query
            ? `/api/recommendations?${query}`
            : "/api/recommendations";

        const data = await fetchJSON(url);
        const products = Array.isArray(data)
            ? data
            : data.recommendations;

        if (!Array.isArray(products)) {
            throw new Error("API не повернув список рекомендацій.");
        }

        tableBody.innerHTML = "";

        if (products.length === 0) {
            showError(
                tableBody,
                "За вибраними умовами товарів не знайдено.",
                7
            );
        } else {
            products.forEach(product => {
                const row = document.createElement("tr");

                const price = Number(product.average_price);
                const score = Number(product.score);

                const formattedPrice = Number.isFinite(price)
                    ? price.toLocaleString("uk-UA", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })
                    : "—";

                const formattedConversion = Number.isFinite(score)
                    ? `${(score * 100).toLocaleString("uk-UA", {
                        maximumFractionDigits: 1
                    })}%`
                    : "—";

                row.innerHTML = `
                    <td>${escapeHTML(product.product_id)}</td>
                    <td>${escapeHTML(product.category_code || "Unknown")}</td>
                    <td>${escapeHTML(product.brand || "Unknown")}</td>
                    <td>${formattedPrice}</td>
                    <td>${formatNumber(product.views)}</td>
                    <td>${formatNumber(product.purchases)}</td>
                    <td>${formattedConversion}</td>
                `;

                tableBody.appendChild(row);
            });
        }

        if (statusElement) {
            const parts = [];

            if (useTypicalCheck) {
                parts.push("Увімкнено типовий чек користувача");
            }

            if (maxPriceText !== "") {
                parts.push(`Максимальна ціна: ${maxPriceText}`);
            } else if (useTypicalCheck) {
                parts.push("Цінове обмеження взято з типового чека");
            }

            statusElement.textContent = parts.length
                ? parts.join(". ") + "."
                : "Ціновий фільтр вимкнено.";
        }

    } catch (error) {
        console.error("Помилка завантаження рекомендацій:", error);

        showError(
            tableBody,
            `Не вдалося завантажити рекомендації: ${error.message}`,
            7
        );

        if (statusElement) {
            statusElement.textContent = error.message;
        }
    } finally {
        if (refreshButton) refreshButton.disabled = false;
    }
}


// ============================================
// 7. Завантаження журналу операцій
// ============================================

async function loadOperations() {
    const operationsList = document.getElementById("operations-list");

    const refreshButton = document.getElementById("refresh-operations");

    if (!operationsList) {
        return;
    }

    if (refreshButton) {
        refreshButton.disabled = true;
    }

    operationsList.innerHTML = `
        <p class="loading-cell">
            Завантаження журналу операцій...
        </p>
    `;

    try {
        const data = await fetchJSON("/api/operations");

        const operations = Array.isArray(data)
            ? data
            : data.operations;

        if (!Array.isArray(operations)) {
            throw new Error(
                "API не повернув список операцій."
            );
        }

        operationsList.innerHTML = "";

        if (operations.length === 0) {
            operationsList.innerHTML = `
                <p class="loading-cell">
                    Операцій поки немає.
                </p>
            `;
            return;
        }

        const visibleOperations = showAllOperations
            ? operations
            : operations.slice(0, 5);

        visibleOperations.forEach(operation => {
            const item = document.createElement("article");
            item.className = "operation-item";

            const info = document.createElement("div");
            info.className = "operation-info";

            const title = document.createElement("p");
            title.className = "operation-title";
            title.textContent = operation.operation_type || "Operation";

            const details = document.createElement("p");
            details.className = "operation-details";

            const rawDetails = operation.details;

            if (
                rawDetails !== null &&
                typeof rawDetails === "object"
            ) {
                details.textContent = JSON.stringify(rawDetails);
            } else {
                details.textContent = rawDetails ?? "Без деталей";
            }

            const time = document.createElement("span");
            time.className = "operation-time";
            time.textContent = operation.created_at || "";

            info.appendChild(title);
            info.appendChild(details);

            item.appendChild(info);
            item.appendChild(time);

            operationsList.appendChild(item);
        });

        if (operations.length > 5) {
            const toggleButton = document.createElement("button");

            toggleButton.type = "button";
            toggleButton.className =
                "button button-secondary operation-toggle";

            toggleButton.textContent = showAllOperations
                ? "Згорнути ▲"
                : `Показати всі операції (${operations.length}) ▼`;

            toggleButton.addEventListener("click", () => {
                showAllOperations = !showAllOperations;
                loadOperations();
            });

            operationsList.appendChild(toggleButton);
        }

    } catch (error) {
        console.error(
            "Помилка завантаження операцій:",
            error
        );

        showError(
            operationsList,
            `Не вдалося завантажити журнал: ${error.message}`
        );
    } finally {
        if (refreshButton) {
            refreshButton.disabled = false;
        }
    }
}


// ============================================
// 8. Sorting: розбираємо список чисел
// ============================================

function parseNumbers(input) {
    const text = input.trim();

    if (!text) {
        throw new Error("Введи список чисел.");
    }

    const parts = text.split(/[,\s;]+/);

    return parts.map(part => {
        const number = Number(part);

        if (part === "" || !Number.isFinite(number)) {
            throw new Error(`Некоректне число: "${part}".`);
        }

        return number;
    });
}


// ============================================
// 9. Sorting: запит до Flask API
// ============================================


async function sortNumbers() {
    const input = document.getElementById("sort-input").value;
    const algorithm = document.getElementById("sort-algorithm").value;
    const result = document.getElementById("sort-result");

    const numbers = input
        .split(",")
        .map(value => value.trim())
        .filter(value => value !== "")
        .map(Number);

    if (
        numbers.length === 0 ||
        numbers.some(number => !Number.isFinite(number))
    ) {
        result.textContent = "Введи коректні числа через кому.";
        return;
    }

    try {
        const response = await fetch("/api/sort", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                numbers: numbers,
                algorithm: algorithm
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Не вдалося виконати сортування.");
        }

        result.textContent =
            "Початковий масив: " + data.original.join(", ") +
            "\nВідсортований масив: " + data.sorted.join(", ");

    } catch (error) {
        console.error("Помилка сортування:", error);
        result.textContent = "Помилка: " + error.message;
    }
}



// ============================================
// 10. Загальна функція POST JSON
// ============================================

async function postJSON(url, body) {
    const response = await fetch(url, {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(body)
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Сервер повернув некоректну відповідь.");
    }

    if (!response.ok) {
        throw new Error(
            data.error || `Помилка сервера: ${response.status}`
        );
    }

    return data;
}


// ============================================
// 11. Searching: запит до Flask API
// ============================================

async function searchNumber() {
    const input = document.getElementById("search-input");
    const targetInput = document.getElementById("search-target");

    const algorithmSelect = document.getElementById(
        "search-algorithm"
    );

    const resultElement = document.getElementById("search-result");
    const button = document.getElementById("search-button");

    if (
        !input ||
        !targetInput ||
        !algorithmSelect ||
        !resultElement
    ) {
        return;
    }

    try {
        const numbers = parseNumbers(input.value);
        const targetText = targetInput.value.trim();

        if (targetText === "") {
            throw new Error("Введи число, яке потрібно знайти.");
        }

        const target = Number(targetText);

        if (!Number.isFinite(target)) {
            throw new Error("Цільове значення має бути числом.");
        }

        const algorithm = algorithmSelect.value;

        if (button) {
            button.disabled = true;
        }

        resultElement.textContent = "Пошук...";

        const data = await postJSON("/api/search", {
            numbers,
            target,
            algorithm
        });

        const algorithmName = algorithm === "linear"
            ? "Linear Search"
            : "Binary Search";

        if (data.found) {
            resultElement.textContent =
                `${algorithmName}\n` +
                `Знайдено число: ${data.target}\n` +
                `Індекс: ${data.index}`;
        } else {
            resultElement.textContent =
                `${algorithmName}\n` +
                `Число ${data.target} не знайдено.\n` +
                `Індекс: -1`;
        }

        await loadOperations();

    } catch (error) {
        resultElement.textContent = `Помилка: ${error.message}`;
    } finally {
        if (button) {
            button.disabled = false;
        }
    }
}


// ============================================
// 12. Queue та Stack
// ============================================

async function updateStructure(type) {
    const data = await fetchJSON(`/api/${type}`);

    const itemsElement = document.getElementById(`${type}-items`);
    const sizeElement = document.getElementById(`${type}-size`);

    if (!itemsElement || !sizeElement) {
        return;
    }

    itemsElement.replaceChildren();

    // Для стека показуємо вершину першою.
    const items = type === "stack"
        ? [...data.items].reverse()
        : data.items;

    items.forEach((item, index) => {
        const li = document.createElement("li");
        li.textContent = item;

        if (type === "stack" && index === 0) {
            li.textContent = `${item} (TOP)`;
        }

        itemsElement.appendChild(li);
    });

    sizeElement.textContent = data.size;
}


async function submitStructureAction(url, item = null) {
    const options = {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        }
    };

    if (item !== null) {
        options.body = JSON.stringify({ item });
    }

    const response = await fetch(url, options);

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Сервер повернув некоректну відповідь.");
    }

    if (!response.ok) {
        throw new Error(data.error || "Операція не вдалася.");
    }

    return data;
}


function setStructureMessage(type, message, isError = false) {
    const element = document.getElementById(`${type}-message`);

    if (!element) {
        return;
    }

    element.textContent = message;
    element.classList.toggle("error-message", isError);
}


function setupStructure(type) {
    const form = document.getElementById(`${type}-form`);
    const input = document.getElementById(`${type}-input`);

    const actionButton = document.getElementById(
        type === "queue" ? "queue-dequeue" : "stack-pop"
    );

    if (!form || !input || !actionButton) {
        return;
    }

    const addAction = type === "queue" ? "enqueue" : "push";
    const removeAction = type === "queue" ? "dequeue" : "pop";

    form.addEventListener("submit", async event => {
        event.preventDefault();

        const item = input.value.trim();

        if (!item) {
            setStructureMessage(
                type,
                "Введи назву елемента.",
                true
            );
            return;
        }

        try {
            await submitStructureAction(
                `/api/${type}/${addAction}`,
                item
            );

            input.value = "";

            setStructureMessage(type, "Елемент успішно додано.");

            await updateStructure(type);
            await loadOperations();

        } catch (error) {
            setStructureMessage(type, error.message, true);
        }
    });

    actionButton.addEventListener("click", async () => {
        try {
            const data = await submitStructureAction(
                `/api/${type}/${removeAction}`
            );

            setStructureMessage(
                type,
                `Видалено: ${data.removed}`
            );

            await updateStructure(type);
            await loadOperations();

        } catch (error) {
            setStructureMessage(type, error.message, true);
        }
    });
}


// ============================================
// 13. Ініціалізація всіх компонентів
// ============================================

document.addEventListener("DOMContentLoaded", async () => {
    // Статус сервера та основний Dashboard.
    checkServerStatus();
    loadDashboardStats();

    // Таблиці.
    loadRecommendations();
    loadOperations();

    // Algorithms Lab.
    document
        .getElementById("sort-button")
        ?.addEventListener("click", sortNumbers);

    document
        .getElementById("search-button")
        ?.addEventListener("click", searchNumber);

    // Кнопки оновлення.
    document
        .getElementById("refresh-recommendations")
        ?.addEventListener("click", loadRecommendations);

    document
        .getElementById("cluster-filter")
        ?.addEventListener("change", loadRecommendations);
    
    document
        .getElementById("typical-check-filter")
        ?.addEventListener("change", loadRecommendations);

    document
        .getElementById("recommendation-max-price")
        ?.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                loadRecommendations();
            }
        });

    document
        .getElementById("refresh-operations")
        ?.addEventListener("click", loadOperations);

    // Queue та Stack.
    setupStructure("queue");
    setupStructure("stack");

    for (const type of ["queue", "stack"]) {
        try {
            await updateStructure(type);
        } catch (error) {
            setStructureMessage(type, error.message, true);
        }
    }

    // Активний пункт навігації.
    document.querySelectorAll(".navigation .nav-link").forEach(link => {
        link.addEventListener("click", () => {
            document
                .querySelectorAll(".navigation .nav-link")
                .forEach(item => item.classList.remove("active"));

            link.classList.add("active");
        });
    });
});
