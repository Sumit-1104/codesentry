import os
import sys

def calculate_total(a,b,c):
    x = 10
    total = a+b+c
    return total

class userManager:
    def __init__(self):
        self.users = []
    def add_user(self, name):
        self.users.append(name)