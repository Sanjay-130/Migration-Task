

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileNameDisplay = document.getElementById('file-name-display');
    const fileSizeDisplay = document.getElementById('file-size-display');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    const uploadSection = document.getElementById('upload-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    
    const resultFilename = document.getElementById('result-filename');
    const resultSummary = document.getElementById('result-summary');
    const analysisMethod = document.getElementById('analysis-method');
    const overallScore = document.getElementById('overall-score');
    const scoreCircle = document.getElementById('score-circle');
    
    const migrationBadge = document.getElementById('migration-badge');
    const badgeIcon = document.getElementById('badge-icon');
    const migrationStatus = document.getElementById('migration-status');
    const migrationExplanation = document.getElementById('migration-explanation');
    
    const metricPages = document.getElementById('metric-pages');
    const metricWords = document.getElementById('metric-words');
    const metricParagraphs = document.getElementById('metric-paragraphs');
    const metricHeadings = document.getElementById('metric-headings');
    const metricAvgWords = document.getElementById('metric-avg-words');
    const metricReadingTime = document.getElementById('metric-reading-time');
    const metricChars = document.getElementById('metric-chars');
    const metricUniqueRatio = document.getElementById('metric-unique-ratio');
    
    const flagTables = document.getElementById('flag-tables');
    const flagImages = document.getElementById('flag-images');
    
    const aiReadability = document.getElementById('ai-readability');
    const aiReadabilityExp = document.getElementById('ai-readability-exp');
    const aiClarityScore = document.getElementById('ai-clarity-score');
    const aiClarityBar = document.getElementById('ai-clarity-bar');
    const aiClarityExp = document.getElementById('ai-clarity-exp');
    const aiStructural = document.getElementById('ai-structural');
    const aiStructuralExp = document.getElementById('ai-structural-exp');
    
    const aiTone = document.getElementById('ai-tone');
    const aiToneBar = document.getElementById('ai-tone-bar');
    const aiToneScore = document.getElementById('ai-tone-score');
    const aiToneExp = document.getElementById('ai-tone-exp');
    
    const suggestionsList = document.getElementById('suggestions-list');
    const headingsSection = document.getElementById('headings-section');
    const headingsList = document.getElementById('headings-list');
    const outlineAuditSummary = document.getElementById('outline-audit-summary');
    
    const downloadJsonBtn = document.getElementById('download-json');
    const newAnalysisBtn = document.getElementById('new-analysis');
    
    // Markdown Exporter Elements
    const markdownPreview = document.getElementById('markdown-preview');
    const copyMarkdownBtn = document.getElementById('copy-markdown-btn');
    
    let selectedFile = null;
    let analysisResultData = null; 

    
    // Trigger file dialog on clicking drop zone
    dropZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag-over styling
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    // Handle dropped file
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    function handleFileSelection(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'docx' && ext !== 'pdf') {
            alert('Unsupported file format! Please upload a .docx or .pdf file.');
            return;
        }
        
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        fileSizeDisplay.textContent = `(${formatBytes(file.size)})`;
        
        dropZone.classList.add('hidden');
        fileInfo.classList.remove('hidden');
        analyzeBtn.classList.remove('hidden');
    }

    // Reset file selection
    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUploadForm();
    });

    function resetUploadForm() {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        analyzeBtn.classList.add('hidden');
        dropZone.classList.remove('hidden');
    }

    // --- API SERVER ACTION ---

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Transition: Upload -> Loading
        uploadSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            // Call our FastAPI backend endpoint /analyze
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze document');
            }

            const data = await response.json();
            analysisResultData = data;
            
            // Render result report details
            renderResults(data);
            
            // Transition: Loading -> Results
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');

        } catch (error) {
            console.error(error);
            alert(`Error during document processing: ${error.message}`);
            // Return back to upload form
            loadingSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
    });

    // Start a new document analysis
    newAnalysisBtn.addEventListener('click', () => {
        resetUploadForm();
        resultsSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
    });

    // Download analysis JSON report file
    downloadJsonBtn.addEventListener('click', () => {
        if (!analysisResultData) return;
        
        const jsonString = JSON.stringify(analysisResultData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${analysisResultData.document_metrics.file_name}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Copy Markdown to Clipboard
    copyMarkdownBtn.addEventListener('click', () => {
        if (!markdownPreview.value) return;
        
        markdownPreview.select();
        navigator.clipboard.writeText(markdownPreview.value).then(() => {
            const originalText = copyMarkdownBtn.textContent;
            copyMarkdownBtn.textContent = 'Copied!';
            copyMarkdownBtn.style.backgroundColor = '#dcfce7';
            copyMarkdownBtn.style.color = '#166534';
            copyMarkdownBtn.style.borderColor = '#166534';
            
            setTimeout(() => {
                copyMarkdownBtn.textContent = originalText;
                copyMarkdownBtn.style.backgroundColor = '';
                copyMarkdownBtn.style.color = '';
                copyMarkdownBtn.style.borderColor = '';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy: ', err);
            alert('Could not copy text to clipboard. Please copy manually.');
        });
    });

    // Technical Tone - Click to locate passive sentences in Markdown Preview
    aiToneExp.addEventListener('click', (e) => {
        const passiveItem = e.target.closest('.passive-item');
        if (passiveItem) {
            const passiveTextEl = passiveItem.querySelector('.passive-text');
            if (passiveTextEl) {
                let sentence = passiveTextEl.textContent.trim();
                if (sentence.startsWith('"') && sentence.endsWith('"')) {
                    sentence = sentence.slice(1, -1);
                }
                highlightSentenceInPreview(sentence);
            }
        }
    });

    // Document Outline - Click to locate headings in Markdown Preview
    headingsList.addEventListener('click', (e) => {
        const node = e.target.closest('.tree-node');
        if (node) {
            const textEl = node.querySelector('.heading-text');
            if (textEl) {
                const headingText = textEl.textContent.trim();
                highlightHeadingInPreview(headingText);
            }
        }
    });

    function highlightHeadingInPreview(headingText) {
        if (!markdownPreview || !markdownPreview.value) return;
        
        const text = markdownPreview.value;
        const lines = text.split('\n');
        let index = -1;
        let matchedLine = '';
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('#') && line.toLowerCase().includes(headingText.toLowerCase())) {
                matchedLine = lines[i];
                index = text.indexOf(matchedLine);
                break;
            }
        }
        
        if (index === -1) {
            index = text.toLowerCase().indexOf(headingText.toLowerCase());
            matchedLine = headingText;
        }
        
        if (index !== -1) {
            markdownPreview.focus();
            markdownPreview.setSelectionRange(index, index + matchedLine.length);
            
            const tempText = text.substring(0, index);
            const lineCount = tempText.split('\n').length;
            const lineHeight = 20; 
            markdownPreview.scrollTop = (lineCount - 4) * lineHeight;
            
            markdownPreview.style.outline = '3px solid #3b82f6';
            markdownPreview.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.4)';
            setTimeout(() => {
                markdownPreview.style.outline = '';
                markdownPreview.style.boxShadow = '';
            }, 1500);
            
            markdownPreview.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function highlightSentenceInPreview(sentence) {
        if (!markdownPreview || !markdownPreview.value) return;
        
        const cleanQuery = sentence.replace(/\.\.\./g, '').trim();
        if (cleanQuery.length < 5) return;
        
        const text = markdownPreview.value;
        const index = text.toLowerCase().indexOf(cleanQuery.toLowerCase());
        
        if (index !== -1) {
            markdownPreview.focus();
            markdownPreview.setSelectionRange(index, index + cleanQuery.length);
            
            const tempText = text.substring(0, index);
            const lines = tempText.split('\n').length;
            const lineHeight = 20; 
            markdownPreview.scrollTop = (lines - 4) * lineHeight;
            
            markdownPreview.style.outline = '3px solid #f59e0b';
            markdownPreview.style.boxShadow = '0 0 10px rgba(245, 158, 11, 0.4)';
            setTimeout(() => {
                markdownPreview.style.outline = '';
                markdownPreview.style.boxShadow = '';
            }, 1500);
            
            markdownPreview.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // --- RENDER CARD & DATA ENGINE ---

    function renderResults(data) {
        const metrics = data.document_metrics;
        const ai = data.ai_analysis;

        // Header info
        resultFilename.textContent = metrics.file_name;
        resultSummary.textContent = data.summary;
        analysisMethod.textContent = `Analysis Method: ${data.analysis_method}`;
        
        // Animated Score Radial Display
        overallScore.textContent = ai.overall_score;
        updateScoreRing(ai.overall_score);

        // Migration Readiness Badge
        renderMigrationBadge(ai.migration_readiness, ai.migration_readiness_explanation);

        // Number Metrics Cards
        metricPages.textContent = metrics.total_pages;
        metricWords.textContent = formatNumber(metrics.word_count);
        metricParagraphs.textContent = formatNumber(metrics.paragraph_count);
        metricHeadings.textContent = formatNumber(metrics.heading_count);
        metricAvgWords.textContent = metrics.avg_words_per_paragraph;
        metricReadingTime.textContent = metrics.estimated_reading_time_min;
        metricChars.textContent = formatNumber(metrics.character_count);
        metricUniqueRatio.textContent = metrics.unique_word_ratio;

        // Table and Image indicators
        toggleFeatureFlag(flagTables, metrics.has_tables);
        toggleFeatureFlag(flagImages, metrics.has_images);

        // AI Cards Configuration
        renderAICards(ai);

        // Bullet Points
        renderSuggestions(ai.suggestions);

        // Headings Structure
        renderHeadingsList(metrics.heading_list);

        // Markdown Exporter Content
        if (markdownPreview) {
            markdownPreview.value = data.markdown_content || "";
        }
    }

    function updateScoreRing(score) {
        if (!scoreCircle) return;
        // Circumference is 2 * PI * r = 2 * 3.14159 * 52 = 326.72
        const circumference = 326.7;
        const offset = circumference - (score / 10) * circumference;
        
        // Simple delay to let the UI finish rendering before animating
        setTimeout(() => {
            scoreCircle.style.strokeDashoffset = offset;
        }, 100);
    }

    function renderMigrationBadge(status, explanation) {
        // Reset classes
        migrationBadge.className = 'migration-badge glass-card';
        
        if (status.includes('Ready') || status.includes('Clean')) {
            migrationBadge.classList.add('state-ready');
            badgeIcon.textContent = '✓';
            migrationStatus.textContent = 'Clean / Reusable';
        } else if (status.includes('Review')) {
            migrationBadge.classList.add('state-review');
            badgeIcon.textContent = '!';
            migrationStatus.textContent = 'Needs Review';
        } else {
            migrationBadge.classList.add('state-restructure');
            badgeIcon.textContent = '✕';
            migrationStatus.textContent = 'Requires Restructuring';
        }
        
        migrationExplanation.textContent = explanation;
    }

    function toggleFeatureFlag(element, isActive) {
        if (isActive) {
            element.classList.add('active');
        } else {
            element.classList.remove('active');
        }
    }

    function renderAICards(ai) {
        // Readability card
        aiReadability.textContent = ai.readability_level;
        aiReadability.className = 'ai-badge ' + ai.readability_level.toLowerCase();
        aiReadabilityExp.textContent = ai.readability_explanation;

        // Clarity card
        aiClarityScore.textContent = `${ai.content_clarity_score}/10`;
        aiClarityBar.style.width = `${ai.content_clarity_score * 10}%`;
        aiClarityExp.textContent = ai.content_clarity_explanation;

        // Structure quality card
        aiStructural.textContent = ai.structural_quality;
        aiStructural.className = 'ai-badge ' + ai.structural_quality.toLowerCase().replace(' ', '-');
        aiStructuralExp.textContent = ai.structural_quality_explanation;

        // Technical Tone card
        aiTone.textContent = ai.tone_assessment_label.split(' ')[0]; // Show short word "Excellent", "Good", or "Review"
        
        // Tone color mapping
        aiTone.className = 'ai-badge';
        if (ai.tone_assessment_label.includes('Excellent')) {
            aiTone.classList.add('easy');
        } else if (ai.tone_assessment_label.includes('Good')) {
            aiTone.classList.add('medium');
        } else {
            aiTone.classList.add('complex');
        }
        
        aiToneBar.style.width = `${ai.tone_active_voice_pct}%`;
        aiToneScore.textContent = `${ai.tone_active_voice_pct}% Active`;
        let toneExpHTML = "Technical guidelines should prefer active voice for direct user instructions.";
        if (ai.tone_passive_sentences && ai.tone_passive_sentences.length > 0) {
            toneExpHTML += "<br><br><strong>Passive structures found:</strong><div class='passive-list'>";
            ai.tone_passive_sentences.forEach(s => {
                const locationRegex = /\s*\[(Page \d+, Line \d+|Line \d+)\]/;
                const match = s.match(locationRegex);
                let cleanSentence = s;
                let locBadge = "";
                
                if (match) {
                    cleanSentence = s.replace(locationRegex, '').trim();
                    locBadge = `<span class="location-tag" style="font-size: 0.65rem; padding: 0.05rem 0.3rem; margin-right: 0;">${match[1]}</span>`;
                } else {
                    locBadge = `<span class="location-tag" style="font-size: 0.65rem; padding: 0.05rem 0.3rem; margin-right: 0; background-color: #e2e8f0; color: #475569; border-color: #cbd5e1;">Global</span>`;
                }
                
                toneExpHTML += `
                    <div class="passive-item" title="Click to highlight this sentence in the Markdown Preview below">
                        <div class="passive-item-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%; pointer-events: none;">
                            ${locBadge}
                            <span style="font-size: 0.65rem; font-weight: 800; color: #b45309; text-transform: uppercase;">⚠️ Convert to Active Voice</span>
                        </div>
                        <div class="passive-text" style="font-size: 0.85rem; color: #78350f; margin-top: 0.4rem; padding: 0.5rem; background: #fffbeb; border: 1px solid #fcd34d; border-radius: 4px;">"${cleanSentence}"</div>
                    </div>`;
            });
            toneExpHTML += "</div>";
        }
        aiToneExp.innerHTML = toneExpHTML;
    }

    function renderSuggestions(suggestions) {
        suggestionsList.innerHTML = '';
        if (suggestions.length === 0) {
            const li = document.createElement('li');
            li.textContent = "Document appears to be in good shape for migration";
            suggestionsList.appendChild(li);
            return;
        }
        
        suggestions.forEach(item => {
            const li = document.createElement('li');
            

            // Try to extract location tag: [Page X] or similar
            const locationRegex = /\s*\[(Page \d+(?:,\s*Line \d+)?|Line \d+|Page \d+)\]/;
            const match = item.match(locationRegex);
            
            if (match) {
                const cleanText = item.replace(locationRegex, '').trim();
                let locationStr = match[1];
                
                // Keep only the Page number
                if (locationStr.includes(',')) {
                    locationStr = locationStr.split(',')[0].trim();
                } else if (locationStr.startsWith('Line')) {
                    locationStr = '';
                }
                
                if (locationStr) {
                    const tag = document.createElement('span');
                    tag.className = 'location-tag';
                    tag.textContent = locationStr;
                    li.appendChild(tag);
                }
                
                const textSpan = document.createElement('span');
                textSpan.textContent = cleanText;
                li.appendChild(textSpan);
            } else {
                li.textContent = item;
            }
            suggestionsList.appendChild(li);
        });
    }

    function renderHeadingsList(headings) {
        if (!headings || headings.length === 0) {
            headingsSection.classList.add('hidden');
            return;
        }

        headingsSection.classList.remove('hidden');
        headingsList.innerHTML = '';
        
        let warningsCount = 0;
        let maxDepth = 1;
        let lastLevel = null;
        const seenTexts = new Set();
        
        // Array of processed heading nodes
        const nodes = headings.map((hStr, idx) => {
            // Expected format: "H{level}: {text}"
            let level = 2;
            let text = hStr;
            
            if (hStr.startsWith('H') && hStr.includes(':')) {
                const parts = hStr.split(':');
                level = parseInt(parts[0].replace('H', ''), 10) || 2;
                text = parts.slice(1).join(':').trim();
            }
            
            if (level > maxDepth) maxDepth = level;
            
            // Warnings array for this node
            const nodeWarnings = [];
            
            // Warning 1: First heading is not H1
            if (idx === 0 && level !== 1) {
                nodeWarnings.push({
                    type: 'no-h1-start',
                    msg: 'Outline starts below level 1 (Best practice: start with H1 title)'
                });
            }
            
            // Warning 2: Level jumps (e.g. H1 followed immediately by H3)
            if (lastLevel !== null && level - lastLevel > 1) {
                nodeWarnings.push({
                    type: 'level-jump',
                    msg: `Hierarchy jump detected: H${lastLevel} directly to H${level}`
                });
            }
            
            // Warning 3: Heading too long (> 60 chars)
            if (text.length > 60) {
                nodeWarnings.push({
                    type: 'too-long',
                    msg: `Heading text exceeds 60 characters (Length: ${text.length} chars)`
                });
            }
            
            // Warning 4: Duplicate heading text
            const lowerText = text.toLowerCase();
            if (seenTexts.has(lowerText)) {
                nodeWarnings.push({
                    type: 'duplicate',
                    msg: `Duplicate heading found: "${text}"`
                });
            } else {
                seenTexts.add(lowerText);
            }
            
            lastLevel = level;
            warningsCount += nodeWarnings.length;
            
            return {
                level,
                text,
                warnings: nodeWarnings
            };
        });
        
        // Render outline tree nodes
        nodes.forEach(node => {
            const itemDiv = document.createElement('div');
            itemDiv.className = `tree-node level-${node.level}`;
            itemDiv.title = "Click to locate this heading in the Markdown Preview below";
            // Level badge
            const badge = document.createElement('span');
            badge.className = 'heading-badge';
            badge.textContent = `H${node.level}`;
            itemDiv.appendChild(badge);
            
            // Heading text
            const textSpan = document.createElement('span');
            textSpan.className = 'heading-text';
            textSpan.textContent = node.text;
            itemDiv.appendChild(textSpan);
            
            // Warnings label
            if (node.warnings.length > 0) {
                const warningSpan = document.createElement('span');
                warningSpan.className = 'heading-audit-badge';
                warningSpan.innerHTML = `⚠️ ${node.warnings[0].msg.split(': ')[1] || node.warnings[0].msg}`;
                warningSpan.title = node.warnings.map(w => w.msg).join('\n');
                itemDiv.appendChild(warningSpan);
            }
            
            headingsList.appendChild(itemDiv);
        });
        
        // Render audit summary banner
        outlineAuditSummary.innerHTML = '';
        
        const summaryStatus = warningsCount === 0 
            ? '<span class="audit-status perfect">✓ Structure Validated</span>'
            : `<span class="audit-status warn">⚠️ ${warningsCount} outline warning${warningsCount > 1 ? 's' : ''}</span>`;
            
        outlineAuditSummary.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <div>
                    <strong>Max Depth:</strong> H${maxDepth}
                    <span style="margin: 0 0.5rem; color: #cbd5e1;">|</span>
                    <strong>Total Headings:</strong> ${nodes.length}
                </div>
                <div>
                    ${summaryStatus}
                </div>
            </div>
        `;
    }

    // --- HELPER UTILITIES ---
    
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
});
