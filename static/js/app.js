function startAIquest(pdfUrl) {
    const aiQuestUrl = `/ai_quest?pdf=${encodeURIComponent(pdfUrl)}`;
    window.open(aiQuestUrl, '_blank');
}