document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("chat-form");
    const question = document.getElementById("question");
    const chatHistory = document.getElementById("chat-history");

    question.addEventListener("input", () => {
        question.style.height = "auto";
        question.style.height = question.scrollHeight + "px";
    });

    question.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    form.addEventListener("submit", async (event) => {

        event.preventDefault();

        const userQuestion = question.value.trim();

        if (!userQuestion) return;

        const currentTime = new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        });

        const formData = new FormData();
        formData.append("question", userQuestion);

        if (chatHistory.style.display === "none") {
            chatHistory.style.display = "block";

            const welcome = document.getElementById("welcome-screen");

            if (welcome)
                welcome.style.display = "none";
        }

        chatHistory.insertAdjacentHTML("beforeend", `
            <div class="user-message">
                <h3>👤 You</h3>
                <div class="user-bubble">${userQuestion}</div>
                <div class="message-time">${currentTime}</div>
            </div>
        `);

        chatHistory.scrollTop = chatHistory.scrollHeight;

        question.value = "";
        question.style.height = "60px";

        const loadingId = "loading-" + Date.now();

        chatHistory.insertAdjacentHTML("beforeend", `
            <div class="ai-loading" id="${loadingId}">
                <div class="Chemai-chat-header">
                    <img id="loading-avatar"
                         src="/static/images/mascot/thinking/chemai_thinking.png"
                         class="Chemai-chat-avatar">
                    <span>Chemai</span>
                </div>

                <div class="loading-content">

                    <div class="ai-core">
                        <div class="core-ring"></div>
                        <div class="core-glow"></div>
                        <div class="core-center"></div>
                    </div>

                    <p id="loading-text">
                        🧪 Analyzing your chemistry question...
                    </p>

                </div>
            </div>
        `);

        chatHistory.scrollTop = chatHistory.scrollHeight;

        const states = [

            [
                "/static/images/mascot/thinking/chemai_thinking.png",
                "🧪 Analyzing your chemistry question..."
            ],

            [
                "/static/images/mascot/loading/chemai_loading.png",
                "📚 Searching chemistry knowledge..."
            ],

            [
                "/static/images/mascot/experiment/chemai_experiment.png",
                "🧬 Checking laboratory database..."
            ],

            [
                "/static/images/mascot/loading/chemai_loading.png",
                "🌱 Looking for green chemistry insights..."
            ]

        ];

        const avatar = document.getElementById("loading-avatar");
        const text = document.getElementById("loading-text");

        let state = 0;

        const loadingAnimation = setInterval(() => {

            state = (state + 1) % states.length;

            avatar.src = states[state][0];
            text.textContent = states[state][1];

        }, 800);

        try {

            console.log("Sending request to Flask...");

            const response = await fetch("/ask_ai_stream", {

                method: "POST",
                body: formData
            });

            if (!response.ok)
                throw new Error("Server Error");

            const loading = document.getElementById(loadingId);

            loading.className = "ai-message fade-in";

            loading.innerHTML = `
                <div class="Chemai-chat-header">
                    <img
                        src="/static/images/mascot/success/chemai_success.png"
                        class="Chemai-chat-avatar">
                    <span>Chemai</span>
                </div>

                <div class="ai-bubble" id="answer-${loadingId}"></div>

                <div class="message-time">${currentTime}</div>
            `;

            const bubble = document.getElementById(`answer-${loadingId}`);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let answer = "";
            let started = false;

            while (true) {

                const { value, done } = await reader.read();

                if (done)
                    break;

                if (!started) {
                    clearInterval(loadingAnimation);
                    started = true;
                }

                answer += decoder.decode(value, { stream: true });

                bubble.innerHTML = marked.parse(answer);

                chatHistory.scrollTop = chatHistory.scrollHeight;

            }

            clearInterval(loadingAnimation);

            question.focus();

        }

        catch (err) {

            clearInterval(loadingAnimation);

            const loading = document.getElementById(loadingId);

            if (loading)
                loading.remove();

            chatHistory.insertAdjacentHTML("beforeend", `
                <div class="ai-error">
                    <h3>❌ Connection Error</h3>
                    <p>Unable to contact the AI service.</p>
                </div>
            `);

        }

    });

});