function startORCIDAuth() {
    const clientId = "APP-62MCKIVIJOU0UD0U";
    const redirectUri = "http://127.0.0.1:8000/callback";
    const orcidAuthUrl = `https://orcid.org/oauth/authorize?client_id=${clientId}&response_type=code&scope=/authenticate&redirect_uri=${redirectUri}`;

    window.location.href = orcidAuthUrl;
}

async function getORCIDToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const authCode = urlParams.get("code");

    if (!authCode) {
        alert("Ошибка: Код авторизации не найден!");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/get_token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: authCode })
        });

        const data = await response.json();

        if (response.ok) {
            showUserInfo(data);
        } else {
            alert("Ошибка при получении токена!");
        }
    } catch (error) {
        alert("Ошибка соединения с сервером!");
    }
}

function showUserInfo(data) {
    document.getElementById("user-info").innerHTML = `
        <pre>
<b>access_token</b>: ${data.access_token}
<b>expires_in</b>: ${data.expires_in}
<b>name</b>: ${data.name || "Неизвестный"}
<b>orcid</b>: ${data.orcid}
<b>refresh_token</b>: ${data.refresh_token}
<b>scope</b>: ${data.scope}
<b>token_type</b>: ${data.token_type}
        </pre>
    `;
}

// Если в URL есть код авторизации, автоматически получаем данные
if (new URLSearchParams(window.location.search).has("code")) {
    getORCIDToken();
}
