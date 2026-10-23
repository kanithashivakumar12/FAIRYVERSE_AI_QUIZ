"""
Automated checks for FAIRYVERSE. Run with:  python test_quiz.py
(No pytest needed. Uses Streamlit's built-in AppTest to drive the real app.)
"""
from streamlit.testing.v1 import AppTest

import app

PASS = []


def check(cond, msg):
    assert cond, f"FAILED: {msg}"
    PASS.append(msg)
    print(f"ok  - {msg}")


# ---------------------------------------------------------------- data + grading
check(len(app.QUESTIONS) == 50, "exactly 50 questions")
check([q["id"] for q in app.QUESTIONS] == list(range(1, 51)), "ids run 1..50 in order")
check(app.validate_bank() == [], "question bank validates with no problems")
check(sum(1 for q in app.QUESTIONS) == app.MAX_SCORE, "max possible score is 50")
types = {q["type"] for q in app.QUESTIONS}
check(types == set(app.TYPE_ORDER), "all seven question types are present")
check(all("answer" not in q for q in app.QUESTIONS), "answers are not stored in the visible question data")


def perfect_answers():
    ans = {}
    for q in app.QUESTIONS:
        k = app.ANSWER_KEY[q["id"]]
        ans[q["id"]] = k["answer"] if q["type"] != "fill" else k["answer"]
    return ans


res = app.compute_results(perfect_answers())
check(res["score"] == 50 and res["pct"] == 100.0, "perfect answers score 50/50 = 100%")
check(app.compute_results({})["score"] == 0 and app.compute_results({})["counts"]["unanswered"] == 50,
      "no answers score 0 with 50 unanswered")

wrong = {}
for q in app.QUESTIONS:
    t = q["type"]
    if t in app.CHOICE_TYPES:
        right = app.ANSWER_KEY[q["id"]]["answer"]
        wrong[q["id"]] = next(k for k in q["options"] if k != right)
    elif t == "fill":
        wrong[q["id"]] = "banana"
    else:
        key = app.ANSWER_KEY[q["id"]]["answer"]
        wrong[q["id"]] = {i: next(c for c in q["choices"] if c != key[i]) for i in key}
check(app.compute_results(wrong)["score"] == 0, "all-wrong answers score 0")

q36 = app.QBY_ID[36]
pts, status = app.grade(q36, {1: "B", 2: "A", 3: "A"})
check(abs(pts - 2 / 3) < 1e-9 and status == "partial", "matching gives proportional credit (2 of 3 pairs)")
check(app.grade(q36, {1: "B", 2: "A", 3: "C"})[0] == 1.0, "matching capped at exactly 1 point")
check(app.grade(q36, {})[1] == "unanswered", "empty matching counts as unanswered")

fills = {31: ["Sensors", "  sensor ", "SENSORS."], 32: ["iterative deepening", "Iterative-Deepening Search", "IDS"],
         33: ["goal", "the Goal", "Goal state"], 34: ["DOMAIN", " domain  "],
         35: ["means end analysis", "Means-End Analysis", "means - end   analysis"]}
for qid, variants in fills.items():
    for v in variants:
        check(app.grade(app.QBY_ID[qid], v)[0] == 1.0, f"Q{qid} accepts {v!r}")
for qid, bad in [(31, "actuators"), (32, "breadth first search"), (33, "start"), (34, "range"), (35, "hill climbing"), (33, "   ")]:
    check(app.grade(app.QBY_ID[qid], bad)[0] == 0.0, f"Q{qid} rejects {bad!r}")

check(app.performance_message(90).startswith("Stardust Supreme"), "90% message")
check(app.performance_message(89.9).startswith("Fairy Scholar") and app.performance_message(75).startswith("Fairy Scholar"), "75-89% message")
check(app.performance_message(74.9).startswith("Growing Your Wings") and app.performance_message(50).startswith("Growing Your Wings"), "50-74% message")
check(app.performance_message(49.9).startswith("Your Journey Has Just Begun"), "below 50% message")

# independent re-derivation of answer key against the supplied brief
expected_mcq = dict(zip(range(1, 21), [
    "B", "B", "B", "B", "B", "A", "A", "B", "B", "B", "B", "B", "A", "A", "B", "A", "A", "A", "A", "A"]))
for qid, letter in expected_mcq.items():
    check(app.ANSWER_KEY[qid]["answer"] == letter, f"Q{qid} key matches the brief ({letter})")
expected_rest = {21: "False", 22: "True", 23: "True", 24: "False", 25: "True",
                 26: "A", 27: "A", 28: "A", 29: "D", 30: "A",
                 41: "A", 42: "B", 43: "A", 44: "A", 45: "A", 46: "A", 47: "A", 48: "B", 49: "C", 50: "C"}
for qid, a in expected_rest.items():
    check(app.ANSWER_KEY[qid]["answer"] == a, f"Q{qid} key matches the brief ({a})")
expected_match = {36: {1: "B", 2: "A", 3: "C"}, 37: {1: "B", 2: "C", 3: "A"}, 38: {1: "C", 2: "B", 3: "A"},
                  39: {1: "B", 2: "C", 3: "A"}, 40: {1: "C", 2: "B", 3: "A"}}
for qid, m in expected_match.items():
    check(app.ANSWER_KEY[qid]["answer"] == m, f"Q{qid} matching key matches the brief")

# Q46 BFS, worked independently from the tree
from collections import deque
tree = {"S": ["A", "B"], "A": ["G"], "B": ["C"], "G": [], "C": []}
dq, removed = deque(["S"]), []
while dq:
    n = dq.popleft()
    removed.append(n)
    if n == "G":
        break
    dq.extend(tree[n])
check(", ".join(removed) == app.QBY_ID[46]["options"]["A"], "Q46: simulated BFS removal order equals option A")
edges = {"S": ["A", "B"], "A": ["S", "G"], "B": ["S", "C"], "C": ["B", "G"], "G": ["A", "C"]}
dist = {"S": 0}
dq = deque(["S"])
while dq:
    n = dq.popleft()
    for m in edges[n]:
        if m not in dist:
            dist[m] = dist[n] + 1
            dq.append(m)
check(dist["G"] == 2, "Q47: shortest S->G has 2 edges (S-A-G)")
check(all(c in app.QBY_ID[50]["options"]["C"] for c in "A = 1, B = 2, C = 3"), "Q50 option C is the valid assignment")
opts50 = {"A": (1, 1, 2), "B": (1, 2, 2), "C": (1, 2, 3), "D": (3, 3, 3)}
valid = [k for k, (a, b, c) in opts50.items() if a != b and b != c]
check(valid == ["C"], "Q50: only option C satisfies both constraints")

# ---------------------------------------------------------------- UI flow


def new_app():
    at = AppTest.from_file("app.py", default_timeout=60).run()
    check(not at.exception, "app starts without exception")
    return at


def to_quiz(at, name="Tester"):
    at.button(key="start_home").click().run()
    at.text_input(key="name_input").set_value(name).run()
    at.button(key="start_setup").click().run()
    at.button(key="start_instr").click().run()
    check(at.session_state.page == "quiz", "reached the quiz page")
    return at


def answer_current(at, ans):
    q = app.QUESTIONS[at.session_state.current]
    qid, t = q["id"], q["type"]
    a = ans.get(qid)
    if a is None:
        return
    if t in app.CHOICE_TYPES:
        at.radio(key=f"w_{qid}").set_value(a)
    elif t == "fill":
        at.text_input(key=f"w_{qid}").set_value(a)
    else:
        for i, v in a.items():
            at.selectbox(key=f"w_{qid}_{i}").set_value(v)
    at.run()


at = new_app()
# empty name is rejected
at.button(key="start_home").click().run()
at.button(key="start_setup").click().run()
check(at.session_state.page == "setup" and len(at.error) == 1, "empty name is rejected with a message")
at.text_input(key="name_input").set_value("Kanitha").run()
at.button(key="start_setup").click().run()
check(at.session_state.page == "instructions", "valid name moves to instructions")
at.button(key="start_instr").click().run()

# persistence across navigation
answer_current(at, {1: "B"})
at.button(key="next_btn").click().run()
check(at.session_state.current == 1, "Next moves to Q2")
at.button(key="prev_btn").click().run()
check(at.radio(key="w_1").value == "B", "Q1 answer is still selected after Previous")
check(at.session_state.answers == {1: "B"}, "answers dict holds only what was answered")

# hint
at.button(key="hint_1").click().run()
check(1 in at.session_state.hints_shown, "hint reveals on click")

# correct answer never appears on the quiz page before submission
page_text = " ".join(m.value for m in at.markdown)
check("Correct answer" not in page_text and "Explanation" not in page_text, "no answers or explanations shown mid-quiz")

# full perfect run
at = to_quiz(new_app())
perfect = perfect_answers()
for n in range(app.N):
    answer_current(at, perfect)
    check(not at.exception, f"Q{n + 1} answered without exception") if n in (0, 15, 30, 35, 49) else None
    if n < app.N - 1:
        at.button(key="next_btn").click().run()
check(at.session_state.current == 49, "reached Q50")
at.button(key="submit_main").click().run()
check(at.session_state.page == "confirm", "Submit opens the confirmation page")
at.button(key="submit_final").click().run()
check(at.session_state.page == "results" and not at.exception, "results page renders")
check(at.session_state.results["score"] == 50, "UI run with correct answers scores 50")
check(any("Stardust Supreme" in m.value for m in at.markdown), "top performance message is shown")
check(len(at.expander) == 0, "review shows nothing to revisit when everything is correct")
at.radio(key="review_filter").set_value("All questions").run()
check(len(at.expander) == 50, "'All questions' lists all 50 review items")
at.button(key="start_again").click().run()
check(at.session_state.page == "setup" and at.session_state.answers == {}, "Try Again clears answers")

# submit with nothing answered
at = to_quiz(new_app())
at.button(key="submit_side").click().run()
check(at.session_state.page == "confirm", "sidebar submit works from any question")
at.button(key="submit_final").click().run()
r = at.session_state.results
check(r["score"] == 0 and r["counts"]["unanswered"] == 50, "submitting with no answers is safe and scores 0")
check(len(at.expander) == 50, "all 50 unanswered questions are listed for review")
at.button(key="restart_return").click().run()
check(at.session_state.page == "home" and at.session_state.results is None, "Return to the Fairy Realm resets")

# partial run: restart mid-quiz
at = to_quiz(new_app())
answer_current(at, {1: "B"})
at.button(key="restart_side").click().run()
at.button(key="restart_yes").click().run()
check(at.session_state.answers == {} and at.session_state.current == 0, "Restart clears answers and returns to Q1")
check(at.radio(key="w_1").value is None, "Q1 widget is empty after restart")

# Stardust difficulty disables hints
at = new_app()
at.button(key="start_home").click().run()
at.text_input(key="name_input").set_value("Hintless").run()
at.radio(key="diff_input").set_value("Stardust").run()
at.button(key="start_setup").click().run()
at.button(key="start_instr").click().run()
check(not any(b.key == "hint_1" for b in at.button), "no hint button on Stardust difficulty")

# every question renders without exception
at = to_quiz(new_app())
for n in range(app.N):
    check(not at.exception, f"Q{n + 1} renders") if n % 7 == 0 else None
    assert not at.exception, f"Q{n + 1} raised {at.exception}"
    if n < app.N - 1:
        at.button(key="next_btn").click().run()
print(f"\nAll {len(PASS)} checks passed.")
