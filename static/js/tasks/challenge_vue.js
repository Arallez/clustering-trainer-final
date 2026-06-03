const { createApp, ref, onMounted, computed, nextTick } = Vue;

const ChallengeApp = {
    setup() {
        // Global Data
        const taskType = ref('');
        const taskSlug = ref('');
        const checkSolutionUrl = ref('');
        const testAttemptId = ref(null);
        
        // Code Task State
        const initialCode = ref('');
        const isRunning = ref(false);
        const codeOutput = ref('// Здесь будет результат выполнения...');
        const isCodeSuccess = ref(null); // null, true, false
        let editor = null;

        // Quiz Task State
        const quizData = ref([]);
        const isMultiQuestion = ref(false);
        const quizAnswers = ref({}); // For multi-question: {0: 'val', 1: 'val'}. For single: ['val1', 'val2']
        const quizResultMsg = ref('');
        const isQuizSuccess = ref(null);
        const quizValidationArray = ref([]); // Holds boolean for each multi-question block
        const remediation = ref(null);

        const parseQuizData = (jsonString) => {
            let data = null;
            try {
                data = JSON.parse(jsonString);
                let attempts = 5;
                while (typeof data === 'string' && attempts > 0) {
                    try { data = JSON.parse(data); } 
                    catch (e) {
                        const clean = data.replace(/\\u00A0/g, ' ').replace(/'/g, '"');
                        try { data = JSON.parse(clean); } catch (e2) { break; }
                    }
                    attempts--;
                }
            } catch(e) { console.error('Quiz JSON Parse Error', e); }
            return data;
        };

        const initEditor = () => {
            const monacoBaseUrl = window.monacoEditorBaseUrl || '/static/js/vendor/monaco/vs';
            require.config({ paths: { 'vs': monacoBaseUrl }});
            require(['vs/editor/editor.main'], function() {
                const container = document.getElementById('monaco-editor');
                if (!container) return;
                editor = monaco.editor.create(container, {
                    value: initialCode.value,
                    language: 'python',
                    theme: 'vs-dark',
                    fontSize: 14,
                    minimap: { enabled: false },
                    automaticLayout: true
                });
            });
        };

        const postSolution = async (payload) => {
            const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
            const body = { slug: taskSlug.value, code: payload };
            if (testAttemptId.value) body.test_attempt_id = parseInt(testAttemptId.value, 10);

            const response = await fetch(checkSolutionUrl.value, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(body)
            });
            const text = await response.text();
            try {
                return JSON.parse(text);
            } catch (e) {
                throw new Error("Invalid Server Response");
            }
        };

        const runCode = async () => {
            if (!editor || isRunning.value) return;
            isRunning.value = true;
            codeOutput.value = "Проверка на сервере...";
            isCodeSuccess.value = null;
            remediation.value = null;

            try {
                const code = editor.getValue();
                const result = await postSolution(code);
                
                isCodeSuccess.value = result.success;
                if (result.success) {
                    codeOutput.value = result.message || 'Правильно!';
                    remediation.value = null;
                } else {
                    codeOutput.value = `Ошибка: ${result.error || 'Неизвестная ошибка'}`;
                    remediation.value = result.remediation || null;
                }
            } catch (e) {
                isCodeSuccess.value = false;
                codeOutput.value = `Network/Server Error: ${e.message}`;
            } finally {
                isRunning.value = false;
            }
        };

        const submitQuiz = async () => {
            if (isRunning.value) return;
            
            let payload = null;
            quizResultMsg.value = '';
            remediation.value = null;

            if (isMultiQuestion.value) {
                payload = [];
                let allAnswered = true;
                quizData.value.forEach((_, idx) => {
                    const ans = quizAnswers.value[idx];
                    if (ans !== undefined && ans !== null && ans !== '') {
                        payload.push(ans);
                    } else {
                        allAnswered = false;
                        payload.push(null);
                    }
                });

                if (!allAnswered) {
                    isQuizSuccess.value = false;
                    quizResultMsg.value = "Пожалуйста, ответьте на все вопросы";
                    return;
                }
            } else {
                payload = Array.isArray(quizAnswers.value) ? quizAnswers.value : Object.values(quizAnswers.value).filter(Boolean);
                if (payload.length === 0) {
                    isQuizSuccess.value = false;
                    quizResultMsg.value = "Выберите хотя бы один вариант";
                    return;
                }
            }

            isRunning.value = true;
            try {
                const result = await postSolution(payload);
                isQuizSuccess.value = result.success;
                
                if (result.quiz_results) {
                    quizValidationArray.value = result.quiz_results;
                }

                if (result.success) {
                    quizResultMsg.value = result.message || 'Правильно!';
                    remediation.value = null;
                } else {
                    if (result.quiz_results) {
                        quizResultMsg.value = `Некоторые ответы неверны (см. красные блоки)`;
                    } else {
                        quizResultMsg.value = result.error || 'Ошибка проверки';
                    }
                    remediation.value = result.remediation || null;
                }
            } catch(e) {
                isQuizSuccess.value = false;
                quizResultMsg.value = "Error: " + e.message;
            } finally {
                isRunning.value = false;
            }
        };

        const getOptionText = (opt) => {
            if (opt == null) return '';
            if (typeof opt === 'string' || typeof opt === 'number') return String(opt);
            return opt.text || opt.label || opt.value || opt.id || '';
        };

        const getOptionValue = (opt) => {
            if (opt == null) return '';
            if (typeof opt === 'string' || typeof opt === 'number') return String(opt);
            return opt.id || opt.value || opt.text || '';
        };

        // For Single Question Format (checkboxes)
        const toggleSingleOption = (val) => {
            if (!Array.isArray(quizAnswers.value)) quizAnswers.value = [];
            const idx = quizAnswers.value.indexOf(val);
            if (idx > -1) quizAnswers.value.splice(idx, 1);
            else quizAnswers.value.push(val);
        };

        onMounted(() => {
            // Read hidden inputs injected by Django template
            taskType.value = document.getElementById('task-type')?.value || '';
            taskSlug.value = document.getElementById('task-slug')?.value || '';
            checkSolutionUrl.value = document.getElementById('check-solution-url')?.value || '/tasks/api/check-solution/';
            testAttemptId.value = document.getElementById('test-attempt-id')?.value || null;
            initialCode.value = document.getElementById('initial-code')?.value || '';

            if (taskType.value === 'code') {
                initEditor();
            } else {
                const rawData = document.getElementById('quiz-data')?.textContent || '';
                let parsed = parseQuizData(rawData);
                if (parsed && !Array.isArray(parsed) && parsed.questions && Array.isArray(parsed.questions)) {
                    parsed = parsed.questions;
                }
                if (!Array.isArray(parsed)) {
                    parsed = (typeof parsed === 'object' && parsed !== null) ? Object.values(parsed) : [parsed];
                }
                quizData.value = parsed;
                isMultiQuestion.value = parsed.some(item => typeof item === 'object' && item.options && Array.isArray(item.options));
                
                if (!isMultiQuestion.value) {
                    quizAnswers.value = [];
                }
            }
        });

        return {
            taskType,
            isRunning,
            codeOutput,
            isCodeSuccess,
            runCode,
            quizData,
            isMultiQuestion,
            quizAnswers,
            quizResultMsg,
            isQuizSuccess,
            quizValidationArray,
            remediation,
            submitQuiz,
            getOptionText,
            getOptionValue,
            toggleSingleOption
        };
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Initialize particles if canvas exists
    if (typeof initParticles === 'function') {
        initParticles();
    }
    
    // We mount Vue to a wrapper inside .editor-area in the template
    const appEl = document.getElementById('challenge-vue-app');
    if (appEl) {
        createApp(ChallengeApp).mount('#challenge-vue-app');
    }
});
