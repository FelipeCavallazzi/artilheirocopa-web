import requests
import io
import random
import pandas as pd

BASE_URL = "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/"

_cache = {}


def _load_csv(filename: str) -> pd.DataFrame:
    if filename in _cache:
        return _cache[filename]
    print(f"Baixando {filename}...")
    r = requests.get(BASE_URL + filename, timeout=15)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    _cache[filename] = df
    return df


def _get_quarterfinal_teams() -> dict[int, set]:
    matches = _load_csv("matches.csv")
    matches = matches[matches["tournament_name"].str.contains("Men's", na=False)]
    matches = matches[matches["tournament_id"] >= "WC-1958"]

    teams_per_year = {}

    for _, row in matches.iterrows():
        year = int(row["tournament_id"].split("-")[1])
        stage = row["stage_name"].lower()

        # Copas com quartas de final normais
        if "quarter" in stage:
            teams_per_year.setdefault(year, set())
            teams_per_year[year].add(row["home_team_name"])
            teams_per_year[year].add(row["away_team_name"])

        # 1974 e 1978: segunda fase de grupos (equivalente às quartas)
        elif year in (1974, 1978) and "second group stage" in stage:
            teams_per_year.setdefault(year, set())
            teams_per_year[year].add(row["home_team_name"])
            teams_per_year[year].add(row["away_team_name"])

        # 1982: semifinal
        elif year == 1982 and "semi" in stage:
            teams_per_year.setdefault(year, set())
            teams_per_year[year].add(row["home_team_name"])
            teams_per_year[year].add(row["away_team_name"])

    return teams_per_year


def build_top_scorers(difficulty: str = "hard") -> list[dict]:
    goals  = _load_csv("goals.csv")
    squads = _load_csv("squads.csv")

    goals = goals[goals["tournament_name"].str.contains("Men's", na=False)]
    goals = goals[goals["tournament_id"] >= "WC-1958"]
    goals = goals[goals["own_goal"] == 0].copy()

    goals["year"] = goals["tournament_id"].str.extract(r"(\d{4})").astype(int)

    def full_name(row):
        given = row["given_name"] if row["given_name"] != "not applicable" else ""
        return f"{given} {row['family_name']}".strip()

    goals["player_name"] = goals.apply(full_name, axis=1)

    grouped = (
        goals.groupby(["year", "player_team_name", "player_team_code", "player_id", "player_name"])
        .size()
        .reset_index(name="goals")
    )

    if difficulty == "easy":
        qf_teams = _get_quarterfinal_teams()
        def in_quarterfinals(row):
            return row["player_team_name"] in qf_teams.get(row["year"], set())
        grouped = grouped[grouped.apply(in_quarterfinals, axis=1)]

    result = []
    for (year, team), group in grouped.groupby(["year", "player_team_name"]):
        group_sorted = group.sort_values("goals", ascending=False)
        correct = group_sorted.iloc[0]

        options = group_sorted[["player_name"]].to_dict(orient="records")[:4]

        if len(options) < 4:
            squad = squads[
                (squads["tournament_id"] == f"WC-{year}") &
                (squads["team_name"] == team)
            ].copy()
            squad["player_name"] = squad.apply(full_name, axis=1)

            already = set(o["player_name"] for o in options)
            extras = [
                {"player_name": name}
                for name in squad["player_name"].tolist()
                if name not in already
            ]
            random.shuffle(extras)
            options += extras[:4 - len(options)]

        result.append({
            "year": int(year),
            "team": team,
            "team_code": correct["player_team_code"],
            "player_id": correct["player_id"],
            "player_name": correct["player_name"],
            "goals": int(correct["goals"]),
            "options": options,
        })

    return result


def get_question(data: list[dict]) -> dict:
    entry = random.choice(data)
    options = entry["options"][:]
    random.shuffle(options)

    return {
        "year": entry["year"],
        "team": entry["team"],
        "correct_name": entry["player_name"],
        "goals": entry["goals"],
        "options": options,
    }