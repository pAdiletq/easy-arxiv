// Initialize Chart.js
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('arxivStats').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.8)');   // violet-500
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0.2)');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024],
            datasets: [{
                label: 'Papers Published',
                data: [1200, 5000, 12000, 20000, 40000, 90000, 150000, 220000],
                backgroundColor: gradient,
                borderColor: 'rgb(139, 92, 246)',
                borderWidth: 1,
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#6d28d9',
                    bodyColor: '#6d28d9',
                    bodyFont: {
                        size: 14
                    },
                    padding: 12,
                    borderColor: 'rgb(139, 92, 246)',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
});