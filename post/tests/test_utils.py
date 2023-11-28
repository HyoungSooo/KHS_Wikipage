from post.utils import extraction_nouns, get_words
from django.test import TestCase
from kiwipiepy import Token


class TestUtils(TestCase):
    @classmethod
    def setUpTestData(self):
        self.text = "안녕하세요 형태소 분석기 키위입니다."

    def test_extraction_nouns(self):
        res = extraction_nouns(self.text)

        self.assertEqual(len(res), 10)

    def test_get_words(self):
        res = get_words(self.text)

        self.assertEqual(res, ['안녕', '형태소', '분석기', '키위'])
