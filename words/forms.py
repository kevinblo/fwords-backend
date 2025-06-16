from django import forms


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Выберите CSV файл для импорта слов. Формат: source_language_code,target_language_code,word,translation,transcription,audio_url,part_of_speech,level'
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError('Файл должен иметь расширение .csv')
        
        # Проверяем размер файла (максимум 10MB)
        if csv_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Размер файла не должен превышать 10MB')
        
        return csv_file
