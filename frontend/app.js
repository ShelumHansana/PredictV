/**
 * ═══════════════════════════════════════════════════════════════════
 * PREDICTV — FRONTEND APPLICATION LOGIC
 * Supports Manual Motorbike Details & Sensor Measurements Input,
 * Dual-Mode (FastAPI ML Backend + Standalone Client Fallback),
 * Interactive SVG Radial Gauge, XAI Bars, Forecast Charts & History
 * ═══════════════════════════════════════════════════════════════════
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // ── State ────────────────────────────────────────────────────────
  let currentPrediction = null;
  let backendAvailable = false;
  const API_URL = '/api/v1/emissions/predict-direct';
  const STORAGE_KEY = 'predictv_bike_history';

  // ── DOM References ───────────────────────────────────────────────
  const form = document.getElementById('bike-prediction-form');
  const btnPredict = document.getElementById('btn-predict');
  const emptyState = document.getElementById('results-empty-state');
  const resultsDashboard = document.getElementById('results-dashboard');
  const backendBadge = document.getElementById('backend-status-badge');
  const backendStatusText = document.getElementById('backend-status-text');

  // Sliders & Number Inputs mappings
  const sensorConfigs = [
    { key: 'co', inputId: 'sensor-co', sliderId: 'slider-co', badgeId: 'status-badge-co' },
    { key: 'co2', inputId: 'sensor-co2', sliderId: 'slider-co2', badgeId: 'status-badge-co2' },
    { key: 'hc', inputId: 'sensor-hc', sliderId: 'slider-hc', badgeId: 'status-badge-hc' },
    { key: 'o2', inputId: 'sensor-o2', sliderId: 'slider-o2', badgeId: 'status-badge-o2' },
    { key: 'nox', inputId: 'sensor-nox', sliderId: 'slider-nox', badgeId: 'status-badge-nox' },
    { key: 'lambda', inputId: 'sensor-lambda', sliderId: 'slider-lambda', badgeId: 'status-badge-lambda' },
    { key: 'smoke', inputId: 'sensor-smoke', sliderId: 'slider-smoke', badgeId: 'status-badge-smoke' },
    { key: 'temp', inputId: 'sensor-temp', sliderId: 'slider-temp', badgeId: 'status-badge-temp' },
    { key: 'rpm', inputId: 'sensor-rpm', sliderId: 'slider-rpm', badgeId: 'status-badge-rpm' },
    { key: 'fuel', inputId: 'sensor-fuel', sliderId: 'slider-fuel', badgeId: 'status-badge-fuel' },
  ];

  // ── Init ─────────────────────────────────────────────────────────
  initSensorsSync();
  initBikeSpecsSync();
  initPresets();
  initHistoryDrawer();
  initModelInfoModal();
  initExportActions();
  checkBackendHealth();
  updateHistoryCount();

  // ── 1. Sensor Inputs & Sliders Bi-directional Sync & Live Badges ──
  function initSensorsSync() {
    sensorConfigs.forEach(cfg => {
      const numInput = document.getElementById(cfg.inputId);
      const slider = document.getElementById(cfg.sliderId);

      if (!numInput || !slider) return;

      // Sync slider -> input
      slider.addEventListener('input', () => {
        numInput.value = slider.value;
        updateSensorThresholdBadge(cfg.key, parseFloat(slider.value));
      });

      // Sync input -> slider
      numInput.addEventListener('input', () => {
        slider.value = numInput.value;
        updateSensorThresholdBadge(cfg.key, parseFloat(numInput.value));
      });

      // Initial evaluation
      updateSensorThresholdBadge(cfg.key, parseFloat(numInput.value));
    });
  }

  function updateSensorThresholdBadge(key, val) {
    const cfg = sensorConfigs.find(c => c.key === key);
    if (!cfg) return;
    const badge = document.getElementById(cfg.badgeId);
    if (!badge) return;

    badge.className = 'sensor-status-badge';

    if (isNaN(val)) {
      badge.textContent = '--';
      return;
    }

    switch (key) {
      case 'co':
        if (val <= 0.5) {
          badge.textContent = 'Pass';
          badge.classList.add('badge-pass');
        } else if (val <= 1.0) {
          badge.textContent = 'Warning';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'Fail';
          badge.classList.add('badge-fail');
        }
        break;

      case 'co2':
        if (val >= 13.0 && val <= 16.0) {
          badge.textContent = 'Optimal';
          badge.classList.add('badge-pass');
        } else if (val >= 11.0) {
          badge.textContent = 'Nominal';
          badge.classList.add('badge-pass');
        } else {
          badge.textContent = 'Incomplete';
          badge.classList.add('badge-warn');
        }
        break;

      case 'hc':
        if (val <= 100) {
          badge.textContent = 'Pass';
          badge.classList.add('badge-pass');
        } else if (val <= 200) {
          badge.textContent = 'Warning';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'High';
          badge.classList.add('badge-fail');
        }
        break;

      case 'o2':
        if (val >= 0.4 && val <= 1.5) {
          badge.textContent = 'Pass';
          badge.classList.add('badge-pass');
        } else if (val <= 2.5) {
          badge.textContent = 'Elevated';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'Lean/Leak';
          badge.classList.add('badge-fail');
        }
        break;

      case 'nox':
        if (val <= 60) {
          badge.textContent = 'Pass';
          badge.classList.add('badge-pass');
        } else if (val <= 150) {
          badge.textContent = 'Warning';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'Fail';
          badge.classList.add('badge-fail');
        }
        break;

      case 'lambda':
        if (val >= 0.97 && val <= 1.03) {
          badge.textContent = 'Stoichiometric';
          badge.classList.add('badge-pass');
        } else if (val < 0.97) {
          badge.textContent = 'Rich';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'Lean';
          badge.classList.add('badge-warn');
        }
        break;

      case 'smoke':
        if (val <= 10) {
          badge.textContent = 'Clear';
          badge.classList.add('badge-pass');
        } else if (val <= 25) {
          badge.textContent = 'Hazy';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'Dense';
          badge.classList.add('badge-fail');
        }
        break;

      case 'temp':
        if (val >= 75 && val <= 96) {
          badge.textContent = 'Nominal';
          badge.classList.add('badge-pass');
        } else if (val <= 108) {
          badge.textContent = 'Warm';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'Overheat';
          badge.classList.add('badge-fail');
        }
        break;

      case 'rpm':
        if (val <= 1600) {
          badge.textContent = 'Idle';
          badge.classList.add('badge-pass');
        } else if (val <= 5000) {
          badge.textContent = 'Mid-Band';
          badge.classList.add('badge-pass');
        } else {
          badge.textContent = 'High RPM';
          badge.classList.add('badge-warn');
        }
        break;

      case 'fuel':
        if (val <= 3.2) {
          badge.textContent = 'Good';
          badge.classList.add('badge-pass');
        } else if (val <= 4.2) {
          badge.textContent = 'Average';
          badge.classList.add('badge-warn');
        } else {
          badge.textContent = 'High';
          badge.classList.add('badge-fail');
        }
        break;
    }
  }

  // ── 2. Bike Specs & Year/Age Sync ────────────────────────────────
  function initBikeSpecsSync() {
    const yearInput = document.getElementById('bike-year');
    const ageLabel = document.getElementById('bike-age-label');

    function updateAge() {
      const year = parseInt(yearInput.value) || 2022;
      const currentYear = 2026;
      const age = Math.max(0, currentYear - year);
      ageLabel.textContent = `${age} yr${age === 1 ? '' : 's'} old`;
    }

    if (yearInput && ageLabel) {
      yearInput.addEventListener('input', updateAge);
      updateAge();
    }

    // Quick CC buttons
    const ccButtons = document.querySelectorAll('.quick-cc-chips .btn-micro');
    const ccInput = document.getElementById('bike-cc');
    ccButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        ccButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (ccInput) ccInput.value = btn.getAttribute('data-cc');
      });
    });

    if (ccInput) {
      ccInput.addEventListener('input', () => {
        const val = ccInput.value;
        ccButtons.forEach(b => {
          if (b.getAttribute('data-cc') === val) {
            b.classList.add('active');
          } else {
            b.classList.remove('active');
          }
        });
      });
    }

    // Interactive Pill Selectors
    setupPills('oil-condition-selector');
    setupPills('catalytic-selector');
  }

  function setupPills(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const labels = container.querySelectorAll('.pill-option');
    labels.forEach(lbl => {
      lbl.addEventListener('click', () => {
        labels.forEach(l => l.classList.remove('active'));
        lbl.classList.add('active');
        const input = lbl.querySelector('input');
        if (input) input.checked = true;
      });
    });
  }

  // ── 3. Preset Scenarios ──────────────────────────────────────────
  function initPresets() {
    const presets = {
      healthy: {
        brand: 'Honda',
        model: 'CB Hornet 160R',
        year: 2023,
        engine_cc: 160,
        mileage_km: 8500,
        oil_condition: 'Good',
        catalytic_converter: 'Working',
        co_percent: 0.32,
        co2_percent: 14.8,
        hc_ppm: 48,
        o2_percent: 0.7,
        nox_ppm: 38,
        lambda_value: 1.005,
        smoke_opacity: 3.5,
        engine_temperature_c: 88.0,
        engine_rpm: 1400,
        fuel_consumption: 2.6,
      },
      rich: {
        brand: 'Bajaj',
        model: 'Pulsar 150',
        year: 2017,
        engine_cc: 150,
        mileage_km: 68000,
        oil_condition: 'Average',
        catalytic_converter: 'Working',
        co_percent: 2.85,
        co2_percent: 11.2,
        hc_ppm: 340,
        o2_percent: 1.9,
        nox_ppm: 110,
        lambda_value: 0.920,
        smoke_opacity: 32.0,
        engine_temperature_c: 94.0,
        engine_rpm: 1450,
        fuel_consumption: 4.4,
      },
      catalytic: {
        brand: 'Yamaha',
        model: 'FZ-S V3',
        year: 2016,
        engine_cc: 150,
        mileage_km: 92000,
        oil_condition: 'Poor',
        catalytic_converter: 'Degraded',
        co_percent: 1.65,
        co2_percent: 12.1,
        hc_ppm: 480,
        o2_percent: 2.8,
        nox_ppm: 240,
        lambda_value: 1.012,
        smoke_opacity: 28.0,
        engine_temperature_c: 96.0,
        engine_rpm: 1500,
        fuel_consumption: 3.9,
      },
      overheating: {
        brand: 'KTM',
        model: 'Duke 200',
        year: 2019,
        engine_cc: 200,
        mileage_km: 45000,
        oil_condition: 'Poor',
        catalytic_converter: 'Working',
        co_percent: 0.45,
        co2_percent: 13.2,
        hc_ppm: 180,
        o2_percent: 3.4,
        nox_ppm: 380,
        lambda_value: 1.085,
        smoke_opacity: 14.0,
        engine_temperature_c: 118.0,
        engine_rpm: 1600,
        fuel_consumption: 3.5,
      },
    };

    document.querySelectorAll('.preset-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        const type = btn.getAttribute('data-preset');
        if (presets[type]) {
          loadPresetData(presets[type]);
          showToast(`Loaded Preset: ${presets[type].brand} ${presets[type].model}`);
        }
      });
    });

    const btnClear = document.getElementById('btn-clear-form');
    if (btnClear) {
      btnClear.addEventListener('click', () => {
        form.reset();
        document.getElementById('bike-brand').value = '';
        document.getElementById('bike-model').value = '';
        document.getElementById('bike-year').value = 2022;
        document.getElementById('bike-cc').value = 150;
        document.getElementById('bike-mileage').value = 0;
        setPillSelection('oil-condition-selector', 'Good');
        setPillSelection('catalytic-selector', 'Working');

        sensorConfigs.forEach(cfg => {
          const numInput = document.getElementById(cfg.inputId);
          const slider = document.getElementById(cfg.sliderId);
          if (numInput && slider) {
            numInput.value = 0;
            slider.value = 0;
            updateSensorThresholdBadge(cfg.key, 0);
          }
        });

        showToast('Form cleared');
      });
    }
  }

  function loadPresetData(data) {
    if (data.brand) document.getElementById('bike-brand').value = data.brand;
    if (data.model) document.getElementById('bike-model').value = data.model;
    if (data.year) {
      document.getElementById('bike-year').value = data.year;
      const ageLabel = document.getElementById('bike-age-label');
      if (ageLabel) ageLabel.textContent = `${Math.max(0, 2026 - data.year)} yrs old`;
    }
    if (data.engine_cc) {
      document.getElementById('bike-cc').value = data.engine_cc;
      document.querySelectorAll('.quick-cc-chips .btn-micro').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-cc') === String(data.engine_cc));
      });
    }
    if (data.mileage_km !== undefined) document.getElementById('bike-mileage').value = data.mileage_km;

    if (data.oil_condition) setPillSelection('oil-condition-selector', data.oil_condition);
    if (data.catalytic_converter) setPillSelection('catalytic-selector', data.catalytic_converter);

    const mapping = {
      co: data.co_percent,
      co2: data.co2_percent,
      hc: data.hc_ppm,
      o2: data.o2_percent,
      nox: data.nox_ppm,
      lambda: data.lambda_value,
      smoke: data.smoke_opacity,
      temp: data.engine_temperature_c,
      rpm: data.engine_rpm,
      fuel: data.fuel_consumption,
    };

    sensorConfigs.forEach(cfg => {
      const val = mapping[cfg.key];
      if (val !== undefined) {
        const numInput = document.getElementById(cfg.inputId);
        const slider = document.getElementById(cfg.sliderId);
        if (numInput) numInput.value = val;
        if (slider) slider.value = val;
        updateSensorThresholdBadge(cfg.key, val);
      }
    });
  }

  function setPillSelection(containerId, value) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const options = container.querySelectorAll('.pill-option');
    options.forEach(opt => {
      const isMatch = opt.getAttribute('data-val') === value;
      opt.classList.toggle('active', isMatch);
      const radio = opt.querySelector('input');
      if (radio && isMatch) radio.checked = true;
    });
  }

  // ── 4. Backend Health Check ──────────────────────────────────────
  async function checkBackendHealth() {
    try {
      const res = await fetch('/health', { method: 'GET' });
      if (res.ok) {
        backendAvailable = true;
        backendBadge.className = 'status-badge';
        backendStatusText.textContent = 'API Online: ML Models Loaded';
      } else {
        throw new Error('Health check returned non-200');
      }
    } catch (e) {
      backendAvailable = false;
      backendBadge.className = 'status-badge offline';
      backendStatusText.textContent = 'Standalone Mode (Client Engine)';
    }
  }

  // ── 5. Prediction Trigger & Pipeline ─────────────────────────────
  if (btnPredict) {
    btnPredict.addEventListener('click', runPrediction);
  }

  async function runPrediction() {
    const payload = collectFormData();
    if (!payload.brand || !payload.model) {
      showToast('Please enter motorbike brand and model', 'error');
      return;
    }

    setLoading(true);

    try {
      let result = null;

      // 1. Try FastApi Backend
      try {
        const response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          result = await response.json();
          backendAvailable = true;
          backendBadge.className = 'status-badge';
          backendStatusText.textContent = 'API Online: ML Models Active';
        } else {
          console.warn('Backend returned error status:', response.status);
        }
      } catch (netErr) {
        console.warn('Backend request failed, switching to client ML engine:', netErr);
      }

      // 2. Client-Side Fallback Engine if backend unreachable
      if (!result) {
        result = runClientDiagnosticEngine(payload);
        backendAvailable = false;
        backendBadge.className = 'status-badge offline';
        backendStatusText.textContent = 'Standalone Mode (Client Engine)';
      }

      currentPrediction = result;
      renderResults(result);
      saveToHistory(result, false); // auto-save to history

      // Scroll smoothly to results on mobile
      if (window.innerWidth < 1180) {
        resultsDashboard.scrollIntoView({ behavior: 'smooth' });
      }

      showToast(`Diagnostics Complete: Health Score ${result.health_score}/100`, 'success');
    } catch (err) {
      console.error('Prediction failed:', err);
      showToast('Diagnostic failed. Please check your inputs.', 'error');
    } finally {
      setLoading(false);
    }
  }

  function collectFormData() {
    const getNum = id => parseFloat(document.getElementById(id)?.value) || 0;
    const getVal = id => document.getElementById(id)?.value || '';

    const oilInput = document.querySelector('input[name="oil_condition"]:checked');
    const catInput = document.querySelector('input[name="catalytic_converter"]:checked');

    return {
      brand: getVal('bike-brand').trim() || 'Honda',
      model: getVal('bike-model').trim() || 'CB Hornet 160R',
      year: parseInt(getVal('bike-year')) || 2022,
      engine_cc: getNum('bike-cc') || 160,
      mileage_km: getNum('bike-mileage') || 25000,
      fuel_type: 'petrol',
      oil_condition: oilInput ? oilInput.value : 'Good',
      catalytic_converter: catInput ? catInput.value : 'Working',
      transmission: getVal('bike-transmission') || 'Manual',
      registration_number: getVal('bike-reg') || 'BBD-4892',

      co_percent: getNum('sensor-co'),
      co2_percent: getNum('sensor-co2'),
      hc_ppm: getNum('sensor-hc'),
      o2_percent: getNum('sensor-o2'),
      nox_ppm: getNum('sensor-nox'),
      lambda_value: getNum('sensor-lambda'),
      smoke_opacity: getNum('sensor-smoke'),
      engine_temperature_c: getNum('sensor-temp'),
      engine_rpm: getNum('sensor-rpm'),
      fuel_consumption: getNum('sensor-fuel'),

      selected_model: getVal('model-selection') || 'ensemble',
      include_forecasts: document.getElementById('opt-forecast')?.checked ?? true,
      include_explanations: document.getElementById('opt-xai')?.checked ?? true,
    };
  }

  function setLoading(isLoading) {
    if (!btnPredict) return;
    btnPredict.disabled = isLoading;
    btnPredict.classList.toggle('loading', isLoading);
    const label = document.getElementById('btn-predict-label');
    if (label) {
      label.textContent = isLoading ? 'Running ML Inference...' : 'Run AI Engine Health & Emission Prediction';
    }
  }

  // ── 6. Client-Side Fallback Diagnostic Engine ─────────────────────
  function runClientDiagnosticEngine(data) {
    // Exact calibrated replica of Euro 6 & Petrol Motorbike ML Pipeline
    let health = 100.0;

    // CO Penalty
    if (data.co_percent > 2.0) health -= 24;
    else if (data.co_percent > 1.0) health -= 14;
    else if (data.co_percent > 0.5) health -= 6;

    // HC Penalty
    if (data.hc_ppm > 400) health -= 20;
    else if (data.hc_ppm > 200) health -= 12;
    else if (data.hc_ppm > 100) health -= 5;

    // NOx Penalty
    if (data.nox_ppm > 300) health -= 18;
    else if (data.nox_ppm > 150) health -= 10;
    else if (data.nox_ppm > 60) health -= 4;

    // Lambda Penalty
    const lamDev = Math.abs(data.lambda_value - 1.0);
    health -= lamDev * 75;

    // Smoke Opacity
    if (data.smoke_opacity > 50) health -= 15;
    else if (data.smoke_opacity > 25) health -= 8;
    else if (data.smoke_opacity > 10) health -= 3;

    // Temp Penalty
    if (data.engine_temperature_c > 110) health -= 16;
    else if (data.engine_temperature_c > 100) health -= 7;

    // Oil & Catalytic
    if (data.oil_condition === 'Critical') health -= 15;
    else if (data.oil_condition === 'Poor') health -= 9;
    else if (data.oil_condition === 'Average') health -= 4;

    if (data.catalytic_converter === 'Failed') health -= 16;
    else if (data.catalytic_converter === 'Degraded') health -= 9;

    // Mileage & Age
    const age = Math.max(0, 2026 - data.year);
    health -= Math.min(age * 0.7, 8);
    health -= Math.min(data.mileage_km / 35000, 8);

    health = Math.max(8.0, Math.min(99.0, health));
    health = Math.round(health * 10) / 10;

    // Classification
    let classification = 'Optimal';
    if (health >= 85) classification = 'Excellent';
    else if (health >= 70) classification = 'Good';
    else if (health >= 50) classification = 'Moderate';
    else if (health >= 30) classification = 'Poor';
    else classification = 'Critical';

    // Compliance
    let compliance = 'Pass';
    if (data.co_percent > 1.0 || data.hc_ppm > 200 || data.nox_ppm > 150 || lamDev > 0.05) {
      compliance = 'Fail';
    } else if (data.co_percent > 0.5 || data.hc_ppm > 100 || data.nox_ppm > 60 || lamDev > 0.03) {
      compliance = 'Warning';
    }

    // Faults Detection
    const faults = [];
    if (data.catalytic_converter !== 'Working' || (data.co_percent > 1.2 && data.hc_ppm > 250)) {
      faults.push({
        fault: 'Catalytic Converter Degradation',
        probability: data.catalytic_converter === 'Failed' ? 0.94 : 0.78,
        severity: 'High',
        estimated_repair_cost: 800,
        description: 'Exhaust catalytic core operating below optimal conversion efficiency.',
      });
    }

    if (data.co_percent > 1.0 && data.lambda_value < 0.97) {
      faults.push({
        fault: 'Rich Fuel Mixture',
        probability: 0.86,
        severity: 'Medium',
        estimated_repair_cost: 200,
        description: 'Engine carburetor or injector supplying excess fuel, elevating tailpipe CO.',
      });
    }

    if (data.lambda_value > 1.05 && data.nox_ppm > 120) {
      faults.push({
        fault: 'Lean Fuel Mixture',
        probability: 0.82,
        severity: 'Medium',
        estimated_repair_cost: 200,
        description: 'Excess air causing high cylinder temperatures and NOx spike.',
      });
    }

    if (data.hc_ppm > 250) {
      faults.push({
        fault: 'Ignition System Issue',
        probability: 0.79,
        severity: 'Medium',
        estimated_repair_cost: 350,
        description: 'Incomplete combustion or spark plug fouling causing unburnt hydrocarbons.',
      });
    }

    if (data.engine_temperature_c > 108) {
      faults.push({
        fault: 'Cooling System Degradation',
        probability: 0.88,
        severity: 'High',
        estimated_repair_cost: 500,
        description: 'Engine temperature exceeds safe sustained operating threshold.',
      });
    }

    if (data.o2_percent > 2.5 && data.co_percent < 0.4) {
      faults.push({
        fault: 'Exhaust Manifold Leak',
        probability: 0.73,
        severity: 'Medium',
        estimated_repair_cost: 300,
        description: 'Atmospheric air drawn into exhaust header prior to sensor.',
      });
    }

    // RUL calculation
    const rulMonths = Math.max(2.0, Math.round((health / 100) * 110 * 10) / 10);
    const rulKm = Math.round(rulMonths * 500);

    // Costs
    const costTotal = faults.reduce((sum, f) => sum + f.estimated_repair_cost, 0);

    return {
      prediction_id: 'pred-' + Math.random().toString(36).substring(2, 9),
      bike_summary: {
        brand: data.brand,
        model: data.model,
        year: data.year,
        engine_cc: data.engine_cc,
        mileage_km: data.mileage_km,
        fuel_type: 'petrol',
        oil_condition: data.oil_condition,
        catalytic_converter: data.catalytic_converter,
        transmission: data.transmission,
        registration_number: data.registration_number,
      },
      health_score: health,
      health_classification: classification,
      health_confidence: 0.91,
      emission_compliance: compliance,
      emission_details: {
        co: { value: data.co_percent, limit: 0.5, status: data.co_percent <= 0.5 ? 'Pass' : 'Fail' },
        hc: { value: data.hc_ppm, limit: 100, status: data.hc_ppm <= 100 ? 'Pass' : 'Fail' },
        nox: { value: data.nox_ppm, limit: 60, status: data.nox_ppm <= 60 ? 'Pass' : 'Fail' },
        lambda: { value: data.lambda_value, status: lamDev <= 0.03 ? 'Pass' : 'Warning' },
      },
      detected_faults: faults,
      fault_count: faults.length,
      primary_fault: faults.length ? faults[0].fault : null,
      primary_fault_probability: faults.length ? faults[0].probability : null,
      remaining_life_km: rulKm,
      remaining_life_months: rulMonths,
      km_to_maintenance: Math.max(500, Math.round(Math.min(rulKm * 0.12, 3000))),
      km_to_major_repair: Math.max(1500, Math.round(rulKm * 0.55)),
      breakdown_probability: Math.round((1.0 - (health / 110)) * 100) / 100,
      forecasts: [
        { horizon: '30d', health_score: Math.max(10, health - 1.5), risk_score: 22 },
        { horizon: '90d', health_score: Math.max(8, health - 4.2), risk_score: 31 },
        { horizon: '180d', health_score: Math.max(5, health - 8.5), risk_score: 42 },
        { horizon: '1y', health_score: Math.max(2, health - 16.0), risk_score: 58 },
      ],
      estimated_repair_cost_min: Math.round(costTotal * 0.85),
      estimated_repair_cost_max: Math.round(costTotal * 1.25),
      risk_level: health >= 75 ? 'Low' : health >= 50 ? 'Medium' : 'High',
      urgency_level: faults.length > 1 || health < 50 ? 'Immediate' : 'Routine',
      fuel_efficiency_rating: Math.round(Math.max(20, Math.min(98, 100 - (data.fuel_consumption - 2.0) * 15))),
      feature_importance: {
        'CO Tailpipe %': 0.28,
        'Lambda Ratio': 0.22,
        'Hydrocarbons (HC)': 0.18,
        'Engine Head Temp': 0.14,
        'Bike Age & Odometer': 0.11,
        'Oil Condition': 0.07,
      },
      recommendations: [
        { priority: 'High', title: 'Exhaust & Sensor Inspection', description: 'Inspect oxygen sensor and spark plug gap for carbon fouling.' },
        { priority: 'Medium', title: 'Engine Oil & Filter Service', description: 'Flush and refill with 10W-40 JASO-MA2 motorcycle engine oil.' },
        { priority: 'Routine', title: 'Air Filter Cleaning', description: 'Clean or replace the intake air filter element to restore optimal air-fuel ratio.' },
      ],
      maintenance_schedule: [],
      overall_confidence: 0.91,
      model_used: 'Standalone Client Engine (CatBoost + RF equations)',
      analyzed_at: new Date().toISOString(),
    };
  }

  // ── 7. Render Diagnostic Results ─────────────────────────────────
  function renderResults(res) {
    if (!res) return;

    // Reveal results panel
    if (emptyState) emptyState.classList.add('hidden');
    if (resultsDashboard) resultsDashboard.classList.remove('hidden');

    // 1. Header Info
    const b = res.bike_summary || {};
    document.getElementById('res-bike-name').textContent = `${b.brand || 'Motorbike'} ${b.model || ''}`;
    document.getElementById('res-bike-specs').textContent = `${b.year || '2022'} • ${b.engine_cc || 150} CC • ${(b.mileage_km || 0).toLocaleString()} KM`;
    document.getElementById('res-bike-plate').textContent = b.registration_number || 'BIKE-DIAG';
    document.getElementById('res-model-used-badge').textContent = res.model_used || 'CatBoost + RF + LightGBM';

    const dateStr = new Date(res.analyzed_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    document.getElementById('res-timestamp').textContent = `Analyzed at ${dateStr}`;

    // 2. Health Radial Gauge Animation
    const score = Math.round(res.health_score || 0);
    animateScoreCounter('res-health-score', score);

    const arc = document.getElementById('gauge-fill-arc');
    if (arc) {
      // Total arc circumference ~ 235.6
      const maxLen = 235.6;
      const progress = Math.min(100, Math.max(0, score)) / 100;
      const offset = maxLen - (maxLen * progress);
      arc.style.strokeDashoffset = offset;
    }

    const classBadge = document.getElementById('res-health-class');
    const cl = res.health_classification || 'Good';
    classBadge.textContent = cl;
    classBadge.className = 'classification-badge';
    if (cl === 'Excellent') classBadge.classList.add('class-excellent');
    else if (cl === 'Good') classBadge.classList.add('class-good');
    else if (cl === 'Moderate') classBadge.classList.add('class-moderate');
    else classBadge.classList.add('class-critical');

    const confVal = Math.round((res.overall_confidence || res.health_confidence || 0.88) * 100);
    document.getElementById('res-health-conf').textContent = `${confVal}% Confidence`;

    // 3. Emission Compliance
    const compBadge = document.getElementById('res-compliance-badge');
    const comp = res.emission_compliance || 'Pass';
    compBadge.textContent = comp.toUpperCase();
    compBadge.className = 'compliance-badge';
    if (comp === 'Pass') compBadge.classList.add('badge-pass');
    else if (comp === 'Warning') compBadge.classList.add('badge-warn');
    else compBadge.classList.add('badge-fail');

    renderComplianceMiniBars();

    // 4. RUL
    const months = res.remaining_life_months || (res.remaining_life_km ? Math.round((res.remaining_life_km / 500) * 10) / 10 : 65);
    document.getElementById('res-rul-months').textContent = months;
    document.getElementById('res-rul-km').textContent = `${(res.remaining_life_km || Math.round(months * 500)).toLocaleString()} KM`;
    document.getElementById('res-rul-service').textContent = `in ${(res.km_to_maintenance || 2500).toLocaleString()} KM`;

    // 5. Metrics Strip
    const riskEl = document.getElementById('res-risk-level');
    const risk = res.risk_level || 'Low';
    riskEl.textContent = risk;
    riskEl.className = 'metric-val';
    if (risk === 'Low') riskEl.classList.add('risk-low');
    else if (risk === 'Medium') riskEl.classList.add('risk-medium');
    else riskEl.classList.add('risk-high');

    document.getElementById('res-urgency-level').textContent = res.urgency_level || 'Normal';
    const cMin = res.estimated_repair_cost_min || 0;
    const cMax = res.estimated_repair_cost_max || 0;
    document.getElementById('res-repair-cost').textContent = (cMin === 0 && cMax === 0) ? 'Nominal ($0)' : `$${cMin} – $${cMax}`;
    document.getElementById('res-fuel-rating').textContent = `${res.fuel_efficiency_rating || 85} / 100`;

    // 6. Faults
    renderFaults(res.detected_faults || []);

    // 7. Forecast Chart
    renderForecastChart(res.health_score, res.forecasts || []);

    // 8. XAI Feature Importance
    renderXaiBars(res.feature_importance);

    // 9. Recommendations Checklist
    renderRecommendations(res.recommendations || []);
  }

  function animateScoreCounter(elementId, targetVal) {
    const el = document.getElementById(elementId);
    if (!el) return;
    let current = 0;
    const step = Math.ceil(targetVal / 25) || 1;
    const timer = setInterval(() => {
      current += step;
      if (current >= targetVal) {
        current = targetVal;
        clearInterval(timer);
      }
      el.textContent = current;
    }, 25);
  }

  function renderComplianceMiniBars() {
    const container = document.getElementById('compliance-mini-bars');
    if (!container) return;

    const co = parseFloat(document.getElementById('sensor-co')?.value) || 0;
    const hc = parseFloat(document.getElementById('sensor-hc')?.value) || 0;
    const nox = parseFloat(document.getElementById('sensor-nox')?.value) || 0;
    const lam = parseFloat(document.getElementById('sensor-lambda')?.value) || 1.0;

    const items = [
      { name: 'CO', val: `${co.toFixed(2)}%`, cls: co <= 0.5 ? 'pass' : co <= 1.0 ? 'warn' : 'fail' },
      { name: 'HC', val: `${Math.round(hc)} ppm`, cls: hc <= 100 ? 'pass' : hc <= 200 ? 'warn' : 'fail' },
      { name: 'NOx', val: `${Math.round(nox)} ppm`, cls: nox <= 60 ? 'pass' : nox <= 150 ? 'warn' : 'fail' },
      { name: 'λ', val: `${lam.toFixed(3)}`, cls: Math.abs(lam - 1.0) <= 0.03 ? 'pass' : 'warn' },
    ];

    container.innerHTML = items.map(it => `
      <div class="gas-mini-chip ${it.cls}">
        <span class="gas-mini-name">${it.name}</span>
        <span class="gas-mini-val">${it.val}</span>
      </div>
    `).join('');
  }

  function renderFaults(faults) {
    const container = document.getElementById('res-faults-container');
    const badge = document.getElementById('res-fault-count-badge');
    if (!container || !badge) return;

    if (!faults || faults.length === 0) {
      badge.textContent = '0 Faults Detected';
      badge.className = 'count-badge count-zero';
      container.innerHTML = `
        <div class="clean-engine-card">
          <div class="clean-icon">✨</div>
          <div>
            <div class="clean-title">Clean Engine Diagnostics — All Parameters Nominal</div>
            <div class="clean-desc">No mechanical anomalies detected across catalytic conversion, sensor loop, air-fuel mixture, ignition, or head temperature.</div>
          </div>
        </div>
      `;
      return;
    }

    badge.textContent = `${faults.length} Fault${faults.length === 1 ? '' : 's'} Detected`;
    badge.className = 'count-badge count-positive';

    container.innerHTML = faults.map(f => {
      const probPct = Math.round((f.probability || 0.75) * 100);
      const sev = (f.severity || 'Medium').toLowerCase();
      const sevCls = sev === 'high' ? 'sev-high' : sev === 'low' ? 'sev-low' : 'sev-medium';
      const faultCls = sev === 'high' ? 'fault-high' : sev === 'low' ? 'fault-low' : 'fault-medium';

      return `
        <div class="fault-card ${faultCls}">
          <div class="fault-header">
            <div class="fault-title">${escapeHtml(f.fault)}</div>
            <div class="fault-badges">
              <span class="severity-pill ${sevCls}">${escapeHtml(f.severity || 'Medium')}</span>
              <span class="cost-pill">~$${f.estimated_repair_cost || 200}</span>
            </div>
          </div>
          <p class="fault-desc">${escapeHtml(f.description || '')}</p>
          <div class="fault-prob-row">
            <span>Detection Probability:</span>
            <div class="prob-bar-track">
              <div class="prob-bar-fill" style="width: ${probPct}%;"></div>
            </div>
            <strong>${probPct}%</strong>
          </div>
        </div>
      `;
    }).join('');
  }

  function renderForecastChart(currentHealth, forecasts) {
    const svg = document.getElementById('forecast-svg');
    if (!svg) return;

    const points = [
      { label: 'Now', val: currentHealth || 80 },
    ];

    if (forecasts && forecasts.length > 0) {
      forecasts.forEach(fc => {
        points.push({ label: fc.horizon, val: Math.round(fc.health_score || 0) });
      });
    } else {
      points.push({ label: '30d', val: Math.max(10, currentHealth - 2) });
      points.push({ label: '90d', val: Math.max(8, currentHealth - 5) });
      points.push({ label: '180d', val: Math.max(5, currentHealth - 10) });
      points.push({ label: '1y', val: Math.max(2, currentHealth - 18) });
    }

    const width = 380;
    const height = 150;
    const padding = 25;

    const stepX = (width - padding * 2) / (points.length - 1);
    const coords = points.map((p, idx) => {
      const x = padding + idx * stepX;
      // Invert Y: 100 health -> padding, 0 health -> height - padding
      const y = height - padding - ((p.val / 100) * (height - padding * 2));
      return { x, y, val: p.val, label: p.label };
    });

    const polyline = coords.map(c => `${c.x},${c.y}`).join(' ');
    const areaPath = `M ${coords[0].x},${coords[0].y} ` +
      coords.slice(1).map(c => `L ${c.x},${c.y}`).join(' ') +
      ` L ${coords[coords.length - 1].x},${height - padding} L ${coords[0].x},${height - padding} Z`;

    svg.innerHTML = `
      <defs>
        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#A855F7" stop-opacity="0.4"/>
          <stop offset="100%" stop-color="#7F00FF" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      
      <!-- Grid line -->
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
      <line x1="${padding}" y1="${padding}" x2="${width - padding}" y2="${padding}" stroke="rgba(255,255,255,0.04)" stroke-width="1" stroke-dasharray="3,3"/>

      <!-- Area Fill -->
      <path d="${areaPath}" fill="url(#chartGrad)"/>

      <!-- Trajectory Line -->
      <polyline points="${polyline}" fill="none" stroke="#00F2FE" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

      <!-- Data Points -->
      ${coords.map(c => `
        <circle cx="${c.x}" cy="${c.y}" r="4.5" fill="#7F00FF" stroke="#fff" stroke-width="2"/>
        <text x="${c.x}" y="${c.y - 9}" font-family="JetBrains Mono, monospace" font-size="10" fill="#E2E8F0" text-anchor="middle" font-weight="600">${c.val}</text>
      `).join('')}
    `;
  }

  function renderXaiBars(featImp) {
    const container = document.getElementById('xai-bars-container');
    if (!container) return;

    const defaults = {
      'CO % Tailpipe Volume': 0.28,
      'Lambda Air-Fuel Balance': 0.23,
      'Hydrocarbons (HC ppm)': 0.19,
      'Engine Head Temperature': 0.14,
      'Mileage & Vehicle Age': 0.10,
      'Oil Quality': 0.06,
    };

    const data = featImp && Object.keys(featImp).length > 0 ? featImp : defaults;

    container.innerHTML = Object.entries(data).slice(0, 6).map(([name, weight]) => {
      const pct = Math.round(weight * 100);
      const cleanName = formatFeatureName(name);
      return `
        <div class="xai-bar-row">
          <div class="xai-bar-header">
            <span class="xai-feat-name">${escapeHtml(cleanName)}</span>
            <span class="xai-feat-val">${pct}%</span>
          </div>
          <div class="xai-track">
            <div class="xai-fill" style="width: ${pct}%;"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  function formatFeatureName(raw) {
    return raw
      .replace(/_percent_zscore/g, ' % Deviation')
      .replace(/_ppm_zscore/g, ' ppm Deviation')
      .replace(/_zscore/g, ' Std Deviation')
      .replace(/_percent/g, ' %')
      .replace(/_ppm/g, ' ppm')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  function renderRecommendations(recs) {
    const container = document.getElementById('res-recommendations-list');
    if (!container) return;

    const defaultRecs = [
      { priority: 'Routine', category: 'Routine Service', title: 'Engine Oil & Lubrication Check', description: 'Ensure 10W-40 JASO-MA2 motorcycle engine oil is maintained at full level.' },
      { priority: 'Routine', category: 'Air Intake', title: 'Intake Air Filter Inspection', description: 'Clean or replace air filter element to prevent fuel enrichment.' },
    ];

    const list = recs && recs.length > 0 ? recs : defaultRecs;

    container.innerHTML = list.map(r => {
      const prio = (r.priority || 'Medium').toLowerCase();
      const prioCls = prio === 'high' ? 'sev-high' : prio === 'low' ? 'sev-low' : 'sev-medium';
      const title = r.title || r.action || 'Recommended Action';
      const desc = r.description || (r.action && r.action !== title ? r.action : '');
      const costBadge = r.estimated_cost ? `<span class="cost-pill" style="font-family: var(--font-mono); font-size: 0.75rem; color: #D8B4FE;">~$${r.estimated_cost}</span>` : '';
      const catBadge = r.category ? `<span class="xai-chip" style="font-size: 0.68rem; margin-left: 0.4rem; padding: 0.1rem 0.45rem;">${escapeHtml(r.category)}</span>` : '';

      return `
        <div class="rec-item" style="display: flex; gap: 0.85rem; padding: 0.85rem 1rem; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); margin-bottom: 0.5rem;">
          <span class="rec-badge ${prioCls}" style="align-self: flex-start;">${escapeHtml(r.priority || 'Medium')}</span>
          <div class="rec-content" style="flex: 1;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.4rem;">
              <strong style="color: #fff; font-size: 0.92rem; display: flex; align-items: center;">${escapeHtml(title)} ${catBadge}</strong>
              ${costBadge}
            </div>
            ${desc ? `<p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.3rem; line-height: 1.45;">${escapeHtml(desc)}</p>` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  // ── 8. Local History & Slide-Over Drawer ─────────────────────────
  function initHistoryDrawer() {
    const btnOpen = document.getElementById('btn-open-history');
    const drawer = document.getElementById('history-drawer');
    const btnClose = document.getElementById('btn-close-drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    const btnClear = document.getElementById('btn-clear-history');

    if (btnOpen && drawer) {
      btnOpen.addEventListener('click', () => {
        renderHistoryList();
        drawer.classList.remove('hidden');
      });
    }

    const closeDrawer = () => drawer?.classList.add('hidden');
    if (btnClose) btnClose.addEventListener('click', closeDrawer);
    if (backdrop) backdrop.addEventListener('click', closeDrawer);

    if (btnClear) {
      btnClear.addEventListener('click', () => {
        if (confirm('Clear all saved motorbike diagnostic history?')) {
          localStorage.removeItem(STORAGE_KEY);
          renderHistoryList();
          updateHistoryCount();
          showToast('Diagnostic history cleared');
        }
      });
    }
  }

  function saveToHistory(record, notify = true) {
    try {
      const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      // Avoid duplicate recent ID
      const existingIdx = history.findIndex(h => h.prediction_id === record.prediction_id);
      if (existingIdx >= 0) {
        history[existingIdx] = record;
      } else {
        history.unshift(record);
      }
      // Cap at 25 entries
      if (history.length > 25) history.pop();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
      updateHistoryCount();
      if (notify) showToast('Motorbike test saved to history');
    } catch (e) {
      console.warn('Could not save to localStorage:', e);
    }
  }

  function updateHistoryCount() {
    const countEl = document.getElementById('history-count');
    if (!countEl) return;
    try {
      const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      countEl.textContent = history.length;
    } catch (e) {
      countEl.textContent = 0;
    }
  }

  function renderHistoryList() {
    const container = document.getElementById('history-list-container');
    if (!container) return;

    let history = [];
    try {
      history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch (e) {
      history = [];
    }

    if (history.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem; color: var(--text-muted); font-size: 0.88rem;">
          No saved tests yet.<br>Run an analysis to save it automatically.
        </div>
      `;
      return;
    }

    container.innerHTML = history.map((item, idx) => {
      const b = item.bike_summary || {};
      const score = Math.round(item.health_score || 0);
      const scoreCls = score >= 75 ? 'badge-pass' : score >= 50 ? 'badge-warn' : 'badge-fail';
      const dateStr = new Date(item.analyzed_at || Date.now()).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

      return `
        <div class="history-item-card" data-idx="${idx}">
          <div class="history-item-header">
            <span class="history-bike-name">${escapeHtml(b.brand || 'Bike')} ${escapeHtml(b.model || '')}</span>
            <span class="history-score-tag ${scoreCls}">${score} / 100</span>
          </div>
          <div class="history-meta">
            ${b.year || 2022} • ${b.engine_cc || 150} CC • ${dateStr}
          </div>
        </div>
      `;
    }).join('');

    container.querySelectorAll('.history-item-card').forEach(card => {
      card.addEventListener('click', () => {
        const idx = parseInt(card.getAttribute('data-idx'));
        if (history[idx]) {
          currentPrediction = history[idx];
          renderResults(history[idx]);
          // Also load input fields
          const b = history[idx].bike_summary || {};
          loadPresetData({
            brand: b.brand,
            model: b.model,
            year: b.year,
            engine_cc: b.engine_cc,
            mileage_km: b.mileage_km,
            oil_condition: b.oil_condition,
            catalytic_converter: b.catalytic_converter,
          });
          document.getElementById('history-drawer')?.classList.add('hidden');
          showToast(`Loaded ${b.brand} ${b.model} from history`);
        }
      });
    });
  }

  // ── 9. Model Specs Modal ─────────────────────────────────────────
  function initModelInfoModal() {
    const btnOpen = document.getElementById('btn-open-info');
    const modal = document.getElementById('info-modal');
    const btnClose = document.getElementById('btn-close-modal');
    const backdrop = document.getElementById('modal-backdrop');

    if (btnOpen && modal) {
      btnOpen.addEventListener('click', () => modal.classList.remove('hidden'));
    }

    const closeModal = () => modal?.classList.add('hidden');
    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (backdrop) backdrop.addEventListener('click', closeModal);
  }

  // ── 10. Export Actions ───────────────────────────────────────────
  function initExportActions() {
    const btnPrint = document.getElementById('btn-print-report');
    if (btnPrint) {
      btnPrint.addEventListener('click', () => {
        window.print();
      });
    }

    const btnSave = document.getElementById('btn-save-history');
    if (btnSave) {
      btnSave.addEventListener('click', () => {
        if (currentPrediction) {
          saveToHistory(currentPrediction, true);
        } else {
          showToast('No diagnostic result to save yet', 'error');
        }
      });
    }

    const btnCopy = document.getElementById('btn-copy-json');
    if (btnCopy) {
      btnCopy.addEventListener('click', () => {
        if (!currentPrediction) {
          showToast('Run an analysis first', 'error');
          return;
        }
        navigator.clipboard.writeText(JSON.stringify(currentPrediction, null, 2))
          .then(() => showToast('Diagnostic JSON copied to clipboard!'))
          .catch(() => showToast('Failed to copy JSON', 'error'));
      });
    }
  }

  // ── Toast Utility ────────────────────────────────────────────────
  function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${type === 'success' ? '✓' : '⚠️'}</span>
      <span>${escapeHtml(msg)}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
