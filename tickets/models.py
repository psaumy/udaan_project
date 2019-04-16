import jsonfield as jsonfield
from django.db import models

# Create your models here.


class Screen(models.Model):
    name = models.TextField(max_length=50, unique=True, blank=False, null=False)
    seats = jsonfield.JSONField()


    def __str__(self):
        return self.name

    @staticmethod
    def list_screen():
        screens =  Screen.objects.all()
        resp = []
        for s in screens:
            resp.append({
                'name' : s.name,
                # 'seats' : s.seats,
            })
        return resp
