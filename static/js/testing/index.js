/**
 * Testing Module Logic
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Initialize particles
    if (typeof initParticles === 'function') {
        initParticles();
    }
    
    // Initialize modals
    initDeleteModals();
});

/**
 * Initialize Delete Confirmation Modals
 */
function initDeleteModals() {
    // Delete Group Modal Logic
    const deleteGroupForms = document.querySelectorAll('.delete-group-form');
    const groupModal = document.getElementById('deleteGroupModal');

    if (groupModal) {
        const cancelGroupBtn = document.getElementById('cancelDeleteBtn');
        const confirmGroupBtn = document.getElementById('confirmDeleteBtn');
        const groupNameSpan = document.getElementById('deleteGroupName');

        let currentGroupFormToSubmit = null;

        deleteGroupForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                currentGroupFormToSubmit = form;
                const groupName = form.getAttribute('data-group-name');
                if (groupNameSpan) groupNameSpan.textContent = groupName;
                groupModal.classList.add('active');
            });
        });

        if (cancelGroupBtn) {
            cancelGroupBtn.addEventListener('click', function() {
                groupModal.classList.remove('active');
                currentGroupFormToSubmit = null;
            });
        }

        if (confirmGroupBtn) {
            confirmGroupBtn.addEventListener('click', function() {
                if (currentGroupFormToSubmit) {
                    currentGroupFormToSubmit.submit();
                }
            });
        }

        groupModal.addEventListener('click', function(e) {
            if (e.target === groupModal) {
                groupModal.classList.remove('active');
                currentGroupFormToSubmit = null;
            }
        });
    }

    // Delete Question Modal Logic
    const deleteQuestionForms = document.querySelectorAll('.delete-question-form');
    const questionModal = document.getElementById('deleteQuestionModal');

    if (questionModal) {
        const cancelQuestionBtn = document.getElementById('cancelDeleteQuestionBtn');
        const confirmQuestionBtn = document.getElementById('confirmDeleteQuestionBtn');
        const questionNameSpan = document.getElementById('deleteQuestionName');

        let currentQuestionFormToSubmit = null;

        deleteQuestionForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                currentQuestionFormToSubmit = form;
                const questionName = form.getAttribute('data-question-name');
                if (questionNameSpan) questionNameSpan.textContent = questionName;
                questionModal.classList.add('active');
            });
        });

        if (cancelQuestionBtn) {
            cancelQuestionBtn.addEventListener('click', function() {
                questionModal.classList.remove('active');
                currentQuestionFormToSubmit = null;
            });
        }

        if (confirmQuestionBtn) {
            confirmQuestionBtn.addEventListener('click', function() {
                if (currentQuestionFormToSubmit) {
                    currentQuestionFormToSubmit.submit();
                }
            });
        }

        questionModal.addEventListener('click', function(e) {
            if (e.target === questionModal) {
                questionModal.classList.remove('active');
                currentQuestionFormToSubmit = null;
            }
        });
    }

    // Delete Test Modal Logic
    const deleteTestForms = document.querySelectorAll('.delete-test-form');
    const testModal = document.getElementById('deleteTestModal');

    if (testModal) {
        const cancelTestBtn = document.getElementById('cancelDeleteTestBtn');
        const confirmTestBtn = document.getElementById('confirmDeleteTestBtn');
        const testNameSpan = document.getElementById('deleteTestName');

        let currentTestFormToSubmit = null;

        deleteTestForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                currentTestFormToSubmit = form;
                const testName = form.getAttribute('data-test-name');
                if (testNameSpan) testNameSpan.textContent = testName;
                testModal.classList.add('active');
            });
        });

        if (cancelTestBtn) {
            cancelTestBtn.addEventListener('click', function() {
                testModal.classList.remove('active');
                currentTestFormToSubmit = null;
            });
        }

        if (confirmTestBtn) {
            confirmTestBtn.addEventListener('click', function() {
                if (currentTestFormToSubmit) {
                    currentTestFormToSubmit.submit();
                }
            });
        }

        testModal.addEventListener('click', function(e) {
            if (e.target === testModal) {
                testModal.classList.remove('active');
                currentTestFormToSubmit = null;
            }
        });
    }
}
