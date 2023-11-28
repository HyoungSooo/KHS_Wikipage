from ninja import NinjaAPI
from django.urls import path
from api.schemas import *
from post.models import Post
from typing import List, Dict
from django.db import connection
from collections import defaultdict, deque

api = NinjaAPI()


@api.get('/post', response={200: List[PostOut], 204: Message})
def get_post_list(request):
    data = Post.objects.all()

    if data.exists():
        return 200, data.values()

    return 204, {"message": "No content"}


@api.post('/post', response={200: PostOut, 400: Message})
def create_post(request, payload: PostCreate):
    try:
        return 200, Post.objects.create(title=payload.title, content=payload.content)
    except:
        return 400, {'message': 'Bad Request'}


@api.get('/post/detail', response={200: PostDetail, 204: Message})
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
        NOT IN (SELECT w.id
          FROM post_word as w 
          JOIN post_post_word as pw
          ON w.id = pw.word_id
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


@api.get('/word/map')
def create_word_map(request, start: str):
    '''
    마지막 문항인 과제 맵을 생성하는 API입니다. DFS알고리즘을 이용해서 단어들의 이동경로를 파악했습니다.
    '''
    sql = '''
      SELECT pw.post_id, w.word 
      FROM post_post_word as pw 
      JOIN post_word as w 
      ON w.id = pw.word_id 
      WHERE pw.word_id IN (
        SELECT word_id 
        FROM post_post_word 
        GROUP BY word_id 
        HAVING Count(word_id) > 1); 
    '''
    cursor = connection.cursor()
    cursor.execute(sql)
    result: List = cursor.fetchall()

    word_dict = defaultdict(list)

    for post, word in result:
        word_dict[word].append(post)
        word_dict[post].append(word)

    stack = deque(list(map(lambda x: (x, start), word_dict.get(start))))
    visited = set([start])
    mapping = []

    while stack:
        post, word = stack.pop()

        for next_word in word_dict.get(post):
            if next_word in visited:
                continue
            mapping.append((word, next_word))
            stack.extend(
                list(map(lambda x: (x, next_word), word_dict.get(next_word))))
            visited.add(next_word)

    return mapping


urlpatterns = [
    path('api/', api.urls)
]
