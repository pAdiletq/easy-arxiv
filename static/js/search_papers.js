async function searchPapers() {
    const topic = document.getElementById('searchInput').value;
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="flex justify-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-700"></div></div>';

    try {
        const response = await fetch('/api/search?topic=' + encodeURIComponent(topic));
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