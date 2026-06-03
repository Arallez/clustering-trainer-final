# Forms for tasks app (admin quiz constructor etc.)

from django import forms
from .models import Task


def _parse_quiz_from_post(data, max_questions=50, max_options_per_question=20):
    """
    Parse constructor POST data into test_input and expected_output.
    Unified format: test_input["questions"] = [ { "question", "options" }, ... ]
    expected_output = [ "id1", "id2", ... ]
    """
    questions = []
    expected = []
    q = 0
    while q < max_questions:
        q_text = (data.get(f"quiz_question_{q}") or "").strip()
        correct_id = (data.get(f"quiz_correct_{q}") or "").strip()
        options = []
        o = 0
        while o < max_options_per_question:
            oid = (data.get(f"quiz_option_{q}_{o}_id") or "").strip()
            otext = (data.get(f"quiz_option_{q}_{o}_text") or "").strip()
            if not oid and not otext:
                o += 1
                continue
            if not oid:
                oid = chr(97 + min(o, 25))
            options.append({"id": oid, "text": otext})
            o += 1
        if not q_text and not options:
            q += 1
            continue
        questions.append({"question": q_text, "options": options})
        expected.append(correct_id if correct_id else (options[0]["id"] if options else ""))
        q += 1
    return questions, expected


class TaskAdminForm(forms.ModelForm):
    """Form for Task with quiz constructor (task_type=choice)."""

    class Meta:
        model = Task
        fields = "__all__"

    def save(self, commit=True):
        task_type = self.cleaned_data.get("task_type") or (
            self.instance.task_type if self.instance.pk else "code"
        )
        if task_type == "choice" and self.data:
            questions, expected = _parse_quiz_from_post(self.data)
            if questions:
                self.instance.test_input = {"questions": questions}
                self.instance.expected_output = expected
        return super().save(commit=commit)
