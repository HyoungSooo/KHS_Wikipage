from django.test import TestCase
from post.models import Post, Word


class TestModels(TestCase):
    @classmethod
    def setUpTestData(self):
        self.data = {"title": "test_post", "content": "안녕하세요 형태소 분석기 키위입니다."}

    def test_post_create(self):
        '''
        save 함수가 실행될 때 자동으로 word 객체와 연관지어지는지 테스트
        '''
        data = Post.objects.create(**self.data)

        self.assertEqual(data, Post.objects.first())

        self.assertEqual(data.word.count(), 4)
