from django import forms


PROVIDERS = (
    ("openai", "openai"),
    ("groq", "groq"),
    ("google", "google"),
)

class LLMConfigForm(forms.Form):
    llm_provider = forms.ChoiceField(choices=PROVIDERS)
    model_name   = forms.CharField()

class QuestionForm(forms.Form):
    question = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Type your question…",
            "autocomplete": "off",
            "class": "question-input"
        })
    )
    use_web_search = forms.BooleanField(required=False, label="Use Web Search")
    enhance_formatting = forms.BooleanField(required=False, label="Enhance Formatting")

class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(label="Upload PDF or CSV file")

    def clean_pdf_file(self):
        file = self.cleaned_data["pdf_file"]
        name = file.name.lower()
        if not (name.endswith(".pdf") or name.endswith(".csv")):
            raise forms.ValidationError("Only .pdf or .csv files are allowed")
        if file.size and file.size > 20 * 1024 *1024:
            raise forms.ValidationError("File too large (Max 20 MB)")
        return file
