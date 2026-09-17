document.addEventListener("DOMContentLoaded", () => {
    const simSelect = document.getElementById("sim-date-select");
    const container = document.getElementById("briefing-container");
    const queryInput = document.getElementById("query-input");
    const queryBtn = document.getElementById("query-btn");
    const chatMessages = document.getElementById("chat-messages");

    // Load Left Column Dashboard
    function fetchBriefing() {
        const simDate = simSelect.value;
        container.innerHTML = '<div class="loading">Loading executive briefing...</div>';

        fetch(`/api/briefing?sim_date=${encodeURIComponent(simDate)}`)
            .then(res => res.json())
            .then(data => renderBriefing(data))
            .catch(err => {
                container.innerHTML = `<div class="error">Error loading briefing: ${err}</div>`;
            });
    }

    function renderBriefing(briefing) {
        container.innerHTML = "";
        if (!briefing.sections || briefing.sections.length === 0) {
            container.innerHTML = "<p>No active commitments found for this date.</p>";
            return;
        }

        briefing.sections.forEach(sec => {
            const secEl = document.createElement("section");
            secEl.className = "briefing-section";
            secEl.innerHTML = `<h2>${sec.heading}</h2>`;

            sec.items.forEach(item => {
                const card = document.createElement("div");
                card.className = "commitment-card";
                card.innerHTML = `
                    <div class="card-header">
                        <span class="task-title">${item.task_label}</span>
                        <span class="status-badge badge-${item.status}">${item.status.replace('_', ' ')}</span>
                    </div>
                    <div class="card-meta">
                        Owner: <strong>${item.owner}</strong> | Counterparty: ${item.counterparty || 'N/A'}
                        ${item.current_deadline ? ` | Deadline: <strong>${new Date(item.current_deadline).toLocaleString([], {weekday:'short', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</strong>` : ''}
                    </div>
                    <div class="card-reason">${item.status_reason}</div>
                    <div class="card-cite">Ref: ${item.latest_source_ref}</div>
                `;
                secEl.appendChild(card);
            });
            container.appendChild(secEl);
        });
    }

    // --- Chatbot Logic ---
    function appendMessage(sender, text, citations = []) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender}`;
        
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        
        // Render simple markdown bolding for UI
        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        bubble.innerHTML = formattedText;
        msgDiv.appendChild(bubble);

        if (citations && citations.length > 0) {
            const citeDiv = document.createElement("div");
            citeDiv.className = "chat-citations";
            citeDiv.innerText = `Sources: ${citations.join(", ")}`;
            msgDiv.appendChild(citeDiv);
        }

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv; // return element so we can remove typing indicators later
    }

    function showTyping() {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message bot typing-indicator";
        msgDiv.id = "typing-indicator";
        msgDiv.innerText = "Analyzing data...";
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById("typing-indicator");
        if (typing) typing.remove();
    }

    function runQuery() {
        const query = queryInput.value.trim();
        if (!query) return;

        // Add user message
        appendMessage("user", query);
        queryInput.value = "";
        
        // Show typing
        showTyping();

        fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, sim_date: simSelect.value })
        })
        .then(res => res.json())
        .then(data => {
            removeTyping();
            appendMessage("bot", data.answer, data.citations);
        })
        .catch(err => {
            removeTyping();
            appendMessage("bot", "Sorry, I encountered an error checking your data.");
        });
    }

    // Event Listeners
    simSelect.addEventListener("change", () => {
        fetchBriefing();
        // Notify chat of time jump
        appendMessage("bot", `🕒 *Simulated time jumped to: ${simSelect.options[simSelect.selectedIndex].text}*`);
    });
    
    queryBtn.addEventListener("click", runQuery);
    queryInput.addEventListener("keypress", (e) => { 
        if (e.key === "Enter") {
            e.preventDefault();
            runQuery(); 
        }
    });

    // Initialize Dashboard
    fetchBriefing();
});