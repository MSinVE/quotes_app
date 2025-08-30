from django import forms
from .models import Quote

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['text', 'source', 'weight']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите цитату', 'class': 'form-input'}),
            'source': forms.TextInput(attrs={'placeholder': 'Фильм или книга', 'class': 'form-input'}),
            'weight': forms.NumberInput(attrs={'min': 1, 'max': 10, 'placeholder': 'Вес (1-10)', 'class': 'form-input'}),
        }

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight < 1:
            raise forms.ValidationError('Вес должен быть больше 0.')
        return weight