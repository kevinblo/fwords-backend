# Generated manually to fix migration conflict

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('languages', '0001_initial'),
        ('users', '0004_merge_20250610_1454'),
        ('words', '0004_alter_word_difficulty_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordsProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('new', 'Новое'), ('learning', 'Изучается'), ('learned', 'Изучено'), ('mastered', 'Освоено')], default='new', max_length=10)),
                ('interval', models.PositiveIntegerField(default=1, help_text='Интервал повторения в днях')),
                ('next_review', models.DateTimeField(blank=True, help_text='Дата следующего повторения', null=True)),
                ('review_count', models.PositiveIntegerField(default=0, help_text='Количество повторений')),
                ('correct_count', models.PositiveIntegerField(default=0, help_text='Количество правильных ответов')),
                ('date_learned', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('target_language', models.ForeignKey(help_text='Язык, на который изучается перевод', on_delete=django.db.models.deletion.CASCADE, related_name='words_progress_target', to='languages.language')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='words_progress', to=settings.AUTH_USER_MODEL)),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_progress', to='words.word')),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': {('user', 'word', 'target_language')},
            },
        ),
    ]