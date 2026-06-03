from django.db import models


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    job_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class InterviewResponse(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="responses")
    question = models.TextField()
    answer = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.candidate.name}: {self.score if self.score is not None else 'pending'}"


class RegisteredUser(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.email
