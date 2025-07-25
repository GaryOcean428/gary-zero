<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Gemini API Model Explorer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chosen Palette: Warm Neutrals -->
    <!-- Application Structure Plan: The application is designed as an interactive dashboard. A persistent sidebar on the left contains filtering options, allowing users to dynamically query the dataset. The main content area on the right displays the results as a grid of visually distinct "model cards." This structure was chosen to transform the static, dense table into a user-centric tool. It facilitates quick comparison and discovery by enabling users to easily narrow down the extensive list of models based on specific capabilities (e.g., "Image Generation", "Video") or families (e.g., "Gemini 2.5", "Imagen"). A dynamic bar chart at the top provides an immediate visual comparison of a key metric (input token limit) across the filtered models, aiding in decision-making. This interactive, task-oriented design is more intuitive and efficient for a developer trying to select the right model than reading a static table. -->
    <!-- Visualization & Content Choices: 
        - Report Info: Full table of Gemini models. -> Goal: Organize & Compare. -> Viz/Presentation Method: Interactive card grid. -> Interaction: Users can filter the grid by capabilities, model families, or input types. -> Justification: Cards provide better information hierarchy and scannability than a table. Filtering is essential for navigating a large dataset and finding relevant models quickly. -> Library/Method: HTML/CSS (Tailwind) and Vanilla JS.
        - Report Info: Input Token Limits. -> Goal: Compare. -> Viz/Presentation Method: Dynamic Bar Chart. -> Interaction: The chart updates automatically when filters are applied, showing a comparison of the currently visible models. -> Justification: A bar chart offers a much clearer and more immediate comparison of numerical data (like token limits) than scanning numbers in a table. It highlights the vast differences in context window sizes. -> Library/Method: Chart.js (Canvas).
        - Report Info: Model capabilities/features. -> Goal: Inform & Filter. -> Viz/Presentation Method: Filter buttons/tags. -> Interaction: Clicking a button filters the model grid and updates the chart. -> Justification: This provides a clear, interactive way for users to explore the models based on the features they care about most. -> Library/Method: HTML/CSS (Tailwind) and Vanilla JS.
    -->
    <!-- CONFIRMATION: NO SVG graphics used. NO Mermaid JS used. -->
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .chart-container {
            position: relative;
            width: 100%;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
            height: 300px;
            max-height: 40vh;
        }
        @media (min-width: 768px) {
            .chart-container {
                height: 350px;
            }
        }
        .model-card {
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .model-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .filter-btn.active {
            background-color: #4338ca;
            color: #ffffff;
            font-weight: 600;
        }
        .filter-btn {
            transition: background-color 0.2s ease, color 0.2s ease;
        }
    </style>
</head>
<body class="bg-stone-50 text-stone-800">

    <div id="app" class="flex flex-col min-h-screen">
        <header class="bg-white/80 backdrop-blur-lg border-b border-stone-200 sticky top-0 z-20">
            <div class="container mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center justify-between h-16">
                    <h1 class="text-2xl font-bold text-indigo-700">Gemini API Model Explorer</h1>
                    <p class="text-sm text-stone-500 hidden md:block">An interactive guide to Google's AI models</p>
                </div>
            </div>
        </header>

        <div class="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
                
                <aside class="lg:col-span-1 lg:sticky lg:top-24 self-start">
                    <div class="bg-white p-6 rounded-xl border border-stone-200 shadow-sm">
                        <h2 class="text-lg font-semibold mb-4 border-b pb-2">Filter Models</h2>
                        <div id="filters">
                            <h3 class="font-semibold text-md mb-2 mt-4">By Capability</h3>
                            <div id="capability-filters" class="flex flex-wrap gap-2"></div>
                            
                            <h3 class="font-semibold text-md mb-2 mt-6">By Model Family</h3>
                            <div id="family-filters" class="flex flex-wrap gap-2"></div>

                            <h3 class="font-semibold text-md mb-2 mt-6">By Input Type</h3>
                            <div id="input-filters" class="flex flex-wrap gap-2"></div>

                            <button id="reset-filters" class="w-full mt-6 bg-stone-200 hover:bg-stone-300 text-stone-700 font-semibold py-2 px-4 rounded-lg transition-colors">Reset Filters</button>
                        </div>
                    </div>
                </aside>

                <main class="lg:col-span-3">
                    <section id="chart-section" class="mb-8 bg-white p-6 rounded-xl border border-stone-200 shadow-sm">
                        <h2 class="text-xl font-semibold mb-1">Input Token Limit Comparison</h2>
                        <p class="text-stone-600 mb-4 text-sm">This chart visualizes the maximum number of input tokens for each model, representing its context window size. Models with higher limits can process larger amounts of information at once. Use the filters to compare specific models. A token is roughly 4 characters.</p>
                        <div class="chart-container">
                            <canvas id="tokenChart"></canvas>
                        </div>
                    </section>
                    
                    <section id="models-section">
                         <div class="flex justify-between items-center mb-4">
                            <h2 class="text-xl font-semibold">Available Models</h2>
                            <p id="model-count" class="text-stone-600 font-medium"></p>
                        </div>
                        <div id="model-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        </div>
                         <div id="no-results" class="hidden text-center py-12">
                            <p class="text-xl font-semibold text-stone-700">No models match your criteria.</p>
                            <p class="text-stone-500 mt-2">Try adjusting or resetting your filters.</p>
                        </div>
                    </section>
                </main>

            </div>
        </div>

        <footer class="bg-white mt-12 py-6 border-t border-stone-200">
            <div class="container mx-auto px-4 sm:px-6 lg:px-8 text-center text-stone-500 text-sm">
                <p>Data sourced from the Google Gemini API documentation. This is a visual aid for exploration.</p>
                <p>&copy; 2025 Interactive Model Explorer. All rights reserved.</p>
            </div>
        </footer>
    </div>

    <script>
        const modelData = [
            { name: "Gemini 2.5 Pro", code: "gemini-2.5-pro", updated: "June 2025", description: "State-of-the-art model for complex reasoning in code, math, and STEM, and analysis of large datasets.", inputs: ["Audio", "Images", "Video", "Text", "PDF"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 65536, features: ["Structured outputs", "Caching", "Function calling", "Code execution", "Search grounding", "Image Generation", "Audio Generation", "Live API", "Thinking"], family: "Gemini 2.5" },
            { name: "Gemini 2.5 Flash", code: "models/gemini-2.5-flash", updated: "June 2025", description: "Best price-performance model for large-scale, low-latency, and high-volume tasks.", inputs: ["Text", "Images", "Video", "Audio"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 65536, features: ["Audio Generation", "Caching", "Code execution", "Function calling", "Image Generation", "Search grounding", "Structured outputs", "Thinking", "Batch Mode"], family: "Gemini 2.5" },
            { name: "Gemini 2.5 Flash-Lite", code: "models/gemini-2.5-flash-lite", updated: "July 2025", description: "A cost-efficient and high-throughput version of Gemini 2.5 Flash.", inputs: ["Text", "Images", "Video", "Audio", "PDF"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 65536, features: ["Structured outputs", "Caching", "Function calling", "Code execution", "URL Context", "Search grounding", "Image Generation", "Audio Generation", "Live API"], family: "Gemini 2.5" },
            { name: "Gemini 2.5 Flash Native Audio", code: "models/gemini-2.5-flash-preview-native-audio-dialog", updated: "May 2025", description: "Native audio dialog model for interactive and unstructured conversational experiences.", inputs: ["Audio", "Video", "Text"], outputs: ["Audio", "Text"], inputTokens: 128000, outputTokens: 8000, features: ["Audio Generation", "Caching", "Code execution", "Function calling", "Image Generation", "Search grounding", "Structured outputs", "Thinking", "Tuning"], family: "Gemini 2.5" },
            { name: "Gemini 2.5 Flash Preview TTS", code: "models/gemini-2.5-flash-preview-tts", updated: "May 2025", description: "Price-performant text-to-speech model for structured workflows like podcasts and audiobooks.", inputs: ["Text"], outputs: ["Audio"], inputTokens: 8000, outputTokens: 16000, features: ["Text-to-Speech", "Structured outputs", "Caching", "Tuning", "Function calling", "Code execution", "Search", "Audio Generation", "Live API", "Thinking"], family: "Gemini 2.5" },
            { name: "Gemini 2.5 Pro Preview TTS", code: "models/gemini-2.5-pro-preview-tts", updated: "May 2025", description: "Most powerful text-to-speech model for high-control structured audio generation.", inputs: ["Text"], outputs: ["Audio"], inputTokens: 8000, outputTokens: 16000, features: ["Text-to-Speech", "Structured outputs", "Caching", "Tuning", "Function calling", "Code execution", "Search", "Audio Generation", "Live API", "Thinking"], family: "Gemini 2.5" },
            { name: "Gemini 2.0 Flash", code: "models/gemini-2.0-flash", updated: "Feb 2025", description: "Next-gen features with superior speed, native tool use, and a 1M token context window.", inputs: ["Audio", "Images", "Video", "Text"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 8192, features: ["Structured outputs", "Caching", "Tuning", "Function calling", "Code execution", "Search", "Image Generation", "Audio Generation", "Live API"], family: "Gemini 2.0" },
            { name: "Gemini 2.0 Flash Preview Image Generation", code: "models/gemini-2.0-flash-preview-image-generation", updated: "May 2025", description: "Improved image generation and conversational image editing.", inputs: ["Audio", "Images", "Video", "Text"], outputs: ["Text", "Images"], inputTokens: 32000, outputTokens: 8192, features: ["Image Generation", "Structured outputs", "Caching", "Tuning", "Function calling", "Code execution", "Search", "Audio Generation", "Live API"], family: "Gemini 2.0" },
            { name: "Gemini 2.0 Flash-Lite", code: "models/gemini-2.0-flash-lite", updated: "Feb 2025", description: "A cost-efficient and low-latency version of Gemini 2.0 Flash.", inputs: ["Audio", "Images", "Video", "Text"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 8192, features: ["Structured outputs", "Caching", "Tuning", "Function calling", "Code execution", "Search", "Image Generation", "Audio Generation", "Live API"], family: "Gemini 2.0" },
            { name: "Gemini 1.5 Pro", code: "models/gemini-1.5-pro", updated: "Sep 2025", description: "Most advanced Gemini model with a large context window for complex tasks.", inputs: ["Audio", "Images", "Video", "Text"], outputs: ["Text"], inputTokens: 2097152, outputTokens: 8192, features: ["System instructions", "JSON mode", "JSON schema", "Adjustable safety settings", "Caching", "Tuning"], family: "Gemini 1.5" },
            { name: "Gemini 1.5 Flash", code: "models/gemini-1.5-flash", updated: "Sep 2025", description: "Fast and versatile multimodal model for scaling across diverse tasks.", inputs: ["Audio", "Images", "Video", "Text"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 8192, features: ["System instructions", "JSON mode", "JSON schema", "Adjustable safety settings", "Caching", "Tuning"], family: "Gemini 1.5" },
            { name: "Gemini 1.5 Flash-8B", code: "models/gemini-1.5-flash-8b", updated: "Sep 2025", description: "A small model designed for lower intelligence tasks.", inputs: ["Audio", "Images", "Video", "Text"], outputs: ["Text"], inputTokens: 1048576, outputTokens: 8192, features: ["System instructions", "JSON mode", "JSON schema", "Adjustable safety settings", "Caching", "Tuning"], family: "Gemini 1.5" },
            { name: "Imagen 4", code: "imagen-4.0-generate-preview-06-06", updated: "June 2025", description: "Latest image model for highly detailed images with rich lighting and better text rendering.", inputs: ["Text"], outputs: ["Images"], inputTokens: 480, outputTokens: null, features: ["Image Generation", "High-resolution output"], family: "Imagen" },
            { name: "Imagen 3", code: "imagen-3.0-generate-002", updated: "Feb 2025", description: "High-quality text-to-image model for detailed images with rich lighting.", inputs: ["Text"], outputs: ["Images"], inputTokens: null, outputTokens: null, features: ["Image Generation", "Fewer distracting artifacts"], family: "Imagen" },
            { name: "Veo 3 Preview", code: "veo-3.0-generate-preview", updated: "July 2025", description: "Latest text-to-video model with integrated audio and direct camera controls.", inputs: ["Text"], outputs: ["Video with audio"], inputTokens: 1024, outputTokens: null, features: ["Video Generation", "Enhanced prompt adherence"], family: "Veo" },
            { name: "Veo 2", code: "veo-2.0-generate-001", updated: "April 2025", description: "High-quality text- and image-to-video model for detailed videos.", inputs: ["Text", "Images"], outputs: ["Video"], inputTokens: null, outputTokens: null, features: ["Video Generation", "Captures artistic nuance"], family: "Veo" },
            { name: "Gemini 2.5 Flash Live", code: "models/gemini-live-2.5-flash-preview", updated: "June 2025", description: "Enables low-latency bidirectional voice and video interactions with Gemini.", inputs: ["Audio", "Video", "Text"], outputs: ["Text", "Audio"], inputTokens: 1048576, outputTokens: 8192, features: ["Live API", "Structured outputs", "Tuning", "Function calling", "Code execution", "Search", "Image Generation", "Audio Generation", "Thinking"], family: "Gemini 2.5" },
            { name: "Gemini 2.0 Flash Live", code: "models/gemini-2.0-flash-live-001", updated: "April 2025", description: "Enables low-latency bidirectional voice and video interactions with Gemini.", inputs: ["Audio", "Video", "Text"], outputs: ["Text", "Audio"], inputTokens: 1048576, outputTokens: 8192, features: ["Live API", "Structured outputs", "Tuning", "Function calling", "Code execution", "Search", "Image Generation", "Audio Generation", "Thinking"], family: "Gemini 2.0" },
            { name: "Gemini Embedding", code: "gemini-embedding-001", updated: "June 2025", description: "Measures the relatedness of strings for applications like retrieval.", inputs: ["Text"], outputs: ["Text embeddings"], inputTokens: 2048, outputTokens: null, features: ["Embeddings", "Code", "multi-lingual support"], family: "Embedding" },
            { name: "Text Embedding (Legacy)", code: "models/text-embedding-004", updated: "April 2024", description: "Legacy model for measuring the relatedness of text strings.", inputs: ["Text"], outputs: ["Text embeddings"], inputTokens: 2048, outputTokens: null, features: ["Embeddings", "Adjustable safety settings"], family: "Embedding" },
        ];

        document.addEventListener('DOMContentLoaded', () => {
            const modelGrid = document.getElementById('model-grid');
            const capabilityFiltersContainer = document.getElementById('capability-filters');
            const familyFiltersContainer = document.getElementById('family-filters');
            const inputFiltersContainer = document.getElementById('input-filters');
            const modelCountEl = document.getElementById('model-count');
            const noResultsEl = document.getElementById('no-results');
            const resetBtn = document.getElementById('reset-filters');
            
            let activeCapabilityFilters = [];
            let activeFamilyFilters = [];
            let activeInputFilters = [];

            let tokenChart;

            const createFilterButtons = () => {
                const allCapabilities = [...new Set(modelData.flatMap(m => m.features.filter(f => ["Image Generation", "Video Generation", "Audio Generation", "Text-to-Speech", "Embeddings", "Live API", "Thinking"].includes(f))))].sort();
                const allFamilies = [...new Set(modelData.map(m => m.family))].sort();
                const allInputs = [...new Set(modelData.flatMap(m => m.inputs))].sort();

                capabilityFiltersContainer.innerHTML = allCapabilities.map(cap => `<button class="filter-btn text-sm bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full" data-filter-type="capability" data-filter="${cap}">${cap}</button>`).join('');
                familyFiltersContainer.innerHTML = allFamilies.map(fam => `<button class="filter-btn text-sm bg-teal-100 text-teal-700 px-3 py-1 rounded-full" data-filter-type="family" data-filter="${fam}">${fam}</button>`).join('');
                inputFiltersContainer.innerHTML = allInputs.map(inp => `<button class="filter-btn text-sm bg-amber-100 text-amber-700 px-3 py-1 rounded-full" data-filter-type="input" data-filter="${inp}">${inp}</button>`).join('');
            };

            const renderModels = (models) => {
                modelGrid.innerHTML = models.map(model => `
                    <div class="model-card bg-white p-6 rounded-xl border border-stone-200 flex flex-col h-full">
                        <div class="flex-grow">
                            <h3 class="text-lg font-bold text-indigo-800">${model.name}</h3>
                            <p class="text-xs text-stone-500 mb-3 font-mono">${model.code}</p>
                            <p class="text-sm text-stone-600 mb-4">${model.description}</p>
                            <div class="mb-4">
                               <h4 class="font-semibold text-sm mb-2">Capabilities:</h4>
                               <div class="flex flex-wrap gap-2">
                                   ${model.features.map(f => `<span class="text-xs bg-stone-100 text-stone-700 px-2 py-1 rounded-md">${f}</span>`).join('')}
                               </div>
                            </div>
                        </div>
                        <div class="mt-auto pt-4 border-t border-stone-200 text-sm">
                             <div class="flex justify-between items-center mb-2">
                                <span class="font-semibold text-stone-700">Inputs:</span>
                                <span class="text-right">${model.inputs.join(', ')}</span>
                            </div>
                            <div class="flex justify-between items-center mb-2">
                                <span class="font-semibold text-stone-700">Input Tokens:</span>
                                <span class="font-mono text-indigo-600 font-bold">${model.inputTokens ? model.inputTokens.toLocaleString() : 'N/A'}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="font-semibold text-stone-700">Last Updated:</span>
                                <span class="text-stone-500">${model.updated}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            };

            const filterAndRender = () => {
                const filteredModels = modelData.filter(model => {
                    const capabilityMatch = activeCapabilityFilters.length === 0 || activeCapabilityFilters.every(filter => model.features.includes(filter));
                    const familyMatch = activeFamilyFilters.length === 0 || activeFamilyFilters.includes(model.family);
                    const inputMatch = activeInputFilters.length === 0 || activeInputFilters.every(filter => model.inputs.includes(filter));
                    return capabilityMatch && familyMatch && inputMatch;
                });

                renderModels(filteredModels);
                updateChart(filteredModels);
                modelCountEl.textContent = `${filteredModels.length} of ${modelData.length} models shown`;
                
                if (filteredModels.length === 0) {
                    noResultsEl.classList.remove('hidden');
                    modelGrid.classList.add('hidden');
                } else {
                    noResultsEl.classList.add('hidden');
                    modelGrid.classList.remove('hidden');
                }
            };
            
            const handleFilterClick = (e) => {
                if (!e.target.matches('.filter-btn')) return;

                const filter = e.target.dataset.filter;
                const type = e.target.dataset.filterType;
                e.target.classList.toggle('active');

                let filterArray;
                if (type === 'capability') filterArray = activeCapabilityFilters;
                else if (type === 'family') filterArray = activeFamilyFilters;
                else if (type === 'input') filterArray = activeInputFilters;

                const index = filterArray.indexOf(filter);
                if (index > -1) {
                    filterArray.splice(index, 1);
                } else {
                    filterArray.push(filter);
                }
                
                filterAndRender();
            };

            const resetFilters = () => {
                activeCapabilityFilters = [];
                activeFamilyFilters = [];
                activeInputFilters = [];
                document.querySelectorAll('.filter-btn.active').forEach(btn => btn.classList.remove('active'));
                filterAndRender();
            };

            const updateChart = (models) => {
                const chartData = models.filter(m => m.inputTokens && m.inputTokens > 0).sort((a, b) => b.inputTokens - a.inputTokens);
                
                tokenChart.data.labels = chartData.map(m => m.name);
                tokenChart.data.datasets[0].data = chartData.map(m => m.inputTokens);
                tokenChart.update();
            };

            const initializeChart = () => {
                const ctx = document.getElementById('tokenChart').getContext('2d');
                tokenChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Max Input Tokens',
                            data: [],
                            backgroundColor: 'rgba(79, 70, 229, 0.6)',
                            borderColor: 'rgba(79, 70, 229, 1)',
                            borderWidth: 1,
                            hoverBackgroundColor: 'rgba(79, 70, 229, 0.8)',
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                beginAtZero: true,
                                type: 'logarithmic',
                                ticks: {
                                    callback: function(value, index, values) {
                                        return Number(value.toString()).toLocaleString();
                                    }
                                }
                            },
                            y: {
                                ticks: {
                                    autoSkip: false,
                                    font: {
                                        size: 10
                                    }
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.x !== null) {
                                            label += context.parsed.x.toLocaleString();
                                        }
                                        return label;
                                    }
                                }
                            }
                        }
                    }
                });
            };

            createFilterButtons();
            initializeChart();
            filterAndRender();
            
            document.getElementById('filters').addEventListener('click', handleFilterClick);
            resetBtn.addEventListener('click', resetFilters);
        });
    </script>
</body>
</html>
