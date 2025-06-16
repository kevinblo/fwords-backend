from django.core.management.base import BaseCommand
from django.db import transaction
from languages.models import Language
from parts_of_speech.models import PartOfSpeech, PartOfSpeechTranslation


class Command(BaseCommand):
    help = 'Заполняет базу данных базовыми частями речи с переводами на разные языки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие части речи перед добавлением новых',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очистка существующих частей речи...')
            PartOfSpeech.objects.all().delete()

        # Определяем базовые части речи с переводами
        parts_of_speech_data = {
            'noun': {
                'description': 'A word used to identify any of a class of people, places, or things',
                'translations': {
                    'en': {'name': 'Noun', 'abbreviation': 'n.'},
                    'ru': {'name': 'Существительное', 'abbreviation': 'сущ.'},
                    'es': {'name': 'Sustantivo', 'abbreviation': 'sust.'},
                    'fr': {'name': 'Nom', 'abbreviation': 'n.'},
                    'de': {'name': 'Substantiv', 'abbreviation': 'subst.'},
                    'it': {'name': 'Sostantivo', 'abbreviation': 'sost.'},
                    'pt': {'name': 'Substantivo', 'abbreviation': 'subst.'},
                    'zh': {'name': '名词', 'abbreviation': '名'},
                    'ja': {'name': '名詞', 'abbreviation': '名'},
                    'ko': {'name': '명사', 'abbreviation': '명'},
                }
            },
            'verb': {
                'description': 'A word used to describe an action, state, or occurrence',
                'translations': {
                    'en': {'name': 'Verb', 'abbreviation': 'v.'},
                    'ru': {'name': 'Глагол', 'abbreviation': 'гл.'},
                    'es': {'name': 'Verbo', 'abbreviation': 'v.'},
                    'fr': {'name': 'Verbe', 'abbreviation': 'v.'},
                    'de': {'name': 'Verb', 'abbreviation': 'v.'},
                    'it': {'name': 'Verbo', 'abbreviation': 'v.'},
                    'pt': {'name': 'Verbo', 'abbreviation': 'v.'},
                    'zh': {'name': '动词', 'abbreviation': '动'},
                    'ja': {'name': '動詞', 'abbreviation': '動'},
                    'ko': {'name': '동사', 'abbreviation': '동'},
                }
            },
            'adjective': {
                'description': 'A word naming an attribute of a noun, such as sweet, red, or technical',
                'translations': {
                    'en': {'name': 'Adjective', 'abbreviation': 'adj.'},
                    'ru': {'name': 'Прилагательное', 'abbreviation': 'прил.'},
                    'es': {'name': 'Adjetivo', 'abbreviation': 'adj.'},
                    'fr': {'name': 'Adjectif', 'abbreviation': 'adj.'},
                    'de': {'name': 'Adjektiv', 'abbreviation': 'adj.'},
                    'it': {'name': 'Aggettivo', 'abbreviation': 'agg.'},
                    'pt': {'name': 'Adjetivo', 'abbreviation': 'adj.'},
                    'zh': {'name': '形容词', 'abbreviation': '形'},
                    'ja': {'name': '形容詞', 'abbreviation': '形'},
                    'ko': {'name': '형용사', 'abbreviation': '형'},
                }
            },
            'adverb': {
                'description': 'A word or phrase that modifies or qualifies an adjective, verb, or other adverb',
                'translations': {
                    'en': {'name': 'Adverb', 'abbreviation': 'adv.'},
                    'ru': {'name': 'Наречие', 'abbreviation': 'нар.'},
                    'es': {'name': 'Adverbio', 'abbreviation': 'adv.'},
                    'fr': {'name': 'Adverbe', 'abbreviation': 'adv.'},
                    'de': {'name': 'Adverb', 'abbreviation': 'adv.'},
                    'it': {'name': 'Avverbio', 'abbreviation': 'avv.'},
                    'pt': {'name': 'Advérbio', 'abbreviation': 'adv.'},
                    'zh': {'name': '副词', 'abbreviation': '副'},
                    'ja': {'name': '副詞', 'abbreviation': '副'},
                    'ko': {'name': '부사', 'abbreviation': '부'},
                }
            },
            'pronoun': {
                'description': 'A word that can function by itself as a noun phrase and that refers either to the participants in the discourse',
                'translations': {
                    'en': {'name': 'Pronoun', 'abbreviation': 'pron.'},
                    'ru': {'name': 'Местоимение', 'abbreviation': 'мест.'},
                    'es': {'name': 'Pronombre', 'abbreviation': 'pron.'},
                    'fr': {'name': 'Pronom', 'abbreviation': 'pron.'},
                    'de': {'name': 'Pronomen', 'abbreviation': 'pron.'},
                    'it': {'name': 'Pronome', 'abbreviation': 'pron.'},
                    'pt': {'name': 'Pronome', 'abbreviation': 'pron.'},
                    'zh': {'name': '代词', 'abbreviation': '代'},
                    'ja': {'name': '代名詞', 'abbreviation': '代'},
                    'ko': {'name': '대명사', 'abbreviation': '대'},
                }
            },
            'preposition': {
                'description': 'A word governing, and usually preceding, a noun or pronoun and expressing a relation to another word',
                'translations': {
                    'en': {'name': 'Preposition', 'abbreviation': 'prep.'},
                    'ru': {'name': 'Предлог', 'abbreviation': 'предл.'},
                    'es': {'name': 'Preposición', 'abbreviation': 'prep.'},
                    'fr': {'name': 'Préposition', 'abbreviation': 'prép.'},
                    'de': {'name': 'Präposition', 'abbreviation': 'präp.'},
                    'it': {'name': 'Preposizione', 'abbreviation': 'prep.'},
                    'pt': {'name': 'Preposição', 'abbreviation': 'prep.'},
                    'zh': {'name': '介词', 'abbreviation': '介'},
                    'ja': {'name': '前置詞', 'abbreviation': '前'},
                    'ko': {'name': '전치사', 'abbreviation': '전'},
                }
            },
            'conjunction': {
                'description': 'A word used to connect clauses or sentences or to coordinate words in the same clause',
                'translations': {
                    'en': {'name': 'Conjunction', 'abbreviation': 'conj.'},
                    'ru': {'name': 'Союз', 'abbreviation': 'союз'},
                    'es': {'name': 'Conjunción', 'abbreviation': 'conj.'},
                    'fr': {'name': 'Conjonction', 'abbreviation': 'conj.'},
                    'de': {'name': 'Konjunktion', 'abbreviation': 'konj.'},
                    'it': {'name': 'Congiunzione', 'abbreviation': 'cong.'},
                    'pt': {'name': 'Conjunção', 'abbreviation': 'conj.'},
                    'zh': {'name': '连词', 'abbreviation': '连'},
                    'ja': {'name': '接続詞', 'abbreviation': '接'},
                    'ko': {'name': '접속사', 'abbreviation': '접'},
                }
            },
            'interjection': {
                'description': 'An abrupt remark, made especially as an aside or interruption',
                'translations': {
                    'en': {'name': 'Interjection', 'abbreviation': 'interj.'},
                    'ru': {'name': 'Междометие', 'abbreviation': 'межд.'},
                    'es': {'name': 'Interjección', 'abbreviation': 'interj.'},
                    'fr': {'name': 'Interjection', 'abbreviation': 'interj.'},
                    'de': {'name': 'Interjektion', 'abbreviation': 'interj.'},
                    'it': {'name': 'Interiezione', 'abbreviation': 'inter.'},
                    'pt': {'name': 'Interjeição', 'abbreviation': 'interj.'},
                    'zh': {'name': '感叹词', 'abbreviation': '感'},
                    'ja': {'name': '感嘆詞', 'abbreviation': '感'},
                    'ko': {'name': '감탄사', 'abbreviation': '감'},
                }
            },
            'article': {
                'description': 'A particular item or object, typically one of a specified type',
                'translations': {
                    'en': {'name': 'Article', 'abbreviation': 'art.'},
                    'ru': {'name': 'Артикль', 'abbreviation': 'арт.'},
                    'es': {'name': 'Artículo', 'abbreviation': 'art.'},
                    'fr': {'name': 'Article', 'abbreviation': 'art.'},
                    'de': {'name': 'Artikel', 'abbreviation': 'art.'},
                    'it': {'name': 'Articolo', 'abbreviation': 'art.'},
                    'pt': {'name': 'Artigo', 'abbreviation': 'art.'},
                    'zh': {'name': '冠词', 'abbreviation': '冠'},
                    'ja': {'name': '冠詞', 'abbreviation': '冠'},
                    'ko': {'name': '관사', 'abbreviation': '관'},
                }
            },
            'numeral': {
                'description': 'A figure, symbol, or group of these denoting a number',
                'translations': {
                    'en': {'name': 'Numeral', 'abbreviation': 'num.'},
                    'ru': {'name': 'Числительное', 'abbreviation': 'числ.'},
                    'es': {'name': 'Numeral', 'abbreviation': 'num.'},
                    'fr': {'name': 'Numéral', 'abbreviation': 'num.'},
                    'de': {'name': 'Numerale', 'abbreviation': 'num.'},
                    'it': {'name': 'Numerale', 'abbreviation': 'num.'},
                    'pt': {'name': 'Numeral', 'abbreviation': 'num.'},
                    'zh': {'name': '数词', 'abbreviation': '数'},
                    'ja': {'name': '数詞', 'abbreviation': '数'},
                    'ko': {'name': '수사', 'abbreviation': '수'},
                }
            }
        }

        # Получаем все доступные языки
        languages = {lang.code: lang for lang in Language.objects.all()}

        if not languages:
            self.stdout.write(
                self.style.WARNING('Не найдено ни одного языка в базе данных. Сначала создайте языки.')
            )
            return

        created_count = 0
        translation_count = 0

        with transaction.atomic():
            for code, data in parts_of_speech_data.items():
                # Создаем или получаем часть речи
                part_of_speech, created = PartOfSpeech.objects.get_or_create(
                    code=code,
                    defaults={
                        'description': data['description'],
                        'enabled': True
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'Создана часть речи: {code}')
                else:
                    self.stdout.write(f'Часть речи уже существует: {code}')

                # Создаем переводы для всех доступных языков
                for lang_code, translation_data in data['translations'].items():
                    if lang_code in languages:
                        translation, created = PartOfSpeechTranslation.objects.get_or_create(
                            part_of_speech=part_of_speech,
                            language=languages[lang_code],
                            defaults={
                                'name': translation_data['name'],
                                'abbreviation': translation_data['abbreviation']
                            }
                        )

                        if created:
                            translation_count += 1
                            self.stdout.write(
                                f'  Создан перевод: {lang_code} - {translation_data["name"]}'
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  Язык {lang_code} не найден в базе данных')
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано {created_count} частей речи и {translation_count} переводов'
            )
        )
