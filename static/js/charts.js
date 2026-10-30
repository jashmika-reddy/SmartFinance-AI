// SmartFinance AI - Chart.js Visualizations Controller (INR / Indian Rupee)

// Centralized Indian Rupee Formatter for JavaScript Charts & UI
function formatINR(val, decimals = 2) {
    if (val === null || val === undefined || isNaN(val)) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(Number(val));
}

function formatINRCompact(val) {
    if (val === null || val === undefined || isNaN(val)) return '₹0';
    const num = Math.abs(Number(val));
    const sign = Number(val) < 0 ? '-' : '';
    if (num >= 10000000) return `${sign}₹${(num / 10000000).toFixed(2)} Cr`;
    if (num >= 100000) return `${sign}₹${(num / 100000).toFixed(2)} L`;
    if (num >= 1000) return `${sign}₹${(num / 1000).toFixed(1)} k`;
    return `${sign}₹${num.toFixed(0)}`;
}

// Global Chart default styling for dark theme
if (window.Chart) {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = '#1e293b';
    Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
    Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
    Chart.defaults.plugins.tooltip.borderColor = '#334155';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
}

// 1. Initialize Cashflow Monthly Trend Chart
function initCashflowChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    fetch('/api/v1/chart/cashflow')
        .then(res => res.json())
        .then(data => {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Income (Inflow)',
                            data: data.income,
                            backgroundColor: 'rgba(16, 185, 129, 0.75)',
                            borderColor: '#10b981',
                            borderWidth: 1,
                            borderRadius: 6,
                            maxBarThickness: 36
                        },
                        {
                            label: 'Expenses (Outflow)',
                            data: data.expense,
                            backgroundColor: 'rgba(239, 68, 68, 0.75)',
                            borderColor: '#ef4444',
                            borderWidth: 1,
                            borderRadius: 6,
                            maxBarThickness: 36
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { boxWidth: 12, font: { weight: 600 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ${ctx.dataset.label}: ${formatINR(ctx.raw)}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false }
                        },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: {
                                callback: val => formatINRCompact(val)
                            }
                        }
                    }
                }
            });
        })
        .catch(err => console.error('Cashflow chart error:', err));
}

// 2. Initialize Category Spending Doughnut Chart
function initCategoryChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    fetch('/api/v1/chart/categories')
        .then(res => res.json())
        .then(data => {
            if (!data.labels || data.labels.length === 0) {
                ctx.parentElement.innerHTML = '<div class="flex items-center justify-center h-48 text-gray-500 text-sm">No expense records found.</div>';
                return;
            }

            const palette = [
                '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6',
                '#8b5cf6', '#14b8a6', '#f97316', '#06b6d4', '#64748b'
            ];

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.values,
                        backgroundColor: palette.slice(0, data.labels.length),
                        borderColor: '#0f172a',
                        borderWidth: 2,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 10,
                                font: { size: 11, weight: 500 },
                                padding: 12
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ${ctx.label}: ${formatINR(ctx.raw)}`
                            }
                        }
                    }
                }
            });
        })
        .catch(err => console.error('Category chart error:', err));
}

// 3. Initialize Debt Payoff Comparison Chart (Avalanche vs Snowball)
let debtChartInstance = null;
function initDebtPayoffChart(canvasId, labels, avalancheData, snowballData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (debtChartInstance) {
        debtChartInstance.destroy();
    }

    debtChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Debt Avalanche (Optimal APR)',
                    data: avalancheData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: false,
                    tension: 0.25,
                    borderWidth: 2.5,
                    pointRadius: 2,
                    pointHoverRadius: 5
                },
                {
                    label: 'Debt Snowball (Lowest Balance)',
                    data: snowballData,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: false,
                    tension: 0.25,
                    borderWidth: 2.5,
                    borderDash: [5, 5],
                    pointRadius: 2,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 14, font: { weight: 600 } }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${formatINR(ctx.raw)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        callback: val => formatINRCompact(val)
                    }
                }
            }
        }
    });
}

// 4. Initialize Monte Carlo Simulation Confidence Fan Chart
let mcChartInstance = null;
function initMonteCarloChart(canvasId, scenarioKey) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    fetch(`/api/v1/chart/monte-carlo?scenario=${scenarioKey}`)
        .then(res => res.json())
        .then(data => {
            if (mcChartInstance) {
                mcChartInstance.destroy();
            }

            const monthLabels = data.months.map(m => `Month ${m}`);

            mcChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: monthLabels,
                    datasets: [
                        {
                            label: '90th Percentile (Optimistic)',
                            data: data.p90,
                            borderColor: '#38bdf8',
                            backgroundColor: 'rgba(56, 189, 248, 0.08)',
                            fill: '+1',
                            tension: 0.3,
                            borderWidth: 1.5,
                            pointRadius: 0
                        },
                        {
                            label: '50th Percentile (Median Path)',
                            data: data.p50,
                            borderColor: '#818cf8',
                            backgroundColor: 'transparent',
                            fill: false,
                            tension: 0.3,
                            borderWidth: 3,
                            pointRadius: 3
                        },
                        {
                            label: '10th Percentile (Pessimistic Stress)',
                            data: data.p10,
                            borderColor: '#f43f5e',
                            backgroundColor: 'rgba(244, 63, 94, 0.12)',
                            fill: '-1',
                            tension: 0.3,
                            borderWidth: 1.5,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { boxWidth: 12 }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ${ctx.dataset.label}: ${formatINR(ctx.raw)}`
                            }
                        }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: {
                                callback: val => formatINRCompact(val)
                            }
                        }
                    }
                }
            });

            // Update stats cards in UI if available
            const insolvEl = document.getElementById('mc-insolvency-prob');
            if (insolvEl) insolvEl.innerText = `${data.insolvency_probability}%`;

            const medianEl = document.getElementById('mc-median-wealth');
            if (medianEl) medianEl.innerText = formatINR(data.final_median_wealth);

            const minEl = document.getElementById('mc-min-wealth');
            if (minEl) minEl.innerText = formatINR(data.min_observed_wealth);
        })
        .catch(err => console.error('Monte Carlo chart error:', err));
}
