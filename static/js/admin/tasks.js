// JavaScript для админки задач (Task) - конструктор тестов

document.addEventListener('DOMContentLoaded', function() {
    // Показ/скрытие конструктора теста по типу задачи
    var taskTypeField = document.getElementById('id_task_type');
    var quizFieldset = document.querySelector('.quiz-constructor-fieldset');
    
    function toggleQuizConstructor() {
        if (!taskTypeField || !quizFieldset) return;
        
        var selectedType = taskTypeField.value;
        if (selectedType === 'choice') {
            quizFieldset.style.display = 'block';
        } else {
            quizFieldset.style.display = 'none';
        }
    }
    
    if (taskTypeField) {
        taskTypeField.addEventListener('change', toggleQuizConstructor);
        // Вызываем при загрузке страницы
        toggleQuizConstructor();
    }
    
    // Конструктор тестов
    var container = document.getElementById('quiz-questions-container');
    var addQuestionBtn = document.getElementById('add-quiz-question');
    if (!container || !addQuestionBtn) return;

    function nextQuestionIndex() {
        return container.querySelectorAll('.quiz-question-block').length;
    }

    function makeOptionRow(qIdx, oIdx, idVal, textVal) {
        var tr = document.createElement('tr');
        tr.className = 'quiz-option-row';
        
        // ID cell
        var tdId = document.createElement('td');
        var inputId = document.createElement('input');
        inputId.type = 'text';
        inputId.name = 'quiz_option_' + qIdx + '_' + oIdx + '_id';
        inputId.value = idVal;
        inputId.maxLength = 10;
        tdId.appendChild(inputId);
        
        // Text cell
        var tdText = document.createElement('td');
        var inputText = document.createElement('input');
        inputText.type = 'text';
        inputText.name = 'quiz_option_' + qIdx + '_' + oIdx + '_text';
        inputText.value = textVal;
        tdText.appendChild(inputText);
        
        // Button cell
        var tdBtn = document.createElement('td');
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'admin-btn admin-btn-danger admin-btn-sm remove-quiz-option';
        btn.textContent = '×';
        btn.addEventListener('click', function() {
            var tbody = tr.closest('tbody');
            if (tbody.querySelectorAll('.quiz-option-row').length > 1) {
                tr.remove();
                reindexOptionsInTbody(tbody);
            }
        });
        tdBtn.appendChild(btn);
        
        tr.appendChild(tdId);
        tr.appendChild(tdText);
        tr.appendChild(tdBtn);
        
        return tr;
    }

    function reindexOptionsInTbody(tbody) {
        var qIdx = parseInt(tbody.getAttribute('data-question-index'), 10);
        var rows = tbody.querySelectorAll('.quiz-option-row');
        rows.forEach(function(tr, idx) {
            var idInp = tr.querySelector('input[name$="_id"]');
            var textInp = tr.querySelector('input[name$="_text"]');
            if (idInp) idInp.name = 'quiz_option_' + qIdx + '_' + idx + '_id';
            if (textInp) textInp.name = 'quiz_option_' + qIdx + '_' + idx + '_text';
        });
    }

    function addQuestionBlock(qIdx) {
        var block = document.createElement('div');
        block.className = 'quiz-question-block';
        block.setAttribute('data-question-index', qIdx);
        
        // Title
        var title = document.createElement('h4');
        title.className = 'quiz-question-title';
        title.textContent = 'Вопрос ' + (qIdx + 1);
        block.appendChild(title);
        
        // Question text field
        var fieldQuestion = document.createElement('div');
        fieldQuestion.className = 'form-field';
        var labelQuestion = document.createElement('label');
        labelQuestion.className = 'field-label';
        labelQuestion.textContent = 'Текст вопроса:';
        var widgetQuestion = document.createElement('div');
        widgetQuestion.className = 'field-widget';
        var textareaQuestion = document.createElement('textarea');
        textareaQuestion.name = 'quiz_question_' + qIdx;
        textareaQuestion.rows = 2;
        widgetQuestion.appendChild(textareaQuestion);
        fieldQuestion.appendChild(labelQuestion);
        fieldQuestion.appendChild(widgetQuestion);
        block.appendChild(fieldQuestion);
        
        // Options field
        var fieldOptions = document.createElement('div');
        fieldOptions.className = 'form-field';
        var labelOptions = document.createElement('label');
        labelOptions.className = 'field-label';
        labelOptions.textContent = 'Варианты ответа:';
        var widgetOptions = document.createElement('div');
        widgetOptions.className = 'field-widget';
        
        // Table
        var table = document.createElement('table');
        table.className = 'quiz-options-table';
        var thead = document.createElement('thead');
        var trHead = document.createElement('tr');
        ['ID', 'Текст', ''].forEach(function(text) {
            var th = document.createElement('th');
            th.textContent = text;
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);
        table.appendChild(thead);
        
        var tbody = document.createElement('tbody');
        tbody.className = 'quiz-options-tbody';
        tbody.setAttribute('data-question-index', qIdx);
        table.appendChild(tbody);
        
        widgetOptions.appendChild(table);
        
        // Add option button
        var addOptBtn = document.createElement('button');
        addOptBtn.type = 'button';
        addOptBtn.className = 'admin-btn admin-btn-outline admin-btn-sm add-quiz-option';
        addOptBtn.setAttribute('data-question-index', qIdx);
        var iconPlus = document.createElement('i');
        iconPlus.setAttribute('data-lucide', 'plus');
        iconPlus.style.width = '14px';
        iconPlus.style.height = '14px';
        addOptBtn.appendChild(iconPlus);
        addOptBtn.appendChild(document.createTextNode(' Добавить вариант'));
        addOptBtn.addEventListener('click', function() {
            var tbody = block.querySelector('.quiz-options-tbody');
            var oIdx = tbody.querySelectorAll('.quiz-option-row').length;
            tbody.appendChild(makeOptionRow(qIdx, oIdx, String.fromCharCode(97 + Math.min(oIdx, 25)), ''));
            reindexOptionsInTbody(tbody);
        });
        widgetOptions.appendChild(addOptBtn);
        
        fieldOptions.appendChild(labelOptions);
        fieldOptions.appendChild(widgetOptions);
        block.appendChild(fieldOptions);
        
        // Correct answer field
        var fieldCorrect = document.createElement('div');
        fieldCorrect.className = 'form-field';
        var labelCorrect = document.createElement('label');
        labelCorrect.className = 'field-label';
        labelCorrect.textContent = 'Правильный ответ (ID варианта):';
        var widgetCorrect = document.createElement('div');
        widgetCorrect.className = 'field-widget';
        var inputCorrect = document.createElement('input');
        inputCorrect.type = 'text';
        inputCorrect.name = 'quiz_correct_' + qIdx;
        inputCorrect.value = '';
        inputCorrect.maxLength = 10;
        widgetCorrect.appendChild(inputCorrect);
        fieldCorrect.appendChild(labelCorrect);
        fieldCorrect.appendChild(widgetCorrect);
        block.appendChild(fieldCorrect);
        
        // Remove question button
        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'admin-btn admin-btn-danger remove-quiz-question';
        var iconTrash = document.createElement('i');
        iconTrash.setAttribute('data-lucide', 'trash-2');
        iconTrash.style.width = '14px';
        iconTrash.style.height = '14px';
        removeBtn.appendChild(iconTrash);
        removeBtn.appendChild(document.createTextNode(' Удалить вопрос'));
        removeBtn.addEventListener('click', function() {
            if (container.querySelectorAll('.quiz-question-block').length > 1) {
                block.remove();
                reindexQuestionBlocks();
            }
        });
        block.appendChild(removeBtn);
        
        container.appendChild(block);
        
        // Add default options
        tbody.appendChild(makeOptionRow(qIdx, 0, 'a', ''));
        tbody.appendChild(makeOptionRow(qIdx, 1, 'b', ''));
        
        // Re-initialize lucide icons for new elements
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function reindexQuestionBlocks() {
        container.querySelectorAll('.quiz-question-block').forEach(function(block, newIdx) {
            block.setAttribute('data-question-index', newIdx);
            block.querySelector('.quiz-question-title').textContent = 'Вопрос ' + (newIdx + 1);
            var qText = block.querySelector('textarea[name^="quiz_question_"]');
            var qCorrect = block.querySelector('input[name^="quiz_correct_"]');
            if (qText) qText.name = 'quiz_question_' + newIdx;
            if (qCorrect) qCorrect.name = 'quiz_correct_' + newIdx;
            var tbody = block.querySelector('.quiz-options-tbody');
            tbody.setAttribute('data-question-index', newIdx);
            reindexOptionsInTbody(tbody);
            var addOptBtn = block.querySelector('.add-quiz-option');
            if (addOptBtn) addOptBtn.setAttribute('data-question-index', newIdx);
        });
    }

    addQuestionBtn.addEventListener('click', function() {
        addQuestionBlock(nextQuestionIndex());
    });

    // Инициализация существующих блоков
    container.querySelectorAll('.quiz-question-block').forEach(function(block) {
        block.querySelectorAll('.remove-quiz-option').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var tr = btn.closest('tr');
                var tbody = tr.closest('tbody');
                if (tbody.querySelectorAll('.quiz-option-row').length > 1) {
                    tr.remove();
                    reindexOptionsInTbody(tbody);
                }
            });
        });
        
        var addOptBtn = block.querySelector('.add-quiz-option');
        if (addOptBtn) {
            addOptBtn.addEventListener('click', function() {
                var tbody = block.querySelector('.quiz-options-tbody');
                var qIdx = parseInt(tbody.getAttribute('data-question-index'), 10);
                var oIdx = tbody.querySelectorAll('.quiz-option-row').length;
                tbody.appendChild(makeOptionRow(qIdx, oIdx, String.fromCharCode(97 + Math.min(oIdx, 25)), ''));
                reindexOptionsInTbody(tbody);
            });
        }
        
        block.querySelectorAll('.remove-quiz-question').forEach(function(btn) {
            btn.addEventListener('click', function() {
                if (container.querySelectorAll('.quiz-question-block').length > 1) {
                    block.remove();
                    reindexQuestionBlocks();
                }
            });
        });
    });
});