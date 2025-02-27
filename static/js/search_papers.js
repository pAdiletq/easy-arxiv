async function searchPapers() {
    const topic = document.getElementById('searchInput').value;
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="flex justify-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-700"></div></div>';

    try {
        const response = await fetch('/api/search?topic=' + encodeURIComponent(topic));
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.papers.length === 0) {
            resultsDiv.innerHTML = '<div class="text-center p-8 bg-white rounded-lg shadow-md"><p class="text-gray-600 text-lg">No papers found. Try another topic! 🔍</p></div>';
            return;
        }
        
        // Papers
        let resultsHTML = data.papers.map(paper => `
            <div class="bg-white rounded-lg shadow-lg hover:shadow-xl transition-all p-6">
                <h2 class="text-2xl font-bold text-violet-700 mb-2">${paper.title}</h2>
                <p class="text-gray-600 mb-2">👥 Authors: ${paper.authors.join(', ')}</p>
                <p class="text-gray-800 mb-4">${paper.summary}</p>
                <div class="flex flex-wrap gap-2 mb-4">
                    ${paper.keywords.map(keyword => `
                        <span class="px-3 py-1 bg-violet-100 text-violet-700 rounded-full text-sm">
                            ${keyword}
                        </span>
                    `).join('')}
                </div>
                <div class="flex flex-wrap gap-4 items-center justify-between">
                    <div class="flex gap-2">
                        <button onclick="readWithTTS('${paper.summary.replace(/'/g, "\\'")}')" 
                                class="px-4 py-2 bg-violet-100 text-violet-700 rounded-lg hover:bg-violet-200 transition-all">
                            🎧 Read with TTS
                        </button>
                        <a href="${paper.pdf_link}" target="_blank" 
                           class="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-all">
                            📄 PDF Article
                        </a>
                        <button onclick="startAIquest('${paper.pdf_link}')"
                                class="px-4 py-2 bg-violet-100 text-violet-700 rounded-lg hover:bg-violet-200 transition-all">
                            🤖 AI Quest
                        </button>
                    </div>
                    <div class="text-sm text-gray-500">
                        <span>📅 ${new Date(paper.published).toLocaleDateString()}</span>
                        <span class="ml-4">⏱️ ${paper.reading_time}</span>
                    </div>
                </div>
            </div>
        `).join('');

        resultsDiv.innerHTML = resultsHTML;
    } catch (error) {
        resultsDiv.innerHTML = '<div class="text-center p-8 bg-white rounded-lg shadow-md"><p class="text-red-600 text-lg">Error fetching papers. Please try again! ⚠️</p></div>';
    }
}

function setExampleTopic(topic) {
    document.getElementById('searchInput').value = topic;
    searchPapers();
}

let topicSuggestions = []; // Глобальная переменная для хранения тем
let debounceTimer; // Хранит ID таймера

async function loadTopics() {
    if (topicSuggestions.length > 0) return; // Если темы уже загружены, повторно не загружаем

    try {
        let response = await fetch("/static/data/title.json"); // Загружаем из JSON
        if (!response.ok) throw new Error("Ошибка загрузки данных");

        let data = await response.json();
        //  console.log("Raw JSON data:", data); // Проверка структуры JSON

        if (data.categories && Array.isArray(data.categories)) {
            topicSuggestions = data.categories.map(item => item.title || '');
        } else {
            topicSuggestions = [];
        }

        //console.log("Темы загружены:", topicSuggestions); // Проверка загруженных данных
    } catch (error) {
        console.error("Ошибка загрузки тем:", error);
    }
}

// Загружаем темы один раз при загрузке страницы
window.onload = loadTopics;

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const suggestionsBox = document.getElementById('suggestions');

    // Обработчик ввода с дебаунсом (чтобы не было спама вызовов)
    searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer); // Очищаем предыдущий таймер

        debounceTimer = setTimeout(() => {
            filterSuggestions(); // Запускаем фильтрацию через 300 мс
        }, 300);
    });

    function filterSuggestions() {
        const searchText = searchInput.value.toLowerCase();
        if (!searchText) {
            suggestionsBox.style.display = 'none';
            return;
        }

        //console.log("Фильтруем по:", searchText);

        const filteredData = topicSuggestions
            .filter(item => typeof item === 'string' || typeof item === 'number') // Фильтруем только строки/числа
            .map(item => String(item)) // Преобразуем всё в строки
            .filter(item => item.toLowerCase().includes(searchText)); // Фильтрация

        showSuggestions(filteredData);
    }

    function showSuggestions(data) {
        suggestionsBox.innerHTML = '';
        if (!data || data.length === 0) {
            suggestionsBox.style.display = 'none';
            return;
        }

        data.forEach((item) => {
            const div = document.createElement('div');
            div.classList.add('suggestion');
            div.textContent = item;
            div.addEventListener('click', () => {
                searchInput.value = item;
                suggestionsBox.style.display = 'none';
                searchPapers(); // Автоматический запуск поиска
            });
            suggestionsBox.appendChild(div);
        });

        suggestionsBox.style.display = 'block';
    }

    // Прячем подсказки при клике вне поля
    document.addEventListener('click', (event) => {
        if (!searchInput.contains(event.target) && !suggestionsBox.contains(event.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
});
function showSuggestions(data) {
    suggestionsBox.innerHTML = '';
    if (!data || data.length === 0) {
        suggestionsBox.style.display = 'none';
        return;
    }

    data.forEach(item => {
        const div = document.createElement('div');
        div.classList.add('suggestion');
        div.textContent = item;
        div.addEventListener('click', () => {
            searchInput.value = item;
            suggestionsBox.style.display = 'none';
        });

        suggestionsBox.appendChild(div);
    });

    suggestionsBox.style.display = 'block';
}
