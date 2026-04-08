// Application state
const state = {
    currentView: 'profiles',
    currentProfile: null,
    currentYear: null,
    currentMonth: null
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadProfiles();
});

// Load profiles view
async function loadProfiles() {
    state.currentView = 'profiles';
    updateBreadcrumb('Профили');
    
    const profiles = await API.getProfiles();
    const content = document.getElementById('content');
    
    content.innerHTML = `
        <button onclick="showProfileForm()">Добавить профиль</button>
        <div class="profile-list">
            ${profiles.map(profile => `
                <div class="profile-card" onclick="loadYears(${profile.id})">
                    <h3>${profile.name}</h3>
                    <p>${profile.car_brand} - ${profile.license_plate}</p>
                    <button onclick="event.stopPropagation(); editProfile(${profile.id})" class="secondary">Редактировать</button>
                    <button onclick="event.stopPropagation(); deleteProfile(${profile.id})" class="danger">Удалить</button>
                </div>
            `).join('')}
        </div>
    `;
}

// Load years view
async function loadYears(profileId) {
    state.currentProfile = profileId;
    state.currentView = 'years';
    
    const profile = await API.getProfile(profileId);
    const years = await API.getYears(profileId);
    
    updateBreadcrumb(`Профили > ${profile.name}`);
    
    const content = document.getElementById('content');
    content.innerHTML = `
        <button onclick="loadProfiles()">Назад</button>
        <button onclick="showYearForm()">Добавить год</button>
        <div class="year-grid">
            ${years.map(year => `
                <div class="year-card">
                    <div onclick="loadMonths(${profileId}, ${year.year})" style="cursor: pointer;">
                        <h3>${year.year}</h3>
                        <p>${year.is_leap_year ? 'Високосный' : 'Обычный'}</p>
                        <p style="font-size: 0.85em; color: #666; margin-top: 10px;">
                            <strong>На конец ${year.year - 1} года:</strong><br>
                            Спидометр: ${year.initial_odometer?.toFixed(1) || '0.0'}<br>
                            Бензин: ${year.initial_fuel?.toFixed(2) || '0.00'} л
                        </p>
                    </div>
                    <button onclick="event.stopPropagation(); editYearInitials(${profileId}, ${year.year})" class="secondary" style="margin-top: 10px; font-size: 0.85em; width: 100%;">
                        ${year.initial_odometer > 0 || year.initial_fuel > 0 ? 'Изменить' : 'Установить'} начальные значения
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

// Edit year initial values
async function editYearInitials(profileId, year) {
    const yearData = await API.getYear(profileId, year);
    
    const content = document.getElementById('content');
    content.innerHTML = `
        <div style="max-width: 600px; margin: 0 auto;">
            <h2 style="margin-bottom: 10px;">Начальные значения для ${year} года</h2>
            <p style="color: #666; margin-bottom: 30px; font-size: 0.95em;">
                Укажите показания спидометра и остаток бензина на конец ${year - 1} года.<br>
                Эти значения будут использованы для расчетов с 1 января ${year} года.
            </p>
            <form id="yearInitialsForm" style="background: #f8f9fa; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <label style="display: flex; flex-direction: column;">
                        <span style="margin-bottom: 8px; font-weight: 500; font-size: 1.05em;">
                            📊 Спидометр на конец ${year - 1} года (км)
                        </span>
                        <input type="number" step="0.1" name="initial_odometer" value="${yearData.initial_odometer || 0}" required 
                               style="padding: 12px; border: 2px solid #007bff; border-radius: 4px; font-size: 1.1em;">
                        <span style="margin-top: 5px; font-size: 0.85em; color: #666;">Например: 88264.0</span>
                    </label>
                    
                    <label style="display: flex; flex-direction: column;">
                        <span style="margin-bottom: 8px; font-weight: 500; font-size: 1.05em;">
                            ⛽ Остаток бензина на конец ${year - 1} года (л)
                        </span>
                        <input type="number" step="0.01" name="initial_fuel" value="${yearData.initial_fuel || 0}" required 
                               style="padding: 12px; border: 2px solid #28a745; border-radius: 4px; font-size: 1.1em;">
                        <span style="margin-top: 5px; font-size: 0.85em; color: #666;">Например: 17.76</span>
                    </label>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 30px;">
                    <button type="button" onclick="loadYears(${profileId})" style="padding: 10px 30px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Отмена</button>
                    <button type="submit" style="padding: 10px 30px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">💾 Сохранить</button>
                </div>
            </form>
        </div>
    `;
    
    document.getElementById('yearInitialsForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            initial_odometer: parseFloat(formData.get('initial_odometer')),
            initial_fuel: parseFloat(formData.get('initial_fuel'))
        };
        
        await API.updateYear(profileId, year, data);
        loadYears(profileId);
    });
}

// Load months view
async function loadMonths(profileId, year) {
    state.currentProfile = profileId;
    state.currentYear = year;
    state.currentView = 'months';
    
    const profile = await API.getProfile(profileId);
    const yearData = await API.getYear(profileId, year);
    
    updateBreadcrumb(`Профили > ${profile.name} > ${year}`);
    
    const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    
    const content = document.getElementById('content');
    content.innerHTML = `
        <button onclick="loadYears(${profileId})">Назад</button>
        <div class="month-grid">
            ${yearData.months.map(month => `
                <div class="month-card" onclick="loadMonth(${profileId}, ${year}, ${month.month})">
                    <h3>${monthNames[month.month - 1]}</h3>
                    <p>${month.days_in_month} дней</p>
                    <p>${month.has_data ? '✓ Есть данные' : '○ Нет данных'}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// Load month view with daily records and report
async function loadMonth(profileId, year, month) {
    state.currentProfile = profileId;
    state.currentYear = year;
    state.currentMonth = month;
    state.currentView = 'month';

    const [profile, yearData, monthData, reportRows] = await Promise.all([
        API.getProfile(profileId),
        API.getYear(profileId, year),
        API.getMonth(profileId, year, month),
        API.getReport(profileId, year, month)
    ]);

    const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

    updateBreadcrumb(`Профили > ${profile.name} > ${year} > ${monthNames[month - 1]}`);

    const fuelRate = monthData.computed_fuel_rate;
    const initOdo  = monthData.computed_initial_odometer;
    const initFuel = monthData.computed_initial_fuel;
    const records  = monthData.daily_records;

    // fmtN(v) — возвращает объект {text, raw} для подстановки в ячейку
    const _fv = (v, dec) => {
        if (v == null || v === 0) return { text: '', raw: '' };
        return { text: Number(v).toFixed(dec), raw: String(v) };
    };
    const _td = (cls, fv) => `<td class="${cls}" data-value="${fv.raw}">${fv.text}</td>`;
    const fmt0 = v => (v != null && v !== 0) ? Number(v).toFixed(0) : '';
    const fmt3 = v => (v != null && v !== 0) ? Number(v).toFixed(3) : '';
    const fmt2 = v => (v != null && v !== 0) ? Number(v).toFixed(2) : '';

    // Все поля, которые реально сохраняются в БД
    const INPUT_FIELDS = new Set(['odometer_end_day', 'distance_km', 'fuel_received']);

    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="no-print page-actions">
            <button class="btn-back" onclick="loadMonths(${profileId}, ${year})">← Назад</button>
            <button onclick="printDailyTable()">Печать записей</button>
            <button onclick="printReportTable()">Печать отчёта</button>
            <button onclick="printSignature()">Печать итогов</button>
        </div>

        <div class="month-header">
            <h2>${monthNames[month - 1]} ${year}</h2>
            <div class="month-meta">
                <div class="meta-item">
                    <span class="meta-label">Спидометр начало</span>
                    <span class="meta-value">${initOdo ? Number(initOdo).toFixed(0) : '—'} км</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Остаток бензина начало</span>
                    <span class="meta-value">${initFuel ? Number(initFuel).toFixed(3) : '—'} л</span>
                </div>
                <div class="meta-item meta-rate">
                    <span class="meta-label">Норма расхода</span>
                    <div class="rate-input-wrap">
                        <input type="number" step="0.1" id="fuelRateInput"
                            value="${monthData.fuel_rate || fuelRate || ''}"
                            placeholder="—"
                            onchange="updateFuelRate(${profileId}, ${year}, ${month}, this.value)">
                        <span>л/100км</span>
                        ${!monthData.fuel_rate && fuelRate ? '<small>(из профиля)</small>' : ''}
                    </div>
                </div>
            </div>
        </div>

        <div class="table-hint no-print">
            <span class="hint-yellow">Жёлтые ячейки</span> — вводите данные &nbsp;|&nbsp;
            <span class="hint-grey">Серые ячейки</span> — рассчитываются автоматически
        </div>

        <div class="table-section">
            <h3>Таблица ежедневных записей</h3>
            <div class="table-wrap">
                <table id="dailyTable">
                    <thead>
                        <tr>
                            <th>Дата</th>
                            <th>День<br>недели</th>
                            <th>Спидометр<br>конец дня</th>
                            <th>Пробег<br>путевка</th>
                            <th>Бензин<br>путевка</th>
                            <th>Спидометр<br>начало</th>
                            <th>Спидометр<br>конец</th>
                            <th>Бензин<br>остаток</th>
                            <th>Бензин<br>получено</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${records.map((r, i) => {
                            const isWeekend = [0,6].includes(new Date(year, month-1, r.day).getDay());
                            return `
                            <tr data-day="${r.day}" class="${isWeekend ? 'weekend-row' : i%2===0 ? 'even-row' : ''}">
                                <td class="date-cell">${String(r.day).padStart(2,'0')}.${String(month).padStart(2,'0')}.${year}</td>
                                <td class="dow-cell ${isWeekend ? 'weekend' : ''}">${getDayOfWeek(year, month, r.day)}</td>
                                <td class="editable input-cell" data-field="odometer_end_day" data-table="daily" data-value="${r.odometer_end_day ?? ''}">${fmt0(r.odometer_end_day)}</td>
                                <td class="editable input-cell" data-field="distance_km" data-table="daily" data-value="${r.distance_km ?? ''}">${fmt0(r.distance_km)}</td>
                                <td class="editable calc-cell" data-field="fuel_waybill" data-table="daily" data-value="${r.fuel_waybill ?? ''}">${fmt3(r.fuel_waybill)}</td>
                                <td class="editable calc-cell" data-field="odometer_start" data-table="daily" data-value="${r.odometer_start ?? ''}">${fmt0(r.odometer_start)}</td>
                                <td class="editable calc-cell" data-field="odometer_end" data-table="daily" data-value="${r.odometer_end ?? ''}">${fmt0(r.odometer_end)}</td>
                                <td class="editable calc-cell" data-field="fuel_remaining" data-table="daily" data-value="${r.fuel_remaining ?? ''}">${fmt3(r.fuel_remaining)}</td>
                                <td class="editable input-cell" data-field="fuel_received" data-table="daily" data-value="${r.fuel_received ?? ''}">${fmt0(r.fuel_received)}</td>
                            </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="global-format-bar no-print">
            <span>Все ячейки:</span>
            <button onclick="formatAllCells('bold')"><b>Ж</b></button>
            <button onclick="formatAllCells('italic')"><i>К</i></button>
            <select onchange="if(this.value){formatAllCells('fontSize',this.value);this.value=''}">
                <option value="">Размер шрифта</option>
                <option value="10">10px</option>
                <option value="11">11px</option>
                <option value="12">12px</option>
                <option value="13">13px</option>
                <option value="14">14px</option>
            </select>
            <select onchange="if(this.value){formatAllCells('decimals',this.value);this.value=''}">
                <option value="">Знаки после запятой</option>
                <option value="0">0</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
            </select>
        </div>

        <div class="report-info no-print">
            <p><strong>Автомашина:</strong> ${profile.car_brand} &nbsp;|&nbsp;
               <strong>Гос. номер:</strong> ${profile.license_plate} &nbsp;|&nbsp;
               <strong>Водитель:</strong> ${profile.name}</p>
        </div>

        <div class="report-header" style="display:none;">
            <h2>за ${monthNames[month-1].toLowerCase()} месяц ${year} года</h2>
            <p>по автомашине ${profile.car_brand}</p>
            <p>Гос. номер ${profile.license_plate}</p>
            <p>Водитель ${profile.name}</p>
        </div>

        <div class="table-section">
            <h3>Отчёт за ${monthNames[month-1]} ${year}</h3>
            <div class="table-wrap">
                <table id="reportTable">
                    <thead>
                        <tr>
                            <th rowspan="2">Дата</th>
                            <th colspan="2">Начало дня</th>
                            <th colspan="2">Конец дня</th>
                            <th rowspan="2">Получено<br>бензина</th>
                            <th colspan="2">За день</th>
                        </tr>
                        <tr>
                            <th>км</th><th>л</th>
                            <th>км</th><th>л</th>
                            <th>км</th><th>л</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(() => {
                            let totRec=0, totKm=0, totFuel=0;
                            const rows = reportRows.map((row, i) => {
                                if (row.fuel_received) totRec += row.fuel_received;
                                if (row.km_za_den)    totKm  += row.km_za_den;
                                if (row.fuel_waybill) totFuel += row.fuel_waybill;
                                const isWeekend = [0,6].includes(new Date(year, month-1, row.day).getDay());
                                return `
                                <tr data-day="${row.day}" class="${isWeekend ? 'weekend-row' : i%2===0 ? 'even-row' : ''}">
                                    <td class="date-cell">${String(row.day).padStart(2,'0')}.${String(month).padStart(2,'0')}.${year}</td>
                                    <td class="editable calc-cell" data-field="odometer_start" data-table="report" data-value="${row.odometer_start ?? ''}">${fmt0(row.odometer_start)}</td>
                                    <td class="editable calc-cell" data-field="fuel_start"     data-table="report" data-value="${row.fuel_start ?? ''}">${fmt2(row.fuel_start)}</td>
                                    <td class="editable calc-cell" data-field="odometer_end"   data-table="report" data-value="${row.odometer_end ?? ''}">${fmt0(row.odometer_end)}</td>
                                    <td class="editable calc-cell" data-field="fuel_end"       data-table="report" data-value="${row.fuel_end ?? ''}">${fmt2(row.fuel_end)}</td>
                                    <td class="editable input-cell" data-field="fuel_received" data-table="report" data-value="${row.fuel_received ?? ''}">${fmt0(row.fuel_received)}</td>
                                    <td class="editable calc-cell" data-field="km_za_den"      data-table="report" data-value="${row.km_za_den ?? ''}">${fmt0(row.km_za_den)}</td>
                                    <td class="editable calc-cell" data-field="fuel_waybill"   data-table="report" data-value="${row.fuel_waybill ?? ''}">${fmt3(row.fuel_waybill)}</td>
                                </tr>`;
                            }).join('');

                            // Сохраняем данные для печати
                            window._reportTotals = { totRec, totKm, totFuel };
                            window._printMeta = { profile, records, reportRows, year, month };
                            // Заполняем скрытые чистые таблицы для печати
                            _buildPrintTables(profile, records, reportRows, year, month);

                            return rows + `
                            <tr class="total-row">
                                <td>ИТОГО</td>
                                <td>—</td><td>—</td><td>—</td><td>—</td>
                                <td>${totRec > 0 ? totRec.toFixed(0) : ''}</td>
                                <td>${totKm  > 0 ? totKm.toFixed(0)  : ''}</td>
                                <td>${totFuel > 0 ? totFuel.toFixed(3) : ''}</td>
                            </tr>`;
                        })()}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Блок подписи — виден на экране и при печати отчёта -->
        <div class="report-signature" id="reportSignature">
            <div class="sig-line">
                Пробег за&nbsp;<strong>${monthNames[month-1].toLowerCase()} месяц</strong>
                &nbsp;<span class="sig-val" id="sigKm">${window._reportTotals ? window._reportTotals.totKm.toFixed(0) : '—'}</span>&nbsp;км
            </div>
            <div class="sig-line">
                Расход бензина по норме
                &nbsp;<span class="sig-val" id="sigFuel">${window._reportTotals ? window._reportTotals.totFuel.toFixed(1) : '—'}</span>&nbsp;л
            </div>
            <div class="sig-line">
                Фактически израсходовано&nbsp;<span class="sig-blank"></span>&nbsp;л
            </div>
            <div class="sig-line">
                Перерасход&nbsp;/недорасход/&nbsp;<span class="sig-blank"></span>&nbsp;л
            </div>
            <div class="sig-line sig-driver">
                Водитель&nbsp;<span class="sig-blank sig-blank-sm"></span>&nbsp;(${profile.name})
            </div>
        </div>
    `;

    // Передаём набор input-полей в обработчик ячеек
    makeCellsEditable(profileId, year, month, INPUT_FIELDS);
}


// Get day of week in Russian
function getDayOfWeek(year, month, day) {
    const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    const date = new Date(year, month - 1, day);
    return days[date.getDay()];
}

// Excel-style cell editing
let selectedCell = null;
let fillHandleActive = false;
let fillStartCell = null;
let fillTargetCells = [];
let cellEditController = null;  // AbortController для снятия listeners при перезагрузке

function makeCellsEditable(profileId, year, month, inputFields) {
    if (cellEditController) cellEditController.abort();
    cellEditController = new AbortController();
    const { signal } = cellEditController;

    document.querySelectorAll('.editable').forEach(cell => {
        cell.addEventListener('click', (e) => {
            if (e.target.classList.contains('fill-handle')) return;

            if (selectedCell && selectedCell !== cell) {
                if (selectedCell.querySelector('input.cell-input')) {
                    finishEditing(selectedCell, profileId, year, month, inputFields);
                    return;
                }
                selectedCell.classList.remove('selected');
                removeFillHandle();
            }

            selectedCell = cell;
            cell.classList.add('selected');
            startEditing(cell);
            addFillHandle(cell, profileId, year, month);
        }, { signal });

        cell.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                // Запоминаем поле и день до перезагрузки DOM
                const field = cell.dataset.field;
                const nextRow = e.key === 'Enter' ? cell.closest('tr').nextElementSibling : null;
                const allEditables = e.key === 'Tab' ? Array.from(document.querySelectorAll('.editable')) : null;
                const nextTabIndex = allEditables ? allEditables.indexOf(cell) + 1 : -1;

                finishEditing(cell, profileId, year, month, inputFields).then(() => {
                    // После перезагрузки DOM находим следующую ячейку
                    if (e.key === 'Enter' && nextRow) {
                        const targetDay = parseInt(nextRow.dataset.day);
                        const nextCell = document.querySelector(`tr[data-day="${targetDay}"] .editable[data-field="${field}"]`);
                        if (nextCell) nextCell.click();
                    } else if (e.key === 'Tab' && nextTabIndex >= 0) {
                        const allNew = Array.from(document.querySelectorAll('.editable'));
                        if (allNew[nextTabIndex]) allNew[nextTabIndex].click();
                    }
                });
            } else if (e.key === 'Escape') {
                e.preventDefault();
                const inp = cell.querySelector('input.cell-input');
                if (inp) inp.remove();
                cell.textContent = cell.dataset.originalValue || '';
                selectedCell = null;
            }
        }, { signal });
    });

    // Click outside — только один listener на document, снимается через AbortController
    document.addEventListener('click', (e) => {
        if (e.target.closest('.cell-input') || e.target.classList.contains('fill-handle')) return;
        if (!e.target.closest('.editable')) {
            if (selectedCell && selectedCell.querySelector('input.cell-input')) {
                finishEditing(selectedCell, profileId, year, month, inputFields);
                return;
            }
            if (selectedCell) {
                selectedCell.classList.remove('selected');
                removeFillHandle();
                selectedCell = null;
            }
        }
    }, { signal });
}

function addFillHandle(cell, profileId, year, month) {
    removeFillHandle(); // Remove any existing handle
    
    const handle = document.createElement('div');
    handle.className = 'fill-handle';
    handle.style.cssText = `
        position: absolute;
        right: -4px;
        bottom: -4px;
        width: 8px;
        height: 8px;
        background: #4a90e2;
        border: 1px solid white;
        cursor: crosshair;
        z-index: 10;
    `;
    
    cell.style.position = 'relative';
    cell.appendChild(handle);
    
    // Handle drag
    handle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fillHandleActive = true;
        fillStartCell = cell;
        fillTargetCells = [];
        
        const field = cell.dataset.field;
        const startRow = cell.closest('tr');
        const startDay = parseInt(startRow.dataset.day);
        
        document.addEventListener('mousemove', onFillDrag);
        document.addEventListener('mouseup', onFillEnd);
        
        function onFillDrag(e) {
            if (!fillHandleActive) return;
            
            // Find cell under mouse
            const target = document.elementFromPoint(e.clientX, e.clientY);
            if (!target) return;
            
            const targetCell = target.closest('.editable');
            if (!targetCell || targetCell.dataset.field !== field) return;
            
            const targetRow = targetCell.closest('tr');
            const targetDay = parseInt(targetRow.dataset.day);
            
            // Clear previous highlights
            fillTargetCells.forEach(c => c.classList.remove('fill-target'));
            fillTargetCells = [];
            
            // Highlight cells in range
            const minDay = Math.min(startDay, targetDay);
            const maxDay = Math.max(startDay, targetDay);
            
            document.querySelectorAll(`tr[data-day]`).forEach(row => {
                const day = parseInt(row.dataset.day);
                if (day >= minDay && day <= maxDay && day !== startDay) {
                    const cellInRow = row.querySelector(`.editable[data-field="${field}"]`);
                    if (cellInRow) {
                        cellInRow.classList.add('fill-target');
                        fillTargetCells.push(cellInRow);
                    }
                }
            });
        }
        
        async function onFillEnd(e) {
            document.removeEventListener('mousemove', onFillDrag);
            document.removeEventListener('mouseup', onFillEnd);
            
            if (fillTargetCells.length > 0) {
                const sourceValue = parseFloat(fillStartCell.textContent.trim()) || 0;
                const field = fillStartCell.dataset.field;
                
                // Update all target cells
                for (const targetCell of fillTargetCells) {
                    const row = targetCell.closest('tr');
                    const day = parseInt(row.dataset.day);
                    
                    try {
                        await API.updateDailyRecord(profileId, year, month, day, {
                            [field]: sourceValue
                        });
                    } catch (error) {
                        console.error('Error updating cell:', error);
                    }
                }
                
                // Reload month to show all recalculated values
                await loadMonth(profileId, year, month);
            }
            
            // Clear highlights
            fillTargetCells.forEach(c => c.classList.remove('fill-target'));
            fillTargetCells = [];
            fillHandleActive = false;
            fillStartCell = null;
        }
    });
}

function removeFillHandle() {
    const existingHandle = document.querySelector('.fill-handle');
    if (existingHandle) {
        existingHandle.remove();
    }
}

function startEditing(cell) {
    if (cell.querySelector('input.cell-input')) return; // уже редактируется

    const currentValue = cell.textContent.trim();
    cell.dataset.originalValue = currentValue;
    cell.textContent = '';

    const input = document.createElement('input');
    input.type = 'number';
    input.step = 'any';
    input.value = currentValue;
    input.className = 'cell-input';
    input.style.cssText = [
        'width:100%', 'height:100%', 'border:none', 'background:transparent',
        'outline:none', 'font-size:inherit', 'font-family:inherit',
        'text-align:right', 'padding:0', 'margin:0', 'color:inherit',
        'box-sizing:border-box', 'min-width:0'
    ].join(';');

    cell.appendChild(input);
    input.focus();
    input.select();

    // Стоп-пропагация чтобы keydown на cell тоже сработал
    input.addEventListener('keydown', (e) => {
        if (['Enter', 'Tab', 'Escape'].includes(e.key)) {
            e.stopPropagation();
            cell.dispatchEvent(new KeyboardEvent('keydown', { key: e.key, bubbles: false }));
            e.preventDefault();
        }
    });
}

async function finishEditing(cell, profileId, year, month, inputFields) {
    if (!cell) return;
    const input = cell.querySelector('input.cell-input');
    if (!input) return; // не в режиме редактирования

    selectedCell = null;

    const raw = input.value.trim();
    const newValue = raw === '' ? null : (parseFloat(raw) || 0);
    const field = cell.dataset.field;
    const row = cell.closest('tr');
    if (!row) return;
    const day = parseInt(row.dataset.day);

    try {
        // Сохраняем только вводимые поля (жёлтые), расчётные — просто перезагружаем
        const saveFields = inputFields || new Set(['odometer_end_day', 'distance_km', 'fuel_received']);
        if (saveFields.has(field)) {
            // Для report-таблицы: fuel_received тоже относится к записи дня
            await API.updateDailyRecord(profileId, year, month, day, { [field]: newValue });
        }
        await loadMonth(profileId, year, month);
    } catch (error) {
        alert('Ошибка при сохранении: ' + error.message);
    }
}

// Update fuel rate for a month
async function updateFuelRate(profileId, year, month, value) {
    const rate = parseFloat(value) || null;
    await API.updateMonth(profileId, year, month, { fuel_rate: rate });
    await loadMonth(profileId, year, month);
}

// Show profile form
function showProfileForm(profileId = null) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div style="max-width: 820px; margin: 0 auto;">
            <div class="page-actions">
                <button class="btn-back" onclick="loadProfiles()">← Назад</button>
            </div>
            <div style="display: flex; gap: 32px; align-items: flex-start;">
                <div class="profile-form-image">
                    <img src="/FOT.png" alt="Фото" onerror="this.style.display='none'">
                    <p style="font-size:11px; color:#90a4ae; margin-top:6px;">Учёт расхода топлива</p>
                </div>
                <div style="flex: 1;">
                    <h2 style="margin-bottom: 20px; color: #1565c0;">${profileId ? 'Редактировать профиль' : 'Новый профиль водителя'}</h2>
                    <form id="profileForm" style="max-width: 100%;">
                        <fieldset>
                            <legend>Основная информация</legend>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 10px;">
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>ФИО водителя <span style="color:red">*</span></span>
                                    <input type="text" name="name" required placeholder="Абрамов А А">
                                </label>
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>Марка автомобиля <span style="color:red">*</span></span>
                                    <input type="text" name="car_brand" required placeholder="Hyundai Solaris">
                                </label>
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>Гос. номер <span style="color:red">*</span></span>
                                    <input type="text" name="license_plate" required placeholder="А 000 АА 000">
                                </label>
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>Бухгалтерия</span>
                                    <input type="text" name="accounting" placeholder="Необязательно">
                                </label>
                            </div>
                        </fieldset>

                        <fieldset style="margin-top: 16px;">
                            <legend>Нормы расхода топлива</legend>
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-top: 10px;">
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>Лето (март–ноябрь)</span>
                                    <input type="number" step="0.1" name="fuel_rate_summer" placeholder="11.6 л/100км">
                                </label>
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>Зима (дек–фев)</span>
                                    <input type="number" step="0.1" name="fuel_rate_winter" placeholder="12.7 л/100км">
                                </label>
                                <label style="display:flex; flex-direction:column; gap:5px;">
                                    <span>Тип топлива</span>
                                    <select name="fuel_type">
                                        <option value="">—</option>
                                        <option value="Бензин">Бензин</option>
                                        <option value="Дизель">Дизель</option>
                                    </select>
                                </label>
                            </div>
                        </fieldset>

                        <div style="display:flex; gap:10px; justify-content:flex-end; margin-top:20px;">
                            <button type="button" class="secondary" onclick="loadProfiles()">Отмена</button>
                            <button type="submit" style="background:#2e7d32;">Сохранить</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;

    document.getElementById('profileForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        if (data.fuel_rate_summer) data.fuel_rate_summer = parseFloat(data.fuel_rate_summer);
        if (data.fuel_rate_winter) data.fuel_rate_winter = parseFloat(data.fuel_rate_winter);
        if (profileId) {
            await API.updateProfile(profileId, data);
        } else {
            await API.createProfile(data);
        }
        loadProfiles();
    });
}

// Show year form
function showYearForm() {
    const content = document.getElementById('content');
    const currentYear = new Date().getFullYear();
    const years = Array.from({length: 21}, (_, i) => currentYear - 10 + i);
    
    content.innerHTML = `
        <h2>Добавить год</h2>
        <form id="yearForm">
            <label>Год: 
                <select name="year" required>
                    ${years.map(y => `<option value="${y}">${y}</option>`).join('')}
                </select>
            </label>
            <div class="form-actions">
                <button type="submit">Создать</button>
                <button type="button" onclick="loadYears(${state.currentProfile})" class="secondary">Отмена</button>
            </div>
        </form>
    `;
    
    document.getElementById('yearForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const year = parseInt(formData.get('year'));
        
        await API.createYear(state.currentProfile, year);
        loadYears(state.currentProfile);
    });
}

// Edit profile
async function editProfile(profileId) {
    const profile = await API.getProfile(profileId);
    showProfileForm(profileId);
    
    // Fill form with existing data
    document.querySelector('[name="name"]').value = profile.name;
    document.querySelector('[name="car_brand"]').value = profile.car_brand;
    document.querySelector('[name="license_plate"]').value = profile.license_plate;
    document.querySelector('[name="accounting"]').value = profile.accounting || '';
    document.querySelector('[name="fuel_rate_summer"]').value = profile.fuel_rate_summer || '';
    document.querySelector('[name="fuel_rate_winter"]').value = profile.fuel_rate_winter || '';
    document.querySelector('[name="fuel_type"]').value = profile.fuel_type || '';
}

// Delete profile
async function deleteProfile(profileId) {
    if (confirm('Вы уверены, что хотите удалить этот профиль?')) {
        await API.deleteProfile(profileId);
        loadProfiles();
    }
}

// Update breadcrumb
function updateBreadcrumb(text) {
    document.getElementById('breadcrumb').textContent = text;
}

// Print functions
function _printHtml(innerHtml) {
    const frame = document.getElementById('print-frame');
    const app   = document.getElementById('app');
    frame.innerHTML = innerHtml;
    // Показываем только print-frame, скрываем всё остальное
    frame.style.cssText = 'display:block';
    app.style.cssText   = 'display:none';
    window.print();
    // Восстанавливаем
    app.style.cssText   = '';
    frame.style.cssText = 'display:none';
    frame.innerHTML = '';
}

function _printStyles() {
    return ''; // стили описаны в style.css (#print-frame ...)
}

function _docHeader(profile, year, month, title) {
    const monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                        'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
    const mn = monthNames[month - 1];
    return `
        <div style="text-align:center;font-family:'Segoe UI',Arial,sans-serif;margin-bottom:10px;color:#000;">
            <div style="font-size:20px;font-weight:700;letter-spacing:2px;margin-bottom:4px;">${title || 'ОТЧЕТ'}</div>
            <div style="font-size:11px;font-weight:700;margin-bottom:2px;">за ${mn.toLowerCase()} месяц ${year} года</div>
            <div style="font-size:10px;line-height:1.8;">
                по автомашине <b>${profile.car_brand}</b><br>
                Гос. номер <b>${profile.license_plate}</b><br>
                Водитель <b>${profile.name}</b>
            </div>
        </div>`;
}

const MONTH_NAMES = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];

// Inline стили для печатных таблиц — никаких классов приложения
const _B = '0.3px solid #000';
const _PS = {
    table: `width:100%;border-collapse:separate;border-spacing:0;font-size:8px;border-top:${_B};border-left:${_B};`,
    th: `border-right:${_B};border-bottom:${_B};padding:5px 8px;text-align:center;font-weight:700;background:#fff;color:#000;`,
    td: `border-right:${_B};border-bottom:${_B};padding:4px 8px;text-align:center;background:#fff;color:#000;`,
    tdTotal: `border-right:${_B};border-bottom:${_B};padding:4px 8px;text-align:center;background:#fff;color:#000;font-weight:700;`,
};

function _buildPrintTables(profile, records, reportRows, year, month) {
    const f0 = v => (v != null && v !== 0) ? Number(v).toFixed(0) : '';
    const f2 = v => (v != null && v !== 0) ? Number(v).toFixed(2) : '';
    const f3 = v => (v != null && v !== 0) ? Number(v).toFixed(3) : '';
    const days = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'];

    // --- Таблица 1: ежедневные записи ---
    const dailyRows = records.map(r => {
        const d = `${String(r.day).padStart(2,'0')}.${String(month).padStart(2,'0')}.${year}`;
        const dow = days[new Date(year, month-1, r.day).getDay()];
        return `<tr>
            <td style="${_PS.td}">${d}</td>
            <td style="${_PS.td}">${dow}</td>
            <td style="${_PS.td}">${f0(r.odometer_end_day)}</td>
            <td style="${_PS.td}">${f0(r.distance_km)}</td>
            <td style="${_PS.td}">${f3(r.fuel_waybill)}</td>
            <td style="${_PS.td}">${f0(r.odometer_start)}</td>
            <td style="${_PS.td}">${f0(r.odometer_end)}</td>
            <td style="${_PS.td}">${f3(r.fuel_remaining)}</td>
            <td style="${_PS.td}">${f0(r.fuel_received)}</td>
        </tr>`;
    }).join('');
    document.getElementById('print-daily-data').innerHTML = `
        <table style="${_PS.table}">
            <thead><tr>
                <th style="${_PS.th}">Дата</th>
                <th style="${_PS.th}">День<br>нед.</th>
                <th style="${_PS.th}">Спидометр<br>конец дня</th>
                <th style="${_PS.th}">Пробег<br>путевка</th>
                <th style="${_PS.th}">Бензин<br>путевка</th>
                <th style="${_PS.th}">Спидометр<br>начало</th>
                <th style="${_PS.th}">Спидометр<br>конец</th>
                <th style="${_PS.th}">Бензин<br>остаток</th>
                <th style="${_PS.th}">Бензин<br>получено</th>
            </tr></thead>
            <tbody>${dailyRows}</tbody>
        </table>`;

    // --- Таблица 2: отчёт ---
    let totRec=0, totKm=0, totFuel=0;
    const reportRowsHtml = reportRows.map(row => {
        if (row.fuel_received) totRec += row.fuel_received;
        if (row.km_za_den)     totKm  += row.km_za_den;
        if (row.fuel_waybill)  totFuel += row.fuel_waybill;
        const d = `${String(row.day).padStart(2,'0')}.${String(month).padStart(2,'0')}.${year}`;
        return `<tr>
            <td style="${_PS.td}">${d}</td>
            <td style="${_PS.td}">${f0(row.odometer_start)}</td>
            <td style="${_PS.td}">${f2(row.fuel_start)}</td>
            <td style="${_PS.td}">${f0(row.odometer_end)}</td>
            <td style="${_PS.td}">${f2(row.fuel_end)}</td>
            <td style="${_PS.td}">${f0(row.fuel_received)}</td>
            <td style="${_PS.td}">${f0(row.km_za_den)}</td>
            <td style="${_PS.td}">${f3(row.fuel_waybill)}</td>
        </tr>`;
    }).join('');
    const totalRow = `<tr>
        <td style="${_PS.tdTotal}">ИТОГО</td>
        <td style="${_PS.tdTotal}">—</td><td style="${_PS.tdTotal}">—</td>
        <td style="${_PS.tdTotal}">—</td><td style="${_PS.tdTotal}">—</td>
        <td style="${_PS.tdTotal}">${totRec > 0 ? totRec.toFixed(0) : ''}</td>
        <td style="${_PS.tdTotal}">${totKm  > 0 ? totKm.toFixed(0)  : ''}</td>
        <td style="${_PS.tdTotal}">${totFuel > 0 ? totFuel.toFixed(3) : ''}</td>
    </tr>`;
    document.getElementById('print-report-data').innerHTML = `
        <table style="${_PS.table}">
            <thead>
                <tr>
                    <th style="${_PS.th}" rowspan="2">Дата</th>
                    <th style="${_PS.th}" colspan="2">Начало дня</th>
                    <th style="${_PS.th}" colspan="2">Конец дня</th>
                    <th style="${_PS.th}" rowspan="2">Получено<br>бензина</th>
                    <th style="${_PS.th}" colspan="2">За день</th>
                </tr>
                <tr>
                    <th style="${_PS.th}">км</th><th style="${_PS.th}">л</th>
                    <th style="${_PS.th}">км</th><th style="${_PS.th}">л</th>
                    <th style="${_PS.th}">км</th><th style="${_PS.th}">л</th>
                </tr>
            </thead>
            <tbody>${reportRowsHtml}${totalRow}</tbody>
        </table>`;

    // Обновляем итоги
    window._reportTotals = { totRec, totKm, totFuel };
}

function printDailyTable() {
    const m = window._printMeta;
    if (!m) return;
    const tableHtml = document.getElementById('print-daily-data').innerHTML;
    _printHtml(`${_docHeader(m.profile, m.year, m.month, 'ПУТЕВЫЕ ЗАПИСИ')}${tableHtml}`);
}

function printReportTable() {
    const m = window._printMeta;
    if (!m) return;
    const tableHtml = document.getElementById('print-report-data').innerHTML;
    _printHtml(`${_docHeader(m.profile, m.year, m.month, 'ОТЧЕТ')}${tableHtml}`);
}

function printSignature() {
    const m = window._printMeta;
    if (!m) return;
    const t    = window._reportTotals || {};
    const km   = t.totKm   ? t.totKm.toFixed(0)   : '—';
    const fuel = t.totFuel ? t.totFuel.toFixed(1)  : '—';
    const mn   = MONTH_NAMES[m.month-1];
    const blank = (w) => `<span style="display:inline-block;width:${w}px;border-bottom:1px solid #000;vertical-align:bottom;margin:0 6px;"></span>`;
    _printHtml(`
        <div style="text-align:center;margin-top:80px;font-family:'Segoe UI',Arial,sans-serif;font-size:13px;line-height:2.8;color:#000;">
            <div>Пробег за <b>${mn.toLowerCase()} месяц</b> <b>${km}</b> км</div>
            <div>Расход бензина по норме <b>${fuel}</b> л</div>
            <div>Фактически израсходовано ${blank(120)} л</div>
            <div>Перерасход /недорасход/ ${blank(120)} л</div>
            <div style="margin-top:24px;">Водитель ${blank(80)} (${m.profile.name})</div>
        </div>
    `);
}

// Cell formatting
let currentFormattedCell = null;

function showCellFormatToolbar(cell) {
    const toolbar = document.getElementById('cellFormatToolbar');
    if (!toolbar) return;
    
    currentFormattedCell = cell;
    toolbar.style.display = 'flex';
    
    // Position toolbar near the cell
    const rect = cell.getBoundingClientRect();
    toolbar.style.position = 'fixed';
    toolbar.style.top = (rect.top - 45) + 'px';
    toolbar.style.left = rect.left + 'px';
}

function hideCellFormatToolbar() {
    const toolbar = document.getElementById('cellFormatToolbar');
    if (toolbar) {
        toolbar.style.display = 'none';
        currentFormattedCell = null;
    }
}

function _applyFormat(cell, action, value) {
    switch(action) {
        case 'bold':
            cell.style.fontWeight = cell.style.fontWeight === 'bold' ? '' : 'bold';
            break;
        case 'italic':
            cell.style.fontStyle = cell.style.fontStyle === 'italic' ? '' : 'italic';
            break;
        case 'fontSize':
            cell.style.fontSize = value + 'px';
            break;
        case 'color':
            cell.style.color = value;
            break;
        case 'decimals': {
            const raw = parseFloat(cell.dataset.value);
            if (!isNaN(raw)) {
                cell.textContent = raw.toFixed(parseInt(value));
            }
            break;
        }
    }
}

function formatCell(action, value) {
    if (!currentFormattedCell) return;
    _applyFormat(currentFormattedCell, action, value);
}

function formatAllCells(action, value) {
    document.querySelectorAll('#dailyTable td, #reportTable td').forEach(cell => {
        _applyFormat(cell, action, value);
    });
}

// Context menu for cells
document.addEventListener('DOMContentLoaded', () => {
    // Create context menu
    const contextMenu = document.createElement('div');
    contextMenu.id = 'cellContextMenu';
    contextMenu.className = 'context-menu';
    contextMenu.innerHTML = `
        <div class="context-menu-header">
            <span>Формат ячейки</span>
            <button class="context-menu-close" onclick="closeContextMenu()">✕</button>
        </div>
        <div class="context-menu-item" onclick="showCellFormatToolbar(currentFormattedCell); closeContextMenu();">
            <span>⚙️ Формат ячейки</span>
        </div>
        <div class="context-menu-item" onclick="copyCellValue(); closeContextMenu();">
            <span>📋 Копировать</span>
        </div>
        <div class="context-menu-item" onclick="pasteCellValue(); closeContextMenu();">
            <span>📄 Вставить</span>
        </div>
    `;
    contextMenu.style.display = 'none';
    document.body.appendChild(contextMenu);
    
    // Create format toolbar
    const toolbar = document.createElement('div');
    toolbar.id = 'cellFormatToolbar';
    toolbar.className = 'cell-format-toolbar';
    toolbar.style.display = 'none';
    toolbar.innerHTML = `
        <button onclick="formatCell('bold')" title="Жирный"><b>Ж</b></button>
        <button onclick="formatCell('italic')" title="Курсив"><i>К</i></button>
        <select onchange="formatCell('fontSize', this.value)" title="Размер шрифта">
            <option value="">Размер</option>
            <option value="10">10</option>
            <option value="11">11</option>
            <option value="12">12</option>
            <option value="13">13</option>
            <option value="14">14</option>
            <option value="16">16</option>
        </select>
        <select onchange="formatCell('decimals', this.value)" title="Знаки после запятой">
            <option value="">Знаки</option>
            <option value="0">0</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
        </select>
        <input type="color" onchange="formatCell('color', this.value)" title="Цвет текста">
        <button onclick="hideCellFormatToolbar()" title="Закрыть">✕</button>
    `;
    document.body.appendChild(toolbar);

    // Handle right click on editable cells
    document.addEventListener('contextmenu', (e) => {
        const cell = e.target.closest('.editable');
        if (cell) {
            e.preventDefault();
            currentFormattedCell = cell;
            
            contextMenu.style.display = 'block';
            contextMenu.style.left = e.pageX + 'px';
            contextMenu.style.top = e.pageY + 'px';
        }
    });
    
    // Hide context menu on click outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.context-menu') && !e.target.closest('.context-menu-close')) {
            contextMenu.style.display = 'none';
        }
    });
});

function closeContextMenu() {
    const contextMenu = document.getElementById('cellContextMenu');
    if (contextMenu) {
        contextMenu.style.display = 'none';
    }
}

let copiedValue = null;

function copyCellValue() {
    if (currentFormattedCell) {
        copiedValue = currentFormattedCell.textContent.trim();
        navigator.clipboard.writeText(copiedValue);
    }
}

function pasteCellValue() {
    if (currentFormattedCell && copiedValue) {
        currentFormattedCell.textContent = copiedValue;
        // Trigger save
        const profileId = state.currentProfile;
        const year = state.currentYear;
        const month = state.currentMonth;
        finishEditing(currentFormattedCell, profileId, year, month);
    }
}
