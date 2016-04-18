from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
import random

class Account(models.Model):
    cardNum = ''
    for i in range(16):
        cardNum += str(random.randint(0, 9))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_num = models.CharField(max_length=16, default=cardNum)
    checking_balance = models.IntegerField(default=0)
    saving_balance = models.IntegerField(default=0)
    card_activated = models.BooleanField(default=False)
    card_pin = models.CharField(max_length=4)

    def __str__(self):
        return self.card_num
