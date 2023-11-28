from django.db import connection
from typing import List, Dict
from django.test import TestCase
from ninja.testing import TestClient
from ninja.router import Router

from post.models import *
from api.schemas import *

import json

from typing import List

import csv

router = Router()


@router.get('/test1', response={200: List[PostOut], 204: Message})
def get_post_list(request):
    data = Post.objects.all()

    if data.exists():
        return 200, data.values()

    return 204, {"message": "No content"}


@router.post('/test1', response={200: PostOut, 400: Message})
def create_post(request, payload: PostCreate):
    try:
        return 200, Post.objects.create(title=payload.title, content=payload.content)
    except:
        return 400, {'message': 'Bad Request'}


@router.get('/test/detail', response={200: PostDetail, 204: Message})
def get_post_detail(request, pk: int):
    count = int(Post.objects.count() * 0.4)
    sql = f'''
      SELECT p.title, p.created_at, pw.post_id, Count(*) 
      FROM post_post_word as pw 
      JOIN post_post as p
      ON pw.post_id = p.id
      WHERE pw.word_id 
      IN (SELECT w.word_id
        FROM post_post as p 
        JOIN post_post_word as w 
        ON w.post_id = p.id 
        WHERE p.id = {pk} 
        AND w.word_id
        NOT IN (SELECT pw.id
          FROM post_post_word as pw
          GROUP BY pw.word_id
          HAVING Count(pw.word_id) >= {count})
      ) AND pw.post_id != {pk}
      GROUP BY pw.post_id
      HAVING Count(*) > 1
      ORDER BY Count(*) DESC;
    '''
    cursor = connection.cursor()
    cursor.execute(sql)
    result: List[Dict] = cursor.fetchall()
    formatted_result = list(
        map(lambda x: {'id': x[2], 'title': x[0], 'created_at': x[1]}, result))
    try:
        post_data = dict(Post.objects.values().get(id=pk))
    except:
        return 204, {'message': 'No Content'}

    post_data.update({'rel_post': formatted_result})
    return 200, post_data


def create_data(data):
    return Post.objects.create(**data)


def create_data_more_than_one(data):
    for d in data:
        Post.objects.create(**d)


class TestAPI(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(router)
        return super().setUp()

    @classmethod
    def setUpTestData(self):
        self.data = {"title": "test_post", "content": "안녕하세요 형태소 분석기 키위입니다."}
        self.data_list = []

    def test_get_post_list_api(self):
        # 포스트가 없을 때 204를 반환하는가
        res = self.client.get('/test1')
        self.assertEqual(res.status_code, 204)

        # 포스트가 있을 때 200을 반환하는가
        create_data(self.data)
        res = self.client.get('/test1')
        self.assertEqual(res.status_code, 200)
        # 포스트를 반환하는지 확인
        data = json.loads(res.content)
        self.assertEqual(len(data), 1)

    def test_get_post_detail(self):
        # 포스트가 없으면 204를 반환하는가
        res = self.client.get('/test/detail?pk=1')
        self.assertEqual(res.status_code, 204)
        # 포스트가 있으면 200을 반환하는가
        create_data(self.data)
        res = self.client.get('/test/detail?pk=1')
        self.assertEqual(res.status_code, 200)

    def test_get_related_post(self):
        '''
        연관 포스트가 생성되는 로직과 쿼리를 검증합니다.
        여기서 포스트가 생성될 때 연관 포스트가 생성되는 로직을 테스트함으로 밑에 테스트에서 데이터베이스에 저장하는 API만 테스트합니다.
        '''
        # 더미 데이터 10개 생성
        dummy_data_list = [{'title': f'test{i}', 'content': '더미 내용'}
                           for i in range(10)]
        # 관계가 맺어질 데이터 생성
        dummy_data_list.append(
            {'title': 'related_content', 'content': '안녕하세요 명사 분석기 키위입니다.'})
        create_data_more_than_one(dummy_data_list)

        # 테스트 데이터 생성
        query_data = create_data(self.data)

        # 데이터 반환 성공
        res = self.client.get(f'/test/detail?pk={query_data.id}')
        self.assertEqual(res.status_code, 200)

        res_data = json.loads(res.content)
        # 연관 포스트가 하나인지 확인
        self.assertEqual(len(res_data.get('rel_post')), 1)
        self.assertEqual(res_data.get('rel_post')[0].get(
            'title'), 'related_content')

        # 이 포스트가 생성되면 총 13개의 포스트 중 11개의 포스트에 더미라는 단어가 들어가게 됩니다.
        # 60% 조건에 어긋남으로 연관지어지지 않는지 테스트
        check_60_payload = {
            'title': '60퍼 넘은 단어가 연관으로 넘어오는가 테스트',
            'content': '더미 내용 키위 분석기'
        }

        query_data = create_data(check_60_payload)

        _60_res = self.client.get(f'/test/detail?pk={query_data.id}')
        # 데이터 생성 성공
        self.assertEqual(res.status_code, 200)

        data_60_res = json.loads(_60_res.content)
        # 더미 단어가 들어간 포스트 까지 연관지어진다면 총 13개의 데이터가 연관지어져야합니다.
        # 키위 단어가 들어간 2개의 포스트만 연관지어짐으로 테스트 성공
        self.assertEqual(len(data_60_res.get('rel_post')), 2)

    def test_create_post(self):
        create_data(self.data)
        # 위의 테스트에서 포스트 연관 로직을 검사했음으로 데이터베이스에 저장하는 API만 테스트
        payload = {
            'title': '생성할 때 자동으로 연관 포스트가 연결되는가 테스트',
            'content': '키위 분석기 사과 바나나'
        }

        res = self.client.post(
            '/test1', json=payload, content_type='application/json')

        self.assertEqual(res.status_code, 200)

        data = json.loads(res.content)

        self.assertEqual(data.get('title'), payload.get('title'))

        check_rel_post = Post.objects.get(id=data.get('id'))

        self.assertTrue(check_rel_post.word.count())
