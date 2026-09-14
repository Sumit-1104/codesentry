from django.db import models
from django.contrib.auth.models import User
import json


class AnalysisHistory(models.Model):
    """
    Ye model har analysis ka record store karta hai:
    kis user ne, kab, kya analyze kiya, aur result kya tha.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_name = models.CharField(max_length=255)  # file naam ya GitHub URL
    results_json = models.TextField()  # poora result JSON string ke roop mein
    created_at = models.DateTimeField(auto_now_add=True)

    def get_results(self):
        """JSON string ko wapas Python list mein convert karta hai."""
        return json.loads(self.results_json)

    def __str__(self):
        return f"{self.source_name} — {self.user.username} ({self.created_at})"

    class Meta:
        ordering = ["-created_at"]  # Sabse naya sabse upar