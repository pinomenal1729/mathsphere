(function () {
    "use strict";

    const state = {
        currentView: "home",
        selectedImage: null,
        chatHistory: [],
        currentPractice: "",
        heroFrame: null,
        toastTimer: null,
        pointer: { x: 0, y: 0 }
    };

    const $ = (selector, root) => (root || document).querySelector(selector);
    const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));

    function escapeHTML(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function showToast(message) {
        const toast = $("#toast");
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add("show");
        clearTimeout(state.toastTimer);
        state.toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
    }

    function closeMenu() {
        const nav = $("#mainNav");
        const toggle = $("#menuToggle");
        if (nav) nav.classList.remove("open");
        if (toggle) {
            toggle.setAttribute("aria-expanded", "false");
            $("span", toggle).textContent = "Navigate";
        }
        document.body.classList.remove("menu-open");
    }

    function navigate(view, pushHistory) {
        const target = $("#view-" + view);
        if (!target) return;

        state.currentView = view;
        document.body.dataset.view = view;
        $$(".view").forEach(section => section.classList.toggle("active", section === target));
        $$(".main-nav [data-view]").forEach(button => {
            button.classList.toggle("active", button.dataset.view === view);
        });

        document.title = "MathSphere — " + (target.dataset.pageTitle || "See Mathematics Clearly");
        closeMenu();
        window.scrollTo({ top: 0, behavior: "smooth" });

        if (pushHistory !== false && window.location.hash !== "#" + view) {
            history.pushState({ view: view }, "", "#" + view);
        }

        if (view === "visuals") {
            window.requestAnimationFrame(() => {
                drawVectorLab();
                drawTransformLab();
            });
        }

        cancelAnimationFrame(state.heroFrame);
        if (view === "home") {
            state.heroFrame = requestAnimationFrame(drawHero);
        }
    }

    function setLessonTopic(topic) {
        $("#lessonPrompt").value = topic;
        $("#lessonTopicTitle").textContent = topic;
        $$(".topic-row").forEach(row => row.classList.toggle("active", row.dataset.topic === topic));
    }

    async function callMathSphere(message, mode, image, historyItems) {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message || "",
                mode: mode || "math",
                image: image || null,
                history: historyItems || []
            })
        });

        let data;
        try {
            data = await response.json();
        } catch (_error) {
            throw new Error("The server returned an unreadable response.");
        }

        if (!response.ok || data.error) {
            throw new Error(data.error || "MathSphere could not answer just now.");
        }
        return data;
    }

    function thinkingHTML(label) {
        return '<div class="thinking"><span>' + escapeHTML(label || "Thinking") + '</span><i></i><i></i><i></i></div>';
    }

    function renderInto(element, text) {
        if (!element) return;
        if (typeof window.renderMathContent === "function") {
            element.innerHTML = window.renderMathContent(text);
        } else if (typeof renderMathContent === "function") {
            element.innerHTML = renderMathContent(text);
        } else {
            element.innerHTML = '<p class="vr-para">' + escapeHTML(text).replace(/\n/g, "<br>") + "</p>";
        }

        if (typeof window.typesetEl === "function") {
            window.typesetEl(element);
        } else if (typeof typesetEl === "function") {
            typesetEl(element);
        } else if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise([element]).catch(() => {});
        }

        if (element.closest(".message.assistant")) {
            enhanceReasoningSteps(element);
        }
    }

    function enhanceReasoningSteps(element) {
        const candidates = $$(".vr-step-card, .vr-formula-box", element).slice(0, 6);
        candidates.forEach(block => {
            if ($(".why-step", block)) return;
            const button = document.createElement("button");
            button.type = "button";
            button.className = "why-step";
            button.textContent = "Why is this step valid?";
            button.addEventListener("click", () => {
                const context = block.textContent.replace(button.textContent, "").trim().slice(0, 500);
                $("#askInput").value = "In the previous solution, why is this step valid?\n" + context;
                autoResize($("#askInput"));
                $("#askInput").focus();
            });
            block.appendChild(button);
        });
    }

    function renderError(element, error) {
        const message = error && error.message ? error.message : "Something went wrong. Please try again.";
        element.innerHTML = '<div class="error-bubble"><div class="error-title">Unable to complete this</div><div class="error-body">' + escapeHTML(message) + "</div></div>";
    }

    function setButtonLoading(button, loading, loadingText) {
        if (!button) return;
        if (loading) {
            button.dataset.originalText = button.textContent;
            button.textContent = loadingText || "Working...";
            button.disabled = true;
        } else {
            button.textContent = button.dataset.originalText || button.textContent;
            button.disabled = false;
        }
    }

    async function buildLesson() {
        const topic = $("#lessonPrompt").value.trim();
        const mode = $("#lessonStyle").value;
        const result = $("#lessonResult");
        const button = $("#buildLessonBtn");
        if (!topic) {
            showToast("Choose or enter a topic first.");
            $("#lessonPrompt").focus();
            return;
        }

        setLessonTopic(topic);
        $("#lessonEmpty").classList.add("hidden");
        result.classList.remove("hidden");
        result.classList.add("loading");
        result.innerHTML = thinkingHTML("Building your lesson");
        setButtonLoading(button, true, "Building...");
        $$(".proof-thread span").forEach((step, index) => step.classList.toggle("active", index === 0));

        const prompt =
            "Teach me " + topic + ". Begin with why the idea was needed, build the intuition, " +
            "then introduce the formal mathematics and finish with one clear numerical example and one short understanding check.";

        try {
            const data = await callMathSphere(prompt, mode);
            result.classList.remove("loading");
            renderInto(result, data.response);
            $$(".proof-thread span").forEach(step => step.classList.add("active"));
        } catch (error) {
            result.classList.remove("loading");
            renderError(result, error);
        } finally {
            setButtonLoading(button, false);
        }
    }

    async function generatePractice() {
        const topic = $("#practiceTopic").value;
        const level = $("#practiceLevel").value;
        const focus = $("#practiceFocus").selectedOptions[0].textContent;
        const questionArea = $("#practiceQuestion");
        const feedback = $("#practiceFeedback");
        const button = $("#generatePracticeBtn");

        state.currentPractice = "";
        $("#studentAnswer").value = "";
        $("#answerArea").classList.add("hidden");
        feedback.classList.add("hidden");
        questionArea.className = "question-area loading";
        questionArea.innerHTML = thinkingHTML("Creating one focused question");
        $("#practiceStatus").textContent = "Preparing a question";
        setButtonLoading(button, true, "Generating...");

        const prompt =
            "Create exactly one " + level + " level mathematics practice question on " + topic +
            ", focused on " + focus + ". Do not give a hint, solution, answer, marking scheme, or explanation. " +
            "Return only a clear standalone question with all necessary information.";

        try {
            const data = await callMathSphere(prompt, "practice_question");
            state.currentPractice = data.response;
            questionArea.className = "question-area has-question";
            renderInto(questionArea, data.response);
            $("#answerArea").classList.remove("hidden");
            $("#practiceStatus").textContent = topic + " · " + level;
        } catch (error) {
            questionArea.className = "question-area has-question";
            renderError(questionArea, error);
            $("#practiceStatus").textContent = "Please try again";
        } finally {
            setButtonLoading(button, false);
        }
    }

    async function getHint() {
        if (!state.currentPractice) {
            showToast("Generate a question first.");
            return;
        }
        const feedback = $("#practiceFeedback");
        const button = $("#hintBtn");
        feedback.classList.remove("hidden");
        feedback.classList.add("loading");
        feedback.innerHTML = thinkingHTML("Finding the smallest useful hint");
        setButtonLoading(button, true, "Thinking...");

        const prompt =
            "Here is my practice question:\n\n" + state.currentPractice +
            "\n\nGive me exactly one short conceptual hint. Do not reveal the final answer or complete the solution.";

        try {
            const data = await callMathSphere(prompt, "socratic");
            feedback.classList.remove("loading");
            renderInto(feedback, data.response);
        } catch (error) {
            feedback.classList.remove("loading");
            renderError(feedback, error);
        } finally {
            setButtonLoading(button, false);
        }
    }

    async function checkPracticeAnswer() {
        const answer = $("#studentAnswer").value.trim();
        if (!state.currentPractice) {
            showToast("Generate a question first.");
            return;
        }
        if (!answer) {
            showToast("Write your attempt before checking it.");
            $("#studentAnswer").focus();
            return;
        }

        const feedback = $("#practiceFeedback");
        const button = $("#checkAnswerBtn");
        feedback.classList.remove("hidden");
        feedback.classList.add("loading");
        feedback.innerHTML = thinkingHTML("Checking your reasoning");
        setButtonLoading(button, true, "Checking...");

        const prompt =
            "QUESTION:\n" + state.currentPractice +
            "\n\nSTUDENT'S WORKING:\n" + answer +
            "\n\nCheck this attempt carefully. First say what is correct, then identify the first exact error if any, " +
            "and finally show the corrected reasoning. Do not be harsh.";

        try {
            const data = await callMathSphere(prompt, "checker");
            feedback.classList.remove("loading");
            renderInto(feedback, data.response);
        } catch (error) {
            feedback.classList.remove("loading");
            renderError(feedback, error);
        } finally {
            setButtonLoading(button, false);
        }
    }

    function appendUserMessage(text, hasImage) {
        const messages = $("#chatMessages");
        const welcome = $("#chatWelcome");
        if (welcome) welcome.remove();
        const item = document.createElement("div");
        item.className = "message user";
        const suffix = hasImage ? '<div style="margin-top:7px;font-size:10px;opacity:.7">Image attached</div>' : "";
        item.innerHTML = '<div class="message-inner">' + escapeHTML(text || "Please solve the attached problem.") + suffix + "</div>";
        messages.appendChild(item);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendAssistantShell() {
        const messages = $("#chatMessages");
        const item = document.createElement("div");
        item.className = "message assistant";
        item.innerHTML = '<div class="message-label">MathSphere</div><div class="message-inner">' + thinkingHTML("Working through it") + "</div>";
        messages.appendChild(item);
        messages.scrollTop = messages.scrollHeight;
        return item;
    }

    async function sendAsk() {
        const input = $("#askInput");
        const message = input.value.trim();
        const mode = $("#askMode").value;
        const level = $("#askLevel").value;
        const image = state.selectedImage;
        const submit = $(".composer-send");

        if (!message && !image) {
            showToast("Type a question or attach an image.");
            input.focus();
            return;
        }

        const displayMessage = message || "Please solve the problem in this image.";
        const transcriptionInstruction = image
            ? "Begin with TRANSCRIPTION: and reproduce exactly what you read from the image before solving. If any symbol is uncertain, state that uncertainty.\n"
            : "";
        const requestMessage = "[Difficulty: " + level + "]\n" + transcriptionInstruction + displayMessage;
        const previousHistory = state.chatHistory.slice(-8);

        appendUserMessage(displayMessage, Boolean(image));
        const assistantItem = appendAssistantShell();
        const assistantBody = $(".message-inner", assistantItem);

        state.chatHistory.push({ role: "user", content: displayMessage });
        input.value = "";
        autoResize(input);
        clearUpload();
        submit.disabled = true;

        try {
            const data = await callMathSphere(requestMessage, mode, image, previousHistory);
            renderInto(assistantBody, data.response);
            const source = document.createElement("div");
            source.className = "message-source";
            source.textContent = "Answered by " + (data.source || "MathSphere");
            assistantBody.appendChild(source);
            state.chatHistory.push({ role: "assistant", content: data.response });
        } catch (error) {
            renderError(assistantBody, error);
        } finally {
            submit.disabled = false;
            $("#chatMessages").scrollTop = $("#chatMessages").scrollHeight;
        }
    }

    function clearChat() {
        state.chatHistory = [];
        clearUpload();
        $("#chatMessages").innerHTML =
            '<div class="chat-welcome" id="chatWelcome"><span class="folio">01</span>' +
            "<p>There is no such thing as a badly worded first question.</p>" +
            "<h2>What are you trying to understand?</h2></div>";
    }

    function clearUpload() {
        state.selectedImage = null;
        $("#askImage").value = "";
        $("#uploadPreview").classList.add("hidden");
        $("#uploadImage").removeAttribute("src");
        $("#uploadName").textContent = "";
    }

    function handleUpload(file) {
        if (!file) return;
        if (!file.type.startsWith("image/")) {
            showToast("Please choose an image file.");
            return;
        }
        if (file.size > 8 * 1024 * 1024) {
            showToast("Please choose an image smaller than 8 MB.");
            return;
        }

        const reader = new FileReader();
        reader.onload = event => {
            const dataUrl = event.target.result;
            state.selectedImage = {
                data: dataUrl.split(",")[1],
                mimeType: file.type
            };
            $("#uploadImage").src = dataUrl;
            $("#uploadName").textContent = file.name;
            $("#uploadPreview").classList.remove("hidden");
        };
        reader.onerror = () => showToast("That image could not be read.");
        reader.readAsDataURL(file);
    }

    function autoResize(textarea) {
        textarea.style.height = "auto";
        textarea.style.height = Math.min(textarea.scrollHeight, 130) + "px";
    }

    /* Canvas helpers */
    function prepareCanvas(canvas) {
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        const width = Math.round(rect.width * ratio);
        const height = Math.round(rect.height * ratio);
        if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
        }
        const ctx = canvas.getContext("2d");
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        ctx.clearRect(0, 0, rect.width, rect.height);
        return { ctx: ctx, width: rect.width, height: rect.height };
    }

    function drawGrid(ctx, width, height, originX, originY, spacing, color) {
        ctx.save();
        ctx.strokeStyle = color || "rgba(255,255,255,.07)";
        ctx.lineWidth = 1;
        for (let x = originX % spacing; x <= width; x += spacing) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        for (let y = originY % spacing; y <= height; y += spacing) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        ctx.strokeStyle = "rgba(255,255,255,.22)";
        ctx.beginPath();
        ctx.moveTo(0, originY);
        ctx.lineTo(width, originY);
        ctx.moveTo(originX, 0);
        ctx.lineTo(originX, height);
        ctx.stroke();
        ctx.restore();
    }

    function drawArrow(ctx, x1, y1, x2, y2, color, width, label) {
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const head = 10 + (width || 2);
        ctx.save();
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = width || 2;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - head * Math.cos(angle - Math.PI / 6), y2 - head * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(x2 - head * Math.cos(angle + Math.PI / 6), y2 - head * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
        if (label) {
            ctx.font = '500 12px "DM Mono", monospace';
            ctx.fillText(label, x2 + 9 * Math.cos(angle - Math.PI / 2), y2 + 9 * Math.sin(angle - Math.PI / 2));
        }
        ctx.restore();
    }

    function drawHero(time) {
        const canvas = $("#heroCanvas");
        const prepared = prepareCanvas(canvas);
        if (!prepared) return;
        const { ctx, width, height } = prepared;
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const clock = reduced ? 0 : (time || 0) * .00012;
        const cx = width * .5;
        const cy = height * .46;
        const radius = Math.min(width, height) * (width < 700 ? .25 : .27);
        const yaw = clock + state.pointer.x * .22;
        const pitch = -.24 + state.pointer.y * .16;

        function project(latitude, longitude) {
            const x = Math.cos(latitude) * Math.cos(longitude);
            const y = Math.sin(latitude);
            const z = Math.cos(latitude) * Math.sin(longitude);
            const x1 = x * Math.cos(yaw) - z * Math.sin(yaw);
            const z1 = x * Math.sin(yaw) + z * Math.cos(yaw);
            const y1 = y * Math.cos(pitch) - z1 * Math.sin(pitch);
            const z2 = y * Math.sin(pitch) + z1 * Math.cos(pitch);
            return { x: cx + x1 * radius, y: cy - y1 * radius, z: z2 };
        }

        function drawCurve(points, rgb) {
            for (let front = 0; front < 2; front++) {
                ctx.beginPath();
                let drawing = false;
                points.forEach(point => {
                    const visible = front ? point.z >= 0 : point.z < 0;
                    if (!visible) {
                        drawing = false;
                        return;
                    }
                    if (!drawing) ctx.moveTo(point.x, point.y);
                    else ctx.lineTo(point.x, point.y);
                    drawing = true;
                });
                ctx.strokeStyle = "rgba(" + rgb + "," + (front ? .34 : .075) + ")";
                ctx.lineWidth = front ? 1 : .7;
                ctx.stroke();
            }
        }

        ctx.save();
        ctx.shadowBlur = 22;
        ctx.shadowColor = "rgba(99,230,204,.16)";
        for (let i = -4; i <= 4; i++) {
            const points = [];
            const latitude = i * Math.PI / 12;
            for (let n = 0; n <= 96; n++) points.push(project(latitude, n / 96 * Math.PI * 2));
            drawCurve(points, "99,230,204");
        }
        for (let i = 0; i < 12; i++) {
            const points = [];
            const longitude = i / 12 * Math.PI * 2;
            for (let n = -48; n <= 48; n++) points.push(project(n / 48 * Math.PI / 2, longitude));
            drawCurve(points, "110,139,255");
        }
        ctx.restore();

        const orbit = project(.24, 1.2 + clock * 4);
        ctx.beginPath();
        ctx.arc(orbit.x, orbit.y, orbit.z > 0 ? 3.2 : 1.7, 0, Math.PI * 2);
        ctx.fillStyle = orbit.z > 0 ? "#ffb45a" : "rgba(255,180,90,.25)";
        ctx.shadowBlur = orbit.z > 0 ? 16 : 0;
        ctx.shadowColor = "#ffb45a";
        ctx.fill();
        ctx.shadowBlur = 0;

        if (!reduced && state.currentView === "home") {
            state.heroFrame = requestAnimationFrame(drawHero);
        }
    }

    function drawVectorLab() {
        const prepared = prepareCanvas($("#vectorCanvas"));
        if (!prepared) return;
        const { ctx, width, height } = prepared;
        const alpha = Number($("#alphaRange").value);
        const beta = Number($("#betaRange").value);
        const originX = width * .5;
        const originY = height * .57;
        const scale = Math.min(width, height) * .135;
        const a = { x: 1.65 * scale, y: -.7 * scale };
        const b = { x: -.45 * scale, y: -1.45 * scale };
        const result = { x: alpha * a.x + beta * b.x, y: alpha * a.y + beta * b.y };

        drawGrid(ctx, width, height, originX, originY, Math.max(34, scale * .52), "rgba(255,255,255,.065)");

        ctx.save();
        ctx.fillStyle = "rgba(8,127,108,.08)";
        ctx.beginPath();
        ctx.moveTo(originX, originY);
        ctx.lineTo(originX + alpha * a.x, originY + alpha * a.y);
        ctx.lineTo(originX + result.x, originY + result.y);
        ctx.lineTo(originX + beta * b.x, originY + beta * b.y);
        ctx.closePath();
        ctx.fill();
        ctx.restore();

        drawArrow(ctx, originX, originY, originX + a.x, originY + a.y, "#66d9bf", 2.5, "a");
        drawArrow(ctx, originX, originY, originX + b.x, originY + b.y, "#8eb6ef", 2.5, "b");
        drawArrow(ctx, originX, originY, originX + result.x, originY + result.y, "#f5eee2", 3.5, "result");

        $("#alphaOutput").textContent = alpha.toFixed(1);
        $("#betaOutput").textContent = beta.toFixed(1);
        $("#vectorEquation").textContent = alpha.toFixed(1) + "a + " + beta.toFixed(1) + "b";
    }

    function matrixValues() {
        return ["#mA", "#mB", "#mC", "#mD"].map(selector => {
            const value = Number($(selector).value);
            return Number.isFinite(value) ? Math.max(-3, Math.min(3, value)) : 0;
        });
    }

    function drawTransformLab() {
        const prepared = prepareCanvas($("#transformCanvas"));
        if (!prepared) return;
        const { ctx, width, height } = prepared;
        const [a, b, c, d] = matrixValues();
        const originX = width / 2;
        const originY = height / 2;
        const scale = Math.min(width, height) / 9;

        drawGrid(ctx, width, height, originX, originY, scale, "rgba(255,255,255,.035)");

        function point(x, y) {
            return {
                x: originX + (a * x + b * y) * scale,
                y: originY - (c * x + d * y) * scale
            };
        }

        ctx.save();
        ctx.strokeStyle = "rgba(105,214,189,.24)";
        ctx.lineWidth = 1.15;
        for (let k = -8; k <= 8; k++) {
            let p1 = point(k, -8);
            let p2 = point(k, 8);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            p1 = point(-8, k);
            p2 = point(8, k);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        }
        ctx.restore();

        const e1 = point(1, 0);
        const e2 = point(0, 1);
        drawArrow(ctx, originX, originY, e1.x, e1.y, "#67dac0", 3, "Ae₁");
        drawArrow(ctx, originX, originY, e2.x, e2.y, "#8fb7ef", 3, "Ae₂");

        const det = a * d - b * c;
        $("#determinantValue").textContent = det.toFixed(2);
        $("#matrixEquation").textContent = "[[" + a + ", " + b + "], [" + c + ", " + d + "]]";
    }

    function setMatrix(values) {
        ["#mA", "#mB", "#mC", "#mD"].forEach((selector, index) => {
            $(selector).value = values[index];
        });
        drawTransformLab();
    }

    function switchLab(lab) {
        $$(".lab-tab").forEach(button => {
            const active = button.dataset.lab === lab;
            button.classList.toggle("active", active);
            button.setAttribute("aria-selected", String(active));
        });
        $$(".lab-panel").forEach(panel => panel.classList.toggle("active", panel.id === "lab-" + lab));
        requestAnimationFrame(() => lab === "vectors" ? drawVectorLab() : drawTransformLab());
    }

    function bindEvents() {
        $$("[data-view]").forEach(button => {
            button.addEventListener("click", () => navigate(button.dataset.view));
        });
        $$("[data-view-link]").forEach(link => {
            link.addEventListener("click", event => {
                event.preventDefault();
                navigate(link.dataset.viewLink);
            });
        });

        $("#menuToggle").addEventListener("click", () => {
            const nav = $("#mainNav");
            const open = !nav.classList.contains("open");
            nav.classList.toggle("open", open);
            $("#menuToggle").setAttribute("aria-expanded", String(open));
            $("#menuToggle span").textContent = open ? "Close" : "Navigate";
            document.body.classList.toggle("menu-open", open);
        });

        $("#heroAskForm").addEventListener("submit", event => {
            event.preventDefault();
            const question = $("#heroQuestion").value.trim();
            navigate("ask");
            if (question) {
                $("#askInput").value = question;
                sendAsk();
            } else {
                $("#askInput").focus();
            }
        });

        $$("[data-lesson]").forEach(button => {
            button.addEventListener("click", () => {
                navigate("learn");
                setLessonTopic(button.dataset.lesson);
                window.setTimeout(buildLesson, 240);
            });
        });

        $$(".topic-row").forEach(row => {
            row.addEventListener("click", () => setLessonTopic(row.dataset.topic));
        });
        $("#buildLessonBtn").addEventListener("click", buildLesson);
        $("#lessonPrompt").addEventListener("keydown", event => {
            if (event.key === "Enter") buildLesson();
        });

        $$(".lab-tab").forEach(button => button.addEventListener("click", () => switchLab(button.dataset.lab)));
        $("#alphaRange").addEventListener("input", drawVectorLab);
        $("#betaRange").addEventListener("input", drawVectorLab);
        ["#mA", "#mB", "#mC", "#mD"].forEach(selector => $(selector).addEventListener("input", drawTransformLab));
        $$("[data-matrix]").forEach(button => {
            button.addEventListener("click", () => setMatrix(button.dataset.matrix.split(",").map(Number)));
        });

        $("#generatePracticeBtn").addEventListener("click", generatePractice);
        $("#newPracticeBtn").addEventListener("click", generatePractice);
        $("#hintBtn").addEventListener("click", getHint);
        $("#checkAnswerBtn").addEventListener("click", checkPracticeAnswer);

        $$(".ask-prompts [data-question]").forEach(button => {
            button.addEventListener("click", () => {
                $("#askInput").value = button.dataset.question;
                $("#askInput").focus();
                autoResize($("#askInput"));
            });
        });
        $("#chatForm").addEventListener("submit", event => {
            event.preventDefault();
            sendAsk();
        });
        $("#askInput").addEventListener("input", event => autoResize(event.target));
        $("#askInput").addEventListener("keydown", event => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendAsk();
            }
        });
        $("#askImage").addEventListener("change", event => handleUpload(event.target.files[0]));
        $("#removeUploadBtn").addEventListener("click", clearUpload);
        $("#clearChatBtn").addEventListener("click", clearChat);

        const cursor = $("#cursorPoint");
        window.addEventListener("pointermove", event => {
            state.pointer.x = event.clientX / Math.max(window.innerWidth, 1) * 2 - 1;
            state.pointer.y = event.clientY / Math.max(window.innerHeight, 1) * 2 - 1;
            if (cursor && event.pointerType !== "touch") {
                cursor.style.left = event.clientX + "px";
                cursor.style.top = event.clientY + "px";
                cursor.classList.add("visible");
            }
        }, { passive: true });
        document.addEventListener("pointerover", event => {
            if (cursor && event.target.closest("button, a, input, textarea, select")) cursor.classList.add("active");
        });
        document.addEventListener("pointerout", event => {
            if (cursor && event.target.closest("button, a, input, textarea, select")) cursor.classList.remove("active");
        });
        document.addEventListener("keydown", event => {
            if (event.key === "Escape") closeMenu();
        });

        window.addEventListener("scroll", () => $("#siteHeader").classList.toggle("scrolled", window.scrollY > 10), { passive: true });
        window.addEventListener("popstate", () => {
            const view = window.location.hash.replace("#", "") || "home";
            navigate(view, false);
        });
        window.addEventListener("resize", () => {
            if (state.currentView === "home") {
                cancelAnimationFrame(state.heroFrame);
                state.heroFrame = requestAnimationFrame(drawHero);
            }
            if (state.currentView === "visuals") {
                drawVectorLab();
                drawTransformLab();
            }
        });
    }

    function init() {
        bindEvents();
        const initial = window.location.hash.replace("#", "");
        navigate(["home", "learn", "visuals", "practice", "ask"].includes(initial) ? initial : "home", false);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
