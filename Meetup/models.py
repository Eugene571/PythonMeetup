from django.db import models
from django.utils.timezone import now

class Speaker(models.Model):
    """Модель для представления докладчика."""
    name = models.CharField(max_length=255, verbose_name="Имя докладчика")
    bio = models.TextField(blank=True, verbose_name="Биография")
    contact = models.EmailField(blank=True, verbose_name="Контактный email")

    def __str__(self):
        return self.name

class Question(models.Model):
    """Модель для представления вопросов к докладчикам."""
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE, related_name="questions", verbose_name="Докладчик")
    text = models.TextField(verbose_name="Текст вопроса")
    user_name = models.CharField(max_length=255, verbose_name="Имя пользователя, задавшего вопрос")
    created_at = models.DateTimeField(default=now, verbose_name="Дата и время создания")
    is_answered = models.BooleanField(default=False, verbose_name="Ответ дан")

    def __str__(self):
        return f"Вопрос от {self.user_name} к {self.speaker}"

class Event(models.Model):
    """Модель для представления мероприятия."""
    title = models.CharField(max_length=255, verbose_name="Название мероприятия")
    description = models.TextField(blank=True, verbose_name="Описание мероприятия")
    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    speakers = models.ManyToManyField(Speaker, related_name="events", verbose_name="Докладчики")

    def __str__(self):
        return self.title


