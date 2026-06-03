import random
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import AnswerForm, CandidateForm
from .models import Candidate, InterviewResponse, RegisteredUser
from .ai_utils import evaluate_answer, format_evaluation_feedback, generate_question


otp_storage = {}


def index(request):
    return render(request, "index.html")


def home(request):
    return render(request, "index.html")


def user_homepage(request):
    if not request.session.get("registered_user_id"):
        return redirect(f"/user/login/?next={request.path}")
    return render(request, "user_home.html")





def register_view(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        if name and email and password:
            RegisteredUser.objects.update_or_create(
                email=email,
                defaults={"name": name, "password": password, "is_active": True},
            )
            messages.success(request, "Registration successful.")
            return redirect("UserLogin")
        messages.error(request, "Please fill all required fields.")
    return render(request, "register.html")


def user_login(request):

    # If already logged in
    if request.session.get("registered_user_id"):
        return redirect("UserHome")

    next_url = request.GET.get("next")  # capture requested page

    if request.method == "POST":
        next_url = request.POST.get("next") or next_url
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        user = RegisteredUser.objects.filter(
            email=email,
            password=password,
            is_active=True
        ).first()

        if user:
            request.session["registered_user_id"] = user.id
            messages.success(request, "Login successful.")

            # 🔥 redirect back to original page
            if next_url:
                return redirect(next_url)

            return redirect("UserHome")

        messages.error(request, "Invalid credentials.")

    return render(request, "user_login.html", {"next": next_url})




def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if username == "admin" and password == "admin":
            request.session["is_admin"] = True
            return redirect("admin_home")
        messages.error(request, "Invalid admin credentials.")
    return render(request, "admin_login.html")


def admin_home(request):
    if not request.session.get("is_admin"):
        return redirect("AdminLogin")
    users_count = RegisteredUser.objects.count()
    active_count = RegisteredUser.objects.filter(is_active=True).count()
    candidates_count = Candidate.objects.count()
    responses_count = InterviewResponse.objects.count()
    scores = list(InterviewResponse.objects.exclude(score=None).values_list("score", flat=True))
    average_score = round(sum(scores) / len(scores), 2) if scores else None
    context = {
        "users_count": users_count,
        "active_count": active_count,
        "candidates_count": candidates_count,
        "responses_count": responses_count,
        "average_score": average_score,
    }
    return render(request, "admin_home.html", context)


def admin_dashboard(request):
    if not request.session.get("is_admin"):
        return redirect("AdminLogin")
    users = RegisteredUser.objects.all().order_by("-created_at")
    candidates = Candidate.objects.prefetch_related("responses").order_by("-created_at")
    candidate_results = []

    for candidate in candidates:
        responses = list(candidate.responses.all().order_by("created_at"))
        scores = [item.score for item in responses if item.score is not None]
        average_score = round(sum(scores) / len(scores), 2) if scores else None
        candidate_results.append(
            {
                "candidate": candidate,
                "responses": responses,
                "average_score": average_score,
                "response_count": len(responses),
            }
        )

    return render(
        request,
        "admin_dashboard.html",
        {"users": users, "candidate_results": candidate_results},
    )


def user_logout(request):
    request.session.flush()
    logout(request)
    return redirect("home")


@require_POST
def start_interview(request):

    if not request.session.get("registered_user_id"):
        return JsonResponse({"ok": False, "error": "Login required"}, status=403)

    # 🔥 DIRECT DATA (NO FORM)
    name = request.POST.get("name")
    email = request.POST.get("email")
    role = request.POST.get("job_description")

    if not name or not email or not role:
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    candidate = Candidate.objects.create(
        name=name.strip(),
        email=email.strip(),
        job_description=role.strip(),
    )

    # 🔥 AI QUESTION
    question = generate_question(role)

    return JsonResponse({
        "ok": True,
        "candidate_id": candidate.id,
        "question": question
    })



@require_POST
def answer_question(request):

    # 🔒 Check if user logged in
    if not request.session.get("registered_user_id"):
        return JsonResponse({"ok": False, "error": "Login required"}, status=403)

    form = AnswerForm(request.POST)
    candidate_id = request.POST.get("candidate_id")

    if not candidate_id:
        return JsonResponse({"ok": False, "error": "candidate_id is required."}, status=400)

    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    candidate = get_object_or_404(Candidate, id=candidate_id)

    question = request.POST.get("question", "")
    answer = form.cleaned_data["answer"]

    evaluation = evaluate_answer(question, answer)
    score = evaluation["score"]
    feedback = format_evaluation_feedback(evaluation)

    response = InterviewResponse.objects.create(
        candidate=candidate,
        question=question,
        answer=answer,
        score=score,
        feedback=feedback,
    )

    return JsonResponse({
        "ok": True,
        "response_id": response.id,
        "score": score,
        "feedback": feedback,
        "evaluation": evaluation,
    })



def interview_results(request):
    candidate_id = request.GET.get("candidate_id")
    if not candidate_id:
        return JsonResponse({"ok": False, "error": "candidate_id query param is required."}, status=400)

    candidate = get_object_or_404(Candidate, id=candidate_id)
    responses = candidate.responses.all().order_by("created_at")
    scores = [item.score for item in responses if item.score is not None]
    data = [
        {
            "question": item.question,
            "answer": item.answer,
            "score": item.score,
            "feedback": item.feedback,
        }
        for item in responses
    ]
    return JsonResponse({
        "ok": True,
        "candidate": candidate.name,
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "responses": data,
    })


def all_results(request):
    payload = []
    for candidate in Candidate.objects.all().order_by("-created_at"):
        avg_score = candidate.responses.exclude(score=None).values_list("score", flat=True)
        avg = sum(avg_score) / len(avg_score) if avg_score else None
        payload.append(
            {
                "candidate_id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "job_description": candidate.job_description,
                "average_score": avg,
                "responses_count": candidate.responses.count(),
            }
        )
    return JsonResponse({"ok": True, "results": payload})


def activate_user(request, user_id):
    user = get_object_or_404(RegisteredUser, id=user_id)
    user.is_active = True
    user.save(update_fields=["is_active"])
    return redirect("admin_dashboard")


def deactivate_user(request, user_id):
    user = get_object_or_404(RegisteredUser, id=user_id)
    user.is_active = False
    user.save(update_fields=["is_active"])
    return redirect("admin_dashboard")


def delete_user(request, user_id):
    user = get_object_or_404(RegisteredUser, id=user_id)
    user.delete()
    return redirect("admin_dashboard")


def send_otp(request):
    email = request.POST.get("email", "").strip()
    if not email:
        messages.error(request, "Email is required.")
        return redirect("forgot_password")
    otp_storage[email] = str(random.randint(100000, 999999))
    messages.info(request, "OTP generated (development mode).")
    return redirect("verify_view")


def forgot_password(request):
    if request.method == "POST":
        return send_otp(request)
    return render(request, "reset_password.html")


def verify_otp(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        otp = request.POST.get("otp", "").strip()
        if otp_storage.get(email) == otp:
            request.session["reset_email"] = email
            messages.success(request, "OTP verified.")
            return redirect("reset_password")
        messages.error(request, "Invalid OTP.")
    return render(request, "reset_password.html")


def reset_password(request):
    if request.method == "POST":
        email = request.session.get("reset_email") or request.POST.get("email", "").strip()
        new_password = request.POST.get("password", "").strip()
        if not email or not new_password:
            messages.error(request, "Email and password are required.")
            return render(request, "reset_password.html")

        user = RegisteredUser.objects.filter(email=email).first()
        if not user:
            messages.error(request, "User not found.")
            return render(request, "reset_password.html")

        user.password = new_password
        user.save(update_fields=["password"])
        request.session.pop("reset_email", None)
        messages.success(request, "Password reset successful.")
        return redirect("UserLogin")

    return render(request, "reset_password.html")

@ensure_csrf_cookie
def interview_page(request):
    # allow only logged-in users
    if not request.session.get("registered_user_id"):
        return redirect("UserLogin")

    return render(request, "interview.html")
