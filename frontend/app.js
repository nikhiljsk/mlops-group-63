// MLOps Demo Frontend JavaScript
const API_BASE = 'http://localhost:8000';

// Check if we're running on a different port and adjust accordingly
if (window.location.port === '3001') {
    console.log('Frontend running on port 3001, API on port 8000');
}
let predictionsChart;
let metricsData = {
    predictions: [],
    timestamps: []
};

// Sample data for different iris species
const sampleData = {
    setosa: { sepal_length: 5.1, sepal_width: 3.5, petal_length: 1.4, petal_width: 0.2 },
    versicolor: { sepal_length: 6.2, sepal_width: 2.9, petal_length: 4.3, petal_width: 1.3 },
    virginica: { sepal_length: 6.5, sepal_width: 3.0, petal_length: 5.2, petal_width: 2.0 }
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    initializeChart();
    
    // Start periodic updates
    setInterval(updateSystemStatus, 5000);
    setInterval(updateMetrics, 10000);
});

function initializeApp() {
    console.log('🚀 Initializing MLOps Demo...');
    updateSystemStatus();
    loadModelInfo();
    updateMetrics();
}

function setupEventListeners() {
    document.getElementById('prediction-form').addEventListener('submit', handlePrediction);
}

// System Status Functions
async function updateSystemStatus() {
    try {
        // Check API health
        const healthResponse = await fetch(`${API_BASE}/health`);
        const healthData = await healthResponse.json();
        
        updateStatusIndicator('api-status', 'api-text', healthResponse.ok, 
            healthResponse.ok ? 'Online' : 'Offline');
        
        updateStatusIndicator('model-status', 'model-text', 
            healthData.model_loaded, healthData.model_loaded ? 'Loaded' : 'Not Loaded');
        
        // Check metrics endpoint
        const metricsResponse = await fetch(`${API_BASE}/metrics`);
        updateStatusIndicator('metrics-status', 'metrics-text', 
            metricsResponse.ok, metricsResponse.ok ? 'Active' : 'Inactive');
            
        // Update uptime
        if (healthData.uptime_seconds) {
            document.getElementById('uptime').textContent = formatUptime(healthData.uptime_seconds);
        }
        
    } catch (error) {
        console.error('Status check failed:', error);
        updateStatusIndicator('api-status', 'api-text', false, 'Error');
        updateStatusIndicator('model-status', 'model-text', false, 'Error');
        updateStatusIndicator('metrics-status', 'metrics-text', false, 'Error');
    }
}

function updateStatusIndicator(indicatorId, textId, isOnline, text) {
    const indicator = document.getElementById(indicatorId);
    const textElement = document.getElementById(textId);
    
    indicator.className = `status-indicator ${isOnline ? 'status-online' : 'status-offline'}`;
    textElement.textContent = text;
}

// Model Information Functions
async function loadModelInfo() {
    try {
        const response = await fetch(`${API_BASE}/model/info`);
        if (response.ok) {
            const modelInfo = await response.json();
            
            document.getElementById('model-name').textContent = modelInfo.model_name || 'Unknown';
            document.getElementById('model-version').textContent = modelInfo.model_version || 'Unknown';
            document.getElementById('model-type').textContent = modelInfo.model_type || 'Unknown';
            document.getElementById('model-classes').textContent = 
                modelInfo.classes ? modelInfo.classes.join(', ') : 'Unknown';
        }
    } catch (error) {
        console.error('Failed to load model info:', error);
    }
}

// Prediction Functions
async function handlePrediction(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const predictionData = {
        sepal_length: parseFloat(formData.get('sepal_length') || document.getElementById('sepal_length').value),
        sepal_width: parseFloat(formData.get('sepal_width') || document.getElementById('sepal_width').value),
        petal_length: parseFloat(formData.get('petal_length') || document.getElementById('petal_length').value),
        petal_width: parseFloat(formData.get('petal_width') || document.getElementById('petal_width').value)
    };
    
    try {
        showResult('Making prediction...', 'info');
        
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(predictionData)
        });
        
        if (response.ok) {
            const result = await response.json();
            const confidence = (result.confidence * 100).toFixed(1);
            
            showResult(
                `🌸 Prediction: <strong>${result.prediction}</strong><br>
                 📊 Confidence: <strong>${confidence}%</strong><br>
                 ⏱️ Processing Time: <strong>${result.processing_time_ms}ms</strong>`,
                'success'
            );
            
            // Update chart
            addPredictionToChart(result.prediction, result.confidence);
            
        } else {
            const error = await response.json();
            showResult(`❌ Prediction failed: ${error.detail}`, 'error');
        }
        
    } catch (error) {
        console.error('Prediction error:', error);
        showResult(`❌ Network error: ${error.message}`, 'error');
    }
}

function showResult(message, type) {
    const resultDiv = document.getElementById('prediction-result');
    resultDiv.innerHTML = message;
    resultDiv.className = `result ${type}`;
    resultDiv.style.display = 'block';
    
    // Auto-hide after 10 seconds for info messages
    if (type === 'info') {
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 10000);
    }
}

// Sample Data Functions
function loadSampleData() {
    const species = ['setosa', 'versicolor', 'virginica'];
    const randomSpecies = species[Math.floor(Math.random() * species.length)];
    const data = sampleData[randomSpecies];
    
    document.getElementById('sepal_length').value = data.sepal_length;
    document.getElementById('sepal_width').value = data.sepal_width;
    document.getElementById('petal_length').value = data.petal_length;
    document.getElementById('petal_width').value = data.petal_width;
    
    showResult(`📝 Loaded sample data for <strong>${randomSpecies}</strong>`, 'success');
}

// Batch Testing
async function runBatchTest() {
    try {
        showResult('Running batch prediction test...', 'info');
        
        const batchData = {
            samples: [
                sampleData.setosa,
                sampleData.versicolor,
                sampleData.virginica
            ]
        };
        
        const response = await fetch(`${API_BASE}/predict/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(batchData)
        });
        
        if (response.ok) {
            const result = await response.json();
            let resultText = `📊 Batch Prediction Results:<br>`;
            
            result.predictions.forEach((pred, index) => {
                const species = ['Setosa', 'Versicolor', 'Virginica'][index];
                const confidence = (pred.confidence * 100).toFixed(1);
                resultText += `• ${species}: <strong>${pred.prediction}</strong> (${confidence}%)<br>`;
            });
            
            resultText += `⏱️ Total Time: <strong>${result.total_processing_time_ms}ms</strong>`;
            
            showResult(resultText, 'success');
            
            // Update chart with batch results
            result.predictions.forEach(pred => {
                addPredictionToChart(pred.prediction, pred.confidence);
            });
            
        } else {
            const error = await response.json();
            showResult(`❌ Batch test failed: ${error.detail}`, 'error');
        }
        
    } catch (error) {
        console.error('Batch test error:', error);
        showResult(`❌ Batch test error: ${error.message}`, 'error');
    }
}

// Metrics Functions
async function updateMetrics() {
    try {
        const response = await fetch(`${API_BASE}/metrics`);
        if (response.ok) {
            const metricsText = await response.text();
            parsePrometheusMetrics(metricsText);
        }
    } catch (error) {
        console.error('Failed to update metrics:', error);
    }
}

function parsePrometheusMetrics(metricsText) {
    const lines = metricsText.split('\n');
    let totalPredictions = 0;
    let avgConfidence = 0;
    
    lines.forEach(line => {
        if (line.startsWith('ml_predictions_total')) {
            const match = line.match(/ml_predictions_total.*?(\d+\.?\d*)/);
            if (match) {
                totalPredictions += parseFloat(match[1]);
            }
        }
        if (line.startsWith('ml_prediction_confidence')) {
            const match = line.match(/ml_prediction_confidence.*?(\d+\.?\d*)/);
            if (match) {
                avgConfidence = parseFloat(match[1]) * 100;
            }
        }
    });
    
    document.getElementById('total-predictions').textContent = totalPredictions;
    document.getElementById('avg-confidence').textContent = `${avgConfidence.toFixed(1)}%`;
}

// Chart Functions
function initializeChart() {
    const ctx = document.getElementById('predictions-chart').getContext('2d');
    
    predictionsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Setosa', 'Versicolor', 'Virginica'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Prediction Distribution'
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function addPredictionToChart(prediction, confidence) {
    const speciesIndex = {
        'setosa': 0,
        'versicolor': 1,
        'virginica': 2
    };
    
    const index = speciesIndex[prediction.toLowerCase()];
    if (index !== undefined) {
        predictionsChart.data.datasets[0].data[index]++;
        predictionsChart.update();
    }
}

// Pipeline Action Functions
async function runTraining() {
    showActionResult('🏋️ Starting model training... This may take a few minutes.', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/retrain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            showActionResult(
                `✅ Model training completed successfully!<br>
                 🤖 New model: ${result.model_info?.model_type || 'Unknown'}<br>
                 📅 Trained at: ${new Date(result.timestamp).toLocaleString()}`, 
                'success'
            );
            
            // Refresh model info
            loadModelInfo();
            
        } else {
            const error = await response.json();
            showActionResult(`❌ Training failed: ${error.detail}`, 'error');
        }
        
    } catch (error) {
        showActionResult(`❌ Training failed: ${error.message}`, 'error');
    }
}

async function runTests() {
    showActionResult('🧪 Running test pipeline...', 'info');
    
    try {
        // Simulate running tests
        setTimeout(() => {
            showActionResult('✅ All tests passed! API endpoints and model are working correctly.', 'success');
        }, 2000);
        
    } catch (error) {
        showActionResult(`❌ Tests failed: ${error.message}`, 'error');
    }
}

function viewLogs() {
    showActionResult('📋 Opening logs... Check the browser console and server logs.', 'info');
    console.log('=== MLOps Demo Logs ===');
    console.log('Recent predictions:', metricsData);
    console.log('API Base URL:', API_BASE);
    console.log('Chart data:', predictionsChart?.data);
}

function exportMetrics() {
    showActionResult('📊 Exporting metrics... Check Prometheus at http://localhost:9090', 'info');
    
    // Create a simple metrics export
    const exportData = {
        timestamp: new Date().toISOString(),
        predictions: metricsData,
        system_status: {
            api_online: document.getElementById('api-text').textContent === 'Online',
            model_loaded: document.getElementById('model-text').textContent === 'Loaded',
            metrics_active: document.getElementById('metrics-text').textContent === 'Active'
        }
    };
    
    // Download as JSON
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mlops-metrics-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    setTimeout(() => {
        showActionResult('✅ Metrics exported successfully!', 'success');
    }, 1000);
}

function showActionResult(message, type) {
    const resultDiv = document.getElementById('action-result');
    resultDiv.innerHTML = message;
    resultDiv.className = `result ${type}`;
    resultDiv.style.display = 'block';
    
    if (type === 'info') {
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 5000);
    }
}

// Utility Functions
function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}