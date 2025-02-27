async function loadConfig() {
    try {
        const response = await fetch("/static/data/config.json");
        if (!response.ok) throw new Error("Ошибка загрузки config.json");

        const config = await response.json();
        if (!config.orcid_client_id || !config.redirect_uri) {
            throw new Error("Client ID или Redirect URI отсутствуют в config.json");
        }

        window.orcidConfig = config;
    } catch (error) {
        console.error("Ошибка загрузки конфигурации:", error.message);
    }
}

function startORCIDAuth() {
    if (!window.orcidConfig) {
        console.error("Конфигурация ORCID не загружена!");
        return;
    }

    const { orcid_client_id, redirect_uri } = window.orcidConfig;
    const orcidAuthUrl = `https://orcid.org/oauth/authorize?client_id=${orcid_client_id}&response_type=code&scope=/authenticate&redirect_uri=${redirect_uri}`;

    window.location.href = orcidAuthUrl;
}

window.startORCIDAuth = startORCIDAuth; // 🔥 Делаем доступной глобально

window.onload = async function () {
    await loadConfig();
};


async function getORCIDToken() {
    const authCode = new URLSearchParams(window.location.search).get("code");
    if (!authCode) return;

    try {
        const response = await fetch("http://127.0.0.1:5000/get_token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: authCode })
        });

        if (!response.ok) throw new Error("Ошибка при получении токена");

        const data = await response.json();
        console.log("Ответ сервера:", data);

        showUserInfo(data);
        window.history.replaceState({}, document.title, "/"); // Убираем "code" из URL
    } catch (error) {
        console.error("Ошибка соединения с сервером:", error.message);
    }
}

function showUserInfo(data) {
    const loginButton = document.getElementById("orcid-login");
    if (!loginButton) {
        console.error("Кнопка ORCID login не найдена!");
        return;
    }

    loginButton.innerHTML = `<b>🔹${data.name}</b>`;
    loginButton.style.cursor = "default";
    loginButton.onclick = (event) => event.preventDefault(); // Отключаем клик
}

// Загружаем конфиг перед запуском
window.onload = async function () {
    await loadConfig(); // Ждём загрузку конфига
    if (new URLSearchParams(window.location.search).has("code")) {
        getORCIDToken();
    }
};
