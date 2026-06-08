from django.shortcuts import render, redirect
from django.http import HttpRequest
from data_loader import build_top_scorers, get_question

# Carrega os dados uma vez quando o servidor inicia
_data_cache = {}


def _get_data(difficulty: str) -> list:
    if difficulty not in _data_cache:
        _data_cache[difficulty] = build_top_scorers(difficulty=difficulty)
    return _data_cache[difficulty]


def index(request: HttpRequest):
    data_hard = _get_data("hard")
    anos = sorted(set(d["year"] for d in data_hard))
    return render(request, "game/index.html", {
        "ano_min": anos[0],
        "ano_max": anos[-1],
        "anos": anos,
        "last_difficulty": request.session.get("difficulty", "hard"),
        "last_ano_de": request.session.get("ano_de", anos[0]),
        "last_ano_ate": request.session.get("ano_ate", anos[-1]),
    })


def start(request: HttpRequest):
    """Recebe as escolhas do formulário e inicia a sessão do jogo."""
    if request.method != "POST":
        return redirect("index")

    difficulty = request.POST.get("difficulty", "hard")
    ano_de     = int(request.POST.get("ano_de", 1958))
    ano_ate    = int(request.POST.get("ano_ate", 2022))

    data = _get_data(difficulty)
    filtrado = [d for d in data if ano_de <= d["year"] <= ano_ate]

    if not filtrado:
        return redirect("index")

    # Salvar estado do jogo na sessão
    request.session["difficulty"] = difficulty
    request.session["ano_de"]     = ano_de
    request.session["ano_ate"]    = ano_ate
    request.session["score"]      = 0
    request.session["round"]      = 0

    return redirect("question")


def question(request: HttpRequest):
    """Sorteia e exibe a próxima pergunta."""
    difficulty = request.session.get("difficulty", "hard")
    ano_de     = request.session.get("ano_de", 1958)
    ano_ate    = request.session.get("ano_ate", 2022)

    data = _get_data(difficulty)
    filtrado = [d for d in data if ano_de <= d["year"] <= ano_ate]

    q = get_question(filtrado)

    # Salvar a pergunta atual na sessão para verificar a resposta
    request.session["current_question"] = q

    return render(request, "game/question.html", {
        "question": q,
        "round": request.session.get("round", 0) + 1,
        "score": request.session.get("score", 0),
        "letters": ["A", "B", "C", "D"],
    })


def answer(request: HttpRequest):
    """Recebe a resposta, verifica e redireciona."""
    if request.method != "POST":
        return redirect("question")

    chosen_name = request.POST.get("player_name")
    q           = request.session.get("current_question")

    if not q:
        return redirect("index")

    is_correct = chosen_name == q["correct_name"]

    request.session["round"] = request.session.get("round", 0) + 1
    if is_correct:
        request.session["score"] = request.session.get("score", 0) + 1

    request.session["last_result"] = {
        "is_correct":   is_correct,
        "correct_name": q["correct_name"],
        "goals":        q["goals"],
        "team":         q["team"],
        "year":         q["year"],
        "chosen_name":  chosen_name,
    }

    return redirect("result")


def result(request: HttpRequest):
    """Exibe o resultado da rodada e pergunta se quer continuar."""
    last = request.session.get("last_result")
    if not last:
        return redirect("index")

    return render(request, "game/result.html", {
        "result":  last,
        "round":   request.session.get("round", 0),
        "score":   request.session.get("score", 0),
    })


def gameover(request: HttpRequest):
    """Tela de fim de jogo."""
    return render(request, "game/gameover.html", {
        "round": request.session.get("round", 0),
        "score": request.session.get("score", 0),
    })