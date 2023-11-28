from collections.abc import Iterable
from django.db import models
from post.utils import get_words

# Create your models here.


class Post(models.Model):
    title = models.TextField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    word = models.ManyToManyField('Word', related_name='post')

    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)
        words = get_words(self.content)
        for word in words:
            word.replace('"', '')
            data = Word.objects.get_or_create(word=word)[0]
            self.word.add(data)

        return self


class Word(models.Model):
    word = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['word']),
        ]
