'use strict';

function renderSCurveChart(canvasId, dates, pv, ev, ac) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                { label: 'PV (Valor Planejado)', data: pv, borderColor: 'rgba(59,130,246,1)', backgroundColor: 'transparent', tension: 0.4 },
                { label: 'EV (Valor Agregado)', data: ev, borderColor: 'rgba(16,185,129,1)', backgroundColor: 'transparent', tension: 0.4 },
                { label: 'AC (Custo Real)', data: ac, borderColor: 'rgba(239,68,68,1)', backgroundColor: 'transparent', tension: 0.4 },
            ],
        },
        options: { responsive: true, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true } } },
    });
}
