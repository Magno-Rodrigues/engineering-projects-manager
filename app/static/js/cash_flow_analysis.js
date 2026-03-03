'use strict';

function renderSeasonalChart(canvasId, months, avgInflows, avgOutflows) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [
                { label: 'Média Entradas', data: avgInflows, backgroundColor: 'rgba(16,185,129,0.7)', borderColor: 'rgba(16,185,129,1)', borderWidth: 1 },
                { label: 'Média Saídas', data: avgOutflows, backgroundColor: 'rgba(239,68,68,0.7)', borderColor: 'rgba(239,68,68,1)', borderWidth: 1 },
            ],
        },
        options: { responsive: true, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true } } },
    });
}
