const fileInput = document.getElementById('file-input');
const cameraInput = document.getElementById('camera-input');
const uploadSection = document.querySelector('.upload-section');

// --- BUTTON HANDLERS ---
const btnCamera = document.getElementById('direct-camera-btn');
const btnGallery = document.getElementById('direct-gallery-btn');

const previewArea = document.getElementById('preview-area');
const previewImg = document.getElementById('preview-img');
const loadingSpinner = document.getElementById('loading');
const analyzingText = document.getElementById('analyzing-text');
const resultsArea = document.getElementById('results-area');

// --- GEMINI API INTEGRATION ---

// IMPORTANT: Replace this with your actual Gemini API Key


async function callGeminiAPI(base64Image) {
    
    if (!base64Image) return;
    const cleanBase64 = base64Image.split(',')[1];

    try {
    
        const response = await fetch('/api/analyze-crop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: cleanBase64 })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Server Error');
        }

    
        showResults(result);

    } catch (error) {
        console.error("Diagnosis Error:", error);
        alert("Error analyzing image: " + error.message);
        resetUI();
    }
}
// Reuseable Image Handler
function handleImageSelection(e) {
    const file = e.target.files[0];
    if (file) {
        // UI State: Loading
        previewArea.style.display = 'block';
        resultsArea.style.display = 'none';
        loadingSpinner.style.display = 'block';
        analyzingText.style.display = 'block';
        previewImg.style.opacity = '0.7';

        // Auto-scroll to show the user that something is happening
        previewArea.scrollIntoView({ behavior: 'smooth', block: 'center' });

        const reader = new FileReader();
        reader.onload = function (e) {
            const base64Image = e.target.result;
            previewImg.src = base64Image;

            // Call API after slight delay to ensure UI updates
            setTimeout(() => callGeminiAPI(base64Image), 500);
        }
        reader.readAsDataURL(file);
    }
}

// Attach Handlers to Inputs
fileInput.addEventListener('change', handleImageSelection);
cameraInput.addEventListener('change', handleImageSelection);

// --- MODAL LOGIC ---
if (btnCamera) {
    btnCamera.addEventListener('click', () => {
        cameraInput.click();
    });
}

if (btnGallery) {
    btnGallery.addEventListener('click', () => {
        fileInput.click();
    });
}



function showResults(result, saveToHistory = true) {
    // Hide upload section to clear the view
    if (uploadSection) uploadSection.style.display = 'none';

    // Hide loading states
    loadingSpinner.style.display = 'none';
    analyzingText.style.display = 'none';
    previewImg.style.opacity = '1';

    // Update UI with real data

    // Show Image in Report
    const resultImg = document.getElementById('result-display-img');
    if (resultImg) {
        resultImg.src = previewImg.src;
    }

    // Helper to check for healthy
    const isHealthy = result.name.toLowerCase().includes("healthy");

    document.getElementById('disease-name').textContent = result.name;
    document.getElementById('disease-name').style.color = isHealthy ? "#2e7d32" : "#d32f2f";
    document.getElementById('disease-desc').textContent = result.description;
    document.getElementById('confidence-val').textContent = result.confidence + "%";

    // Animate Bar
    setTimeout(() => {
        document.getElementById('confidence-bar').style.width = result.confidence + "%";
        document.getElementById('confidence-bar').style.backgroundColor = result.confidence > 90 ? "#2e7d32" : "#fbc02d";
    }, 100);

    // Populate Treatments
    const list = document.getElementById('treatment-list');
    list.innerHTML = '';

    // Handle if treatments is null/empty or valid array
    const treatments = result.treatments || ["Consult a local agricultural expert."];
    treatments.forEach(t => {
        const li = document.createElement('li');
        li.textContent = t;
        list.appendChild(li);
    });

    // Show Results Area
    resultsArea.style.display = 'block';
    resultsArea.scrollIntoView({ behavior: 'smooth' });

    if (saveToHistory) {
        // Save current state
        sessionStorage.setItem('diagnosisResult', JSON.stringify(result));
        sessionStorage.setItem('diagnosisImage', previewImg.src);

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        addToHistory({ result, image: previewImg.src, timestamp });
    }
}

function resetUI() {
    loadingSpinner.style.display = 'none';
    analyzingText.style.display = 'none';
    previewImg.style.opacity = '1';
}

function resetDiagnosis() {
    // Show upload section again
    if (uploadSection) uploadSection.style.display = 'block';

    fileInput.value = '';
    cameraInput.value = '';
    previewArea.style.display = 'none';
    resultsArea.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Clear current View session but KEEP History
    sessionStorage.removeItem('diagnosisResult');
    sessionStorage.removeItem('diagnosisImage');

    // Ensure dropdown is visible if history exists
    renderHistoryDropdown();
}

// --- HISTORY MANAGEMENT ---
function addToHistory(item) {
    let history = JSON.parse(sessionStorage.getItem('diagnosisHistory') || '[]');

    // Avoid duplicates (simple check based on timestamp or image hash if needed, but simple append is okay for now)
    history.push(item);
    sessionStorage.setItem('diagnosisHistory', JSON.stringify(history));

    renderHistoryDropdown();
}

function renderHistoryDropdown() {
    const history = JSON.parse(sessionStorage.getItem('diagnosisHistory') || '[]');
    const dropdown = document.getElementById('history-dropdown');
    const container = document.getElementById('history-container');

    if (history.length > 0) {
        container.style.display = 'block';

        // Clear existing options (except the first one)
        dropdown.innerHTML = '<option value="" disabled selected>📜 View Previous Reports</option>';

        // Add options in reverse order (newest first)
        history.slice().reverse().forEach((item, index) => {
            const originalIndex = history.length - 1 - index;
            const option = document.createElement('option');
            option.value = originalIndex;
            option.textContent = `${item.timestamp} - ${item.result.name}`;
            dropdown.appendChild(option);
        });
    } else {
        container.style.display = 'none';
    }
}

function loadFromHistory(index) {
    const history = JSON.parse(sessionStorage.getItem('diagnosisHistory') || '[]');
    const item = history[index];

    if (item) {
        // Restore Image
        previewImg.src = item.image;
        previewArea.style.display = 'block';

        // Populate Result
        showResults(item.result, false); // Pass false to avoid re-saving to history
    }
}

// --- PDF DOWNLOAD ---
// --- PDF DOWNLOAD ---
function downloadPDF() {
    // 1. Target the content
    const element = document.querySelector('.results-area');
    const diseaseName = document.getElementById('disease-name').textContent.trim();
    const safeName = diseaseName.replace(/[^a-z0-9]/gi, '_');

    // 2. Clone the element deeply
    const clone = element.cloneNode(true);

    // 3. Create a dedicated container for PDF generation
    //    We place this "on screen" but invisible to the user so browser renders pixels.
    const container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '794px';  // Exact A4 width in pixels (approx)
    container.style.zIndex = '-9999'; // Behind everything
    container.style.opacity = '0';    // Invisible
    container.style.pointerEvents = 'none';
    container.style.background = '#ffffff';

    // 4. Style the Clone for Print
    clone.style.width = '100%';
    clone.style.margin = '0';
    clone.style.padding = '20px';
    clone.style.boxSizing = 'border-box'; // Ensure padding doesn't overflow width
    clone.style.boxShadow = 'none';

    // Fix Typography / Colors
    clone.style.fontFamily = 'Arial, sans-serif';
    clone.style.color = '#000000';

    // Remove unwanted Buttons
    const buttons = clone.querySelector('.btn-analyze').parentElement;
    if (buttons) buttons.remove();

    // Fix header margins
    if (clone.firstElementChild) {
        clone.firstElementChild.style.marginTop = '0';
    }

    // Add Branding Header
    const header = document.createElement('div');
    header.innerHTML = `<h2 style="color:#2e7d32; border-bottom: 2px solid #2e7d32; padding-bottom:10px; margin-top: 0;">Krishi Vaidya Diagnosis Report</h2>`;
    clone.insertBefore(header, clone.firstChild);

    // 5. Assemble and Append
    container.appendChild(clone);
    document.body.appendChild(container);

    // 6. Configure html2pdf
    //    We set windowWidth to force the canvas to capture a desktop layout
    const opt = {
        margin: [0, 0, 0, 0], // We handle margins in CSS padding
        filename: `${safeName}_Report.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
            scale: 2,
            useCORS: true,
            scrollY: 0,
            width: 794,      // Match container
            windowWidth: 794 // Match container
        },
        jsPDF: { unit: 'px', format: [794, 1123], orientation: 'portrait' } // Match pixels roughly (A4 @ 96dpi)
    };

    // 7. Generate
    //    Small timeout to allow DOM to settle / images to load if needed
    setTimeout(() => {
        html2pdf()
            .set(opt)
            .from(clone)
            .save()
            .then(() => {
                // Cleanup
                document.body.removeChild(container);
            })
            .catch(err => {
                console.error("PDF Error:", err);
                alert("Error generating PDF. Please try again.");
                if (document.body.contains(container)) {
                    document.body.removeChild(container);
                }
            });
    }, 500); // Increased delay slightly for safety
}


// --- RESTORE SESSION ---
function loadSession() {
    const savedResult = sessionStorage.getItem('diagnosisResult');
    const savedImage = sessionStorage.getItem('diagnosisImage');

    renderHistoryDropdown(); // Always render dropdown if history exists

    if (savedResult && savedImage) {
        previewImg.src = savedImage;
        previewArea.style.display = 'block';
        showResults(JSON.parse(savedResult), false); // Don't duplicate history on reload
    }
}

// Initialize Session Check
loadSession();
// End of script
