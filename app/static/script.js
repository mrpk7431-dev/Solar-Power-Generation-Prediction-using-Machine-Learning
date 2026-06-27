// =========================================================
//  AI PAGE LOAD ANIMATION CONTROLLER
// =========================================================
(function () {
    const phases = [
        { pct: 15,  msg: 'Initializing AI Model...' },
        { pct: 38,  msg: 'Loading Solar Dataset...' },
        { pct: 60,  msg: 'Calibrating Sensors...' },
        { pct: 80,  msg: 'Running Neural Network...' },
        { pct: 100, msg: 'System Ready ✓' }
    ];

    let phaseIdx = 0;

    function runPhase() {
        if (phaseIdx >= phases.length) {
            // All done — hide loader, reveal dashboard with entrance animation
            setTimeout(() => {
                const overlay = document.getElementById('ai-loader');
                if (overlay) overlay.classList.add('hidden');

                // Add slide-in entrance classes to panels
                const inputPanel  = document.getElementById('input-view');
                const outputPanel = document.getElementById('output-view');
                if (inputPanel)  inputPanel.classList.add('panel-enter-left');
                if (outputPanel) outputPanel.classList.add('panel-enter-right');

                // Remove classes after animation ends so they don't replay
                setTimeout(() => {
                    if (inputPanel)  inputPanel.classList.remove('panel-enter-left');
                    if (outputPanel) outputPanel.classList.remove('panel-enter-right');
                }, 900);
            }, 300);
            return;
        }

        const phase   = phases[phaseIdx];
        const bar     = document.getElementById('ai-progress-bar');
        const pctText = document.getElementById('ai-progress-pct');
        const status  = document.getElementById('ai-loader-status');

        if (bar)     bar.style.width = phase.pct + '%';
        if (pctText) pctText.textContent = phase.pct + '%';
        if (status)  status.textContent  = phase.msg;

        phaseIdx++;
        const delay = phaseIdx === phases.length ? 500 : 450;
        setTimeout(runPhase, delay);
    }

    // Start after a short initial pause
    window.addEventListener('load', () => setTimeout(runPhase, 300));
})();

document.addEventListener('DOMContentLoaded', () => {

    // Particle system disabled to remove all animations

    // =========================================================
    //  DOM REFERENCES
    // =========================================================
    const form = document.getElementById('prediction-form');
    const resetBtn = document.getElementById('reset-btn');
    const predictBtn = document.getElementById('predict-btn');
    const backBtn = document.getElementById('back-btn');
    const btnText = predictBtn.querySelector('.btn-text');
    const spinner = predictBtn.querySelector('.spinner');

    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsContent = document.getElementById('results-content');

    const totalEnergyElement = document.getElementById('total-energy-value');
    const powerStartElement = document.getElementById('power-value-start');
    const powerEndElement = document.getElementById('power-value-end');
    const homesStartElement = document.getElementById('homes-value-start');
    const homesEndElement = document.getElementById('homes-value-end');
    const ratioStartElement = document.getElementById('ratio-value-start');
    const ratioEndElement = document.getElementById('ratio-value-end');

    const statusStart = document.getElementById('generation-status-start');
    const statusEnd = document.getElementById('generation-status-end');

    const gaugeProgressStart = document.getElementById('gauge-progress-start');
    const gaugeProgressEnd = document.getElementById('gauge-progress-end');
    const insightDescription = document.getElementById('insight-description');

    const chartSvg = document.getElementById('generation-chart');
    const chartXLabels = document.getElementById('chart-x-labels');

    const MAX_DASH_OFFSET = 353.43;

    // =========================================================
    //  SLIDER CONFIG + DYNAMIC PROGRESS FILL
    // =========================================================
    const sliders = [
        { id: 'irradiation_start', suffix: ' W/m²', decimals: 2 },
        { id: 'irradiation_end', suffix: ' W/m²', decimals: 2 },
        { id: 'temperature_start', suffix: ' °C', decimals: 0 },
        { id: 'temperature_end', suffix: ' °C', decimals: 0 },
        { id: 'humidity_start', suffix: ' %', decimals: 0 },
        { id: 'humidity_end', suffix: ' %', decimals: 0 }
    ];

    function updateSliderBg(inputEl) {
        const val = parseFloat(inputEl.value);
        const min = parseFloat(inputEl.min) || 0;
        const max = parseFloat(inputEl.max) || 100;
        const pct = ((val - min) / (max - min)) * 100;
        inputEl.style.background = `linear-gradient(to right, #00D4FF 0%, #00D4FF ${pct}%, #121A2E ${pct}%, #121A2E 100%)`;
    }

    sliders.forEach(slider => {
        const inputEl = document.getElementById(slider.id);
        const displayEl = document.getElementById(`${slider.id}-val`);

        if (inputEl && displayEl) {
            const updateLabel = (val) => {
                displayEl.textContent = val.toFixed(slider.decimals);
            };

            inputEl.addEventListener('input', () => {
                updateLabel(parseFloat(inputEl.value));
                updateSliderBg(inputEl);
            });

            // Init on load
            updateLabel(parseFloat(inputEl.value));
            updateSliderBg(inputEl);
        }
    });

    // =========================================================
    //  VIEW SWITCHING HELPERS
    // =========================================================
    function switchView(showId) {
        document.querySelectorAll('.view-panel').forEach(v => v.classList.remove('active'));
        document.getElementById(showId).classList.add('active');
    }

    // =========================================================
    //  RESET BUTTON
    // =========================================================
    resetBtn.addEventListener('click', () => {
        form.reset();

        document.getElementById('irradiation_start-val').textContent = '0.00';
        document.getElementById('irradiation_end-val').textContent = '0.80';
        document.getElementById('temperature_start-val').textContent = '20';
        document.getElementById('temperature_end-val').textContent = '30';
        document.getElementById('humidity_start-val').textContent = '0';
        document.getElementById('humidity_end-val').textContent = '60';
        document.getElementById('hour_start').value = '9';
        document.getElementById('hour_end').value = '17';

        resultsContent.classList.add('hidden');
        resultsPlaceholder.classList.remove('hidden');
        switchView('input-view');

        if (gaugeProgressStart) gaugeProgressStart.style.strokeDashoffset = MAX_DASH_OFFSET;
        if (gaugeProgressEnd) gaugeProgressEnd.style.strokeDashoffset = MAX_DASH_OFFSET;

        chartSvg.innerHTML = '';
        chartXLabels.innerHTML = '';

        setTimeout(() => {
            sliders.forEach(slider => {
                const inputEl = document.getElementById(slider.id);
                if (inputEl) updateSliderBg(inputEl);
            });
        }, 50);
    });

    // =========================================================
    //  BACK BUTTON
    // =========================================================
    if (backBtn) {
        backBtn.addEventListener('click', () => switchView('input-view'));
    }

    // =========================================================
    //  FORM SUBMIT — AI PREDICTION
    // =========================================================
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const irradStart = parseFloat(document.getElementById('irradiation_start').value);
        const irradEnd = parseFloat(document.getElementById('irradiation_end').value);
        const tempStart = parseFloat(document.getElementById('temperature_start').value);
        const tempEnd = parseFloat(document.getElementById('temperature_end').value);
        const humidityStart = parseFloat(document.getElementById('humidity_start').value);
        const humidityEnd = parseFloat(document.getElementById('humidity_end').value);

        const hourStartInput = document.getElementById('hour_start');
        const hourEndInput = document.getElementById('hour_end');
        let hourStart = parseInt(hourStartInput.value);
        let hourEnd = parseInt(hourEndInput.value);

        if (isNaN(hourStart) || hourStart < 0 || hourStart > 23) {
            hourStartInput.focus();
            alert('Please enter a valid start hour (0–23).');
            return;
        }
        if (isNaN(hourEnd) || hourEnd < 0 || hourEnd > 23) {
            hourEndInput.focus();
            alert('Please enter a valid end hour (0–23).');
            return;
        }

        if (hourStart > hourEnd) {
            [hourStart, hourEnd] = [hourEnd, hourStart];
            hourStartInput.value = hourStart;
            hourEndInput.value = hourEnd;
        }

        // Loading state
        predictBtn.disabled = true;
        btnText.style.opacity = '0';
        spinner.classList.remove('hidden');

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    irradiation_start: irradStart,
                    irradiation_end: irradEnd,
                    temperature_start: tempStart,
                    temperature_end: tempEnd,
                    humidity_start: humidityStart,
                    humidity_end: humidityEnd,
                    hour_start: hourStart,
                    hour_end: hourEnd
                })
            });

            if (!response.ok) throw new Error('API failed');
            const data = await response.json();
            renderDashboardResults(data, irradStart, irradEnd, tempStart, tempEnd, hourStart, hourEnd);

        } catch (error) {
            console.error('Prediction error, using fallback:', error);

            const hoursList = [];
            for (let h = hourStart; h <= hourEnd; h++) hoursList.push(h);
            const numSteps = hoursList.length;
            const hourlyData = [];
            let totalEnergy = 0.0;

            hoursList.forEach((h, idx) => {
                const t = numSteps > 1 ? idx / (numSteps - 1) : 0.0;
                const h_irrad = irradStart + t * (irradEnd - irradStart);
                const h_temp = tempStart + t * (tempEnd - tempStart);
                const timeFactor = (h >= 6 && h <= 19) ? Math.sin((h - 6) / 13.0 * Math.PI) : 0.0;
                const tempLoss = Math.max(0, (h_temp + (h_irrad * 25.0) - 25) * 0.004);
                let power = Math.max(0.0, h_irrad * 1400 * (1 - tempLoss) * timeFactor + (Math.random() * 6 - 3));
                power = Math.max(0.0, power);
                hourlyData.push({ hour: h, power: roundTo(power, 2), irradiation: h_irrad, temperature: h_temp });
                totalEnergy += power;
            });

            renderDashboardResults({
                predicted_power_start: hourlyData[0].power,
                predicted_power_end: hourlyData[hourlyData.length - 1].power,
                total_energy_kwh: roundTo(totalEnergy, 2),
                hourly_data: hourlyData
            }, irradStart, irradEnd, tempStart, tempEnd, hourStart, hourEnd);
        } finally {
            predictBtn.disabled = false;
            btnText.style.opacity = '1';
            spinner.classList.add('hidden');
        }
    });

    // =========================================================
    //  RENDER RESULTS
    // =========================================================
    function renderDashboardResults(data, irradStart, irradEnd, tempStart, tempEnd, hourStart, hourEnd) {
        switchView('output-view');
        resultsPlaceholder.classList.add('hidden');
        resultsContent.classList.remove('hidden');

        const powerStart = data.predicted_power_start;
        const powerEnd = data.predicted_power_end;
        const totalEnergy = data.total_energy_kwh;
        const hourlyData = data.hourly_data;

        // Animate values with counting effect
        totalEnergyElement.classList.add('counting');
        animateValue(totalEnergyElement, totalEnergy, 2, 'energy');
        
        powerStartElement.classList.add('counting');
        animateValue(powerStartElement, powerStart, 2, 'default');
        
        powerEndElement.classList.add('counting');
        animateValue(powerEndElement, powerEnd, 2, 'default');

        const homesStart = Math.floor(powerStart / 1.2);
        const homesEnd = Math.floor(powerEnd / 1.2);
        
        homesStartElement.classList.add('counting');
        animateValue(homesStartElement, homesStart, 0, 'homes');
        
        homesEndElement.classList.add('counting');
        animateValue(homesEndElement, homesEnd, 0, 'homes');

        // Capacity ratios
        const maxCapacity = 1400.0;
        const ratioStart = Math.min(100, Math.max(0, (powerStart / maxCapacity) * 100));
        const ratioEnd = Math.min(100, Math.max(0, (powerEnd / maxCapacity) * 100));

        if (gaugeProgressStart) {
            gaugeProgressStart.style.strokeDashoffset = MAX_DASH_OFFSET - (MAX_DASH_OFFSET * (ratioStart / 100.0));
        }
        if (gaugeProgressEnd) {
            gaugeProgressEnd.style.strokeDashoffset = MAX_DASH_OFFSET - (MAX_DASH_OFFSET * (ratioEnd / 100.0));
        }

        ratioStartElement.textContent = ratioStart.toFixed(1) + '%';
        ratioEndElement.textContent = ratioEnd.toFixed(1) + '%';

        updateStatusBadge(statusStart, powerStart);
        updateStatusBadge(statusEnd, powerEnd);

        drawSVGChart(hourlyData, hourStart, hourEnd);

        // Insights
        const numHours = hourEnd - hourStart;
        let insightMsg = '';
        if (totalEnergy < 5) {
            insightMsg = `System standby. Total energy between ${hourStart}:00–${hourEnd}:00 is minimal (${totalEnergy.toFixed(1)} kWh) due to night hours or zero irradiation.`;
        } else {
            insightMsg = `The solar plant generated ${totalEnergy.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kWh of clean energy over this ${numHours}-hour interval. `;
            const diff = powerEnd - powerStart;
            if (diff > 5) {
                insightMsg += `Output climbed from ${powerStart.toFixed(1)} kW → ${powerEnd.toFixed(1)} kW (+${diff.toFixed(1)} kW) as solar irradiation increased.`;
            } else if (diff < -5) {
                insightMsg += `Output declined from ${powerStart.toFixed(1)} kW → ${powerEnd.toFixed(1)} kW (−${Math.abs(diff).toFixed(1)} kW) due to fading solar conditions.`;
            } else {
                insightMsg += `Power maintained stable baseline averaging ${((powerStart + powerEnd) / 2).toFixed(1)} kW.`;
            }
        }
        insightDescription.textContent = insightMsg;
    }

    // =========================================================
    //  SVG CHART — Smooth Curve with Area Fill
    // =========================================================
    function drawSVGChart(hourlyData, hourStart, hourEnd) {
        chartSvg.innerHTML = '';
        chartXLabels.innerHTML = '';
        if (!hourlyData || hourlyData.length === 0) return;

        const svgW = 800, svgH = 180;
        const padLeft = 50, padRight = 20, padTop = 15, padBottom = 25;
        const chartW = svgW - padLeft - padRight;
        const chartH = svgH - padTop - padBottom;

        const maxValInSeries = Math.max(...hourlyData.map(d => d.power));
        const maxScaleY = Math.max(100.0, maxValInSeries * 1.2);

        // Defs
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

        const lineGrad = createSVGGradient('chart-gradient', [
            { offset: '0%', color: '#FFBF00' },
            { offset: '100%', color: '#FFF78D' }
        ], 'horizontal');

        const fillGrad = createSVGGradient('chart-fill-gradient', [
            { offset: '0%', color: '#FFBF00', opacity: '0.2' },
            { offset: '100%', color: '#FFF78D', opacity: '0.0' }
        ], 'vertical');

        defs.appendChild(lineGrad);
        defs.appendChild(fillGrad);
        chartSvg.appendChild(defs);

        // Grid
        for (let i = 0; i <= 3; i++) {
            const yVal = padTop + (chartH / 3) * i;
            const grid = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            grid.setAttribute('x1', padLeft);
            grid.setAttribute('y1', yVal);
            grid.setAttribute('x2', svgW - padRight);
            grid.setAttribute('y2', yVal);
            grid.setAttribute('class', 'chart-grid');
            chartSvg.appendChild(grid);

            const gridText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            gridText.setAttribute('x', padLeft - 8);
            gridText.setAttribute('y', yVal + 4);
            gridText.setAttribute('fill', '#FFBF00');
            gridText.setAttribute('font-size', '9px');
            gridText.setAttribute('text-anchor', 'end');
            gridText.setAttribute('font-weight', '600');
            gridText.setAttribute('font-family', "'JetBrains Mono', monospace");
            gridText.textContent = Math.round(maxScaleY - (maxScaleY / 3) * i) + ' kW';
            chartSvg.appendChild(gridText);
        }

        // Data coordinates
        const numPoints = hourlyData.length;
        const coords = hourlyData.map((d, idx) => ({
            x: padLeft + (numPoints > 1 ? (idx / (numPoints - 1)) * chartW : 0),
            y: padTop + chartH - (d.power / maxScaleY) * chartH,
            hour: d.hour,
            power: d.power
        }));

        if (coords.length > 0) {
            // Smooth cubic bezier path
            let pathD, areaD;

            if (coords.length === 1) {
                pathD = `M ${coords[0].x} ${coords[0].y}`;
                areaD = `M ${coords[0].x} ${padTop + chartH} L ${coords[0].x} ${coords[0].y} L ${coords[0].x} ${padTop + chartH} Z`;
            } else {
                pathD = `M ${coords[0].x} ${coords[0].y}`;
                areaD = `M ${coords[0].x} ${padTop + chartH} L ${coords[0].x} ${coords[0].y}`;

                for (let i = 1; i < coords.length; i++) {
                    const prev = coords[i - 1];
                    const curr = coords[i];
                    const cpx = (prev.x + curr.x) / 2;
                    pathD += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
                    areaD += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
                }
                areaD += ` L ${coords[coords.length - 1].x} ${padTop + chartH} Z`;
            }

            // Area
            const areaPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            areaPath.setAttribute('d', areaD);
            areaPath.setAttribute('class', 'chart-area');
            chartSvg.appendChild(areaPath);

            // Line
            const linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            linePath.setAttribute('d', pathD);
            linePath.setAttribute('class', 'chart-line');
            linePath.style.strokeDasharray = 'none';
            linePath.style.strokeDashoffset = '0';
            linePath.style.animation = 'none';
            chartSvg.appendChild(linePath);

            // Points without animation
            coords.forEach((pt, idx) => {
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', pt.x);
                circle.setAttribute('cy', pt.y);
                circle.setAttribute('r', '4');
                circle.setAttribute('class', 'chart-point');
                circle.style.opacity = '1';
                circle.style.animation = 'none';

                const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                title.textContent = `${pt.hour}:00 — ${pt.power.toFixed(1)} kW`;
                circle.appendChild(title);
                chartSvg.appendChild(circle);
            });
        }

        // X Labels
        const startLabel = document.createElement('span');
        startLabel.textContent = `${hourStart}:00`;
        chartXLabels.appendChild(startLabel);

        if (hourEnd - hourStart > 2) {
            const midLabel = document.createElement('span');
            midLabel.textContent = `${Math.floor((hourStart + hourEnd) / 2)}:00`;
            chartXLabels.appendChild(midLabel);
        }

        const endLabel = document.createElement('span');
        endLabel.textContent = `${hourEnd}:00`;
        chartXLabels.appendChild(endLabel);
    }

    // SVG Gradient helper
    function createSVGGradient(id, stops, direction) {
        const grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        grad.setAttribute('id', id);
        if (direction === 'horizontal') {
            grad.setAttribute('x1', '0%'); grad.setAttribute('y1', '0%');
            grad.setAttribute('x2', '100%'); grad.setAttribute('y2', '0%');
        } else {
            grad.setAttribute('x1', '0%'); grad.setAttribute('y1', '0%');
            grad.setAttribute('x2', '0%'); grad.setAttribute('y2', '100%');
        }
        stops.forEach(s => {
            const stop = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop.setAttribute('offset', s.offset);
            stop.setAttribute('stop-color', s.color);
            if (s.opacity) stop.setAttribute('stop-opacity', s.opacity);
            grad.appendChild(stop);
        });
        return grad;
    }

    // =========================================================
    //  HELPERS
    // =========================================================
    function updateStatusBadge(badgeEl, power) {
        if (power < 150) {
            badgeEl.className = 'status-badge status-low';
            badgeEl.textContent = 'Low';
        } else if (power < 750) {
            badgeEl.className = 'status-badge status-medium';
            badgeEl.textContent = 'Medium';
        } else {
            badgeEl.className = 'status-badge status-high';
            badgeEl.textContent = 'High';
        }
    }

    function animateValue(element, target, decimals, type) {
        const duration = 1000;
        const startTime = performance.now();

        function step(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;

            if (type === 'energy') {
                element.textContent = current.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
            } else if (type === 'homes') {
                element.textContent = Math.floor(current).toLocaleString();
            } else if (type === 'percent') {
                element.textContent = current.toFixed(decimals) + '%';
            } else {
                element.textContent = current.toFixed(decimals);
            }

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
        requestAnimationFrame(step);
    }

    function roundTo(value, decimals) {
        return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
    }
});
