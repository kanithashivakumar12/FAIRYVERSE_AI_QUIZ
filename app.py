"""
FAIRYVERSE: The Enchanted AI Quiz
A self-contained, offline Streamlit quiz for a BSc Data Science AI assignment.

Run with:  streamlit run app.py

Layout of this file
  1. Question bank (QUESTIONS) and answer key (ANSWER_KEY), kept separate
  2. Diagram builders (inline SVG, no external images)
  3. Grading and result building
  4. Theme (CSS + decorations)
  5. Pages: home, setup, instructions, quiz, confirm, results
"""

from __future__ import annotations

import difflib
import html
import re

import streamlit as st

MAX_SCORE = 50

# ======================================================================
# 1. QUESTION BANK  (edit freely; run `python test_quiz.py` afterwards)
# ======================================================================

TYPE_ORDER = ["mcq", "tf", "ar", "fill", "match", "scenario", "search"]
TYPE_INFO = {
    "mcq": ("Multiple Choice", "Section 1"),
    "tf": ("True or False", "Section 2"),
    "ar": ("Assertion & Reason", "Section 3"),
    "fill": ("Fill in the Blanks", "Section 4"),
    "match": ("Matching", "Section 5"),
    "scenario": ("Real-World Scenarios", "Section 6"),
    "search": ("Search & State Space", "Section 7"),
}
CHOICE_TYPES = {"mcq", "tf", "ar", "scenario", "search"}

AR_OPTIONS = {
    "A": "Both Assertion and Reason are true, and Reason correctly explains Assertion.",
    "B": "Both Assertion and Reason are true, but Reason does not correctly explain Assertion.",
    "C": "Assertion is true, but Reason is false.",
    "D": "Assertion is false, but Reason is true.",
}
TF_OPTIONS = {"True": "True", "False": "False"}

DIFFICULTIES = {
    "Dewdrop": {"hints": None, "blurb": "Gentle. Unlimited fairy hints."},
    "Moonbeam": {"hints": 10, "blurb": "Balanced. Up to 10 fairy hints."},
    "Stardust": {"hints": 0, "blurb": "Bold. No hints at all."},
}


def _letters(items):
    return {chr(65 + i): t for i, t in enumerate(items)}


def _q(qid, qtype, category, text, hint, options=None, **extra):
    d = {"id": qid, "type": qtype, "category": category, "text": text, "hint": hint}
    if options is not None:
        d["options"] = _letters(options) if isinstance(options, list) else options
    d.update(extra)
    return d


QUESTIONS = [
    # ---------------- Section 1: Multiple choice ----------------
    _q(1, "mcq", "AI Foundations",
       "Which statement best describes Artificial Intelligence?",
       "Focus on the word 'intelligence': doing something clever, not only storing or calculating.",
       ["A system that only stores large amounts of data",
        "A system that performs tasks requiring intelligent behaviour",
        "A system that only follows fixed mathematical formulas",
        "A system that replaces all human decisions"]),
    _q(2, "mcq", "Turing Test",
       "A chatbot gives responses that are indistinguishable from those of a human during a text conversation. Which concept is being tested?",
       "Think of Alan Turing's 'imitation game'.",
       ["Breadth-First Search", "Turing Test", "Constraint Satisfaction", "Hill Climbing"]),
    _q(3, "mcq", "Intelligent Agents",
       "An intelligent agent observes its environment and chooses actions to achieve goals. What is the main characteristic of a rational agent?",
       "Rational does not mean random, and it does not mean perfect. It is about expected performance.",
       ["It always selects a random action",
        "It chooses actions expected to maximize its performance measure",
        "It ignores information from sensors",
        "It follows the same action in every situation"]),
    _q(4, "mcq", "Sensors and Actuators",
       "In a self-driving car, which component detects nearby vehicles?",
       "Which part of an agent perceives, and which part acts?",
       ["Actuator", "Sensor", "Goal state", "Search operator"]),
    _q(5, "mcq", "Observability",
       "A robot receives incomplete information about obstacles because its camera cannot see around corners. What type of environment is this?",
       "Can the robot see everything relevant at the same moment?",
       ["Fully observable", "Partially observable", "Completely deterministic", "Fully decomposable"]),
    _q(6, "mcq", "Problem Space",
       "In AI problem-solving, what does a state space represent?",
       "Picture a map of every situation the problem could be in, plus the moves between them.",
       ["All possible states reachable or considered in a problem",
        "Only the final solution",
        "Only the initial state",
        "The memory used by the operating system"]),
    _q(7, "mcq", "Production Systems",
       "Which component of a production system contains IF-THEN rules?",
       "Condition-action pairs are stored together in one named component.",
       ["Rule base", "Sensor array", "Goal stack only", "Evaluation chart"]),
    _q(8, "mcq", "Decomposability",
       "A large AI problem can be divided into smaller independent subproblems and solved separately. Which property does it demonstrate?",
       "Splitting a big problem into independent pieces has its own name.",
       ["Partial observability", "Decomposability", "Randomness", "Local maximum"]),
    _q(9, "mcq", "Search Strategy",
       "Which factor is important when selecting a search algorithm?",
       "Ask what actually makes one algorithm better than another for a task.",
       ["Only the colour of the user interface",
        "Completeness, optimality, time, and memory requirements",
        "The computer's wallpaper",
        "The number of buttons on the keyboard"]),
    _q(10, "mcq", "Breadth-First Search",
       "Which data structure is normally used by Breadth-First Search (BFS)?",
       "BFS serves nodes in the order they arrived, like a line at a counter.",
       ["Stack", "Queue", "Priority list ordered only by heuristic", "Hash value"]),
    _q(11, "mcq", "Depth-First Search",
       "Which data structure is most closely associated with Depth-First Search (DFS)?",
       "DFS dives deep, then backs up. Think last in, first out.",
       ["Queue", "Stack", "Spreadsheet", "Circular chart"]),
    _q(12, "mcq", "Iterative Deepening",
       "What is the main idea behind Iterative Deepening Search?",
       "'Iterative' means repeat. 'Deepening' means the limit grows.",
       ["Search only the deepest branch once",
        "Repeatedly run depth-limited search with increasing limits",
        "Always select the state with the smallest heuristic",
        "Avoid revisiting all levels of the tree"]),
    _q(13, "mcq", "Hill Climbing",
       "A hill-climbing algorithm reaches a state where every neighbouring state is worse, but a better solution exists elsewhere. What problem may occur?",
       "Every neighbour is worse, yet this is not the highest peak overall.",
       ["Local maximum", "Complete observability", "Guaranteed global optimum", "Perfect information"]),
    _q(14, "mcq", "Heuristic Search",
       "What is a heuristic function used for in AI search?",
       "A heuristic is an educated estimate, not a guarantee.",
       ["To estimate how close a state is to the goal or its remaining cost",
        "To store the final answer permanently",
        "To remove every possible state",
        "To guarantee that every search is optimal"]),
    _q(15, "mcq", "Greedy Best-First Search",
       "Greedy Best-First Search selects the node with the smallest heuristic value h(n). The frontier contains nodes P, Q, and R with h(P) = 6, h(Q) = 2, and h(R) = 4. Which node is selected next?",
       "Greedy looks only at h(n). Compare the three numbers.",
       ["P", "Q", "R", "All three simultaneously"],
       diagram=("frontier", {"P": 6, "Q": 2, "R": 4})),
    _q(16, "mcq", "Constraint Satisfaction Problems",
       "Which of the following is a typical Constraint Satisfaction Problem (CSP)?",
       "Look for variables, possible values and rules that must all hold.",
       ["Solving a Sudoku puzzle", "Playing a video without interruption",
        "Displaying a static image", "Saving a text file without restrictions"]),
    _q(17, "mcq", "Means-End Analysis",
       "What is the main purpose of means-end analysis?",
       "It is about shrinking the gap between where you are and where you want to be.",
       ["Compare the current state with the goal and choose actions that reduce the difference",
        "Select actions randomly",
        "Ignore the goal state",
        "Explore only the first node"]),
    _q(18, "mcq", "Recommendation Systems",
       "An online shopping system recommends products based on a customer's previous purchases and preferences. Which AI application is this?",
       "The system learns from what the customer did before.",
       ["Recommendation system", "Depth-limited search only",
        "Production rule compiler only", "State-space diagram"]),
    _q(19, "mcq", "Search Optimality",
       "When all edges in a graph have equal cost, which uninformed search algorithm finds a shortest path in terms of number of edges, assuming the goal is reachable?",
       "Which uninformed search expands the shallowest nodes first?",
       ["Breadth-First Search", "Depth-First Search", "Hill Climbing", "Random Search"]),
    _q(20, "mcq", "Random-Restart Hill Climbing",
       "Why can random-restart hill climbing improve the chance of finding a global optimum?",
       "The key word is 'restart'. What changes from one run to the next?",
       ["It starts the search from different initial states",
        "It always explores every possible path",
        "It removes all local maxima from the search space",
        "It guarantees that every starting state has the same result"]),
    # ---------------- Section 2: True or False ----------------
    _q(21, "tf", "Intelligent Agents",
       "A rational agent always knows the complete state of its environment.",
       "Does acting rationally require knowing everything?", TF_OPTIONS),
    _q(22, "tf", "Breadth-First Search",
       "BFS finds a shortest path in an unweighted graph when the goal is reachable and the search is performed correctly.",
       "Think about the order in which BFS visits nodes by distance from the start.", TF_OPTIONS),
    _q(23, "tf", "Production Systems",
       "Production systems can represent knowledge using IF-THEN rules.",
       "Condition leads to action.", TF_OPTIONS),
    _q(24, "tf", "Hill Climbing",
       "Hill climbing is guaranteed to find the global optimum in every search space.",
       "Can hill climbing ever get stuck?", TF_OPTIONS),
    _q(25, "tf", "Constraint Satisfaction Problems",
       "In a CSP, a variable's domain contains the values that can be assigned to that variable.",
       "A domain is the pool of allowed values.", TF_OPTIONS),
    # ---------------- Section 3: Assertion and reason ----------------
    _q(26, "ar", "Breadth-First Search", "",
       "Does BFS miss any level when the branching factor is finite? Then ask whether the reason explains the assertion.",
       AR_OPTIONS,
       assertion="BFS is complete when the branching factor is finite.",
       reason="BFS systematically explores nodes level by level and will eventually reach a reachable goal at finite depth."),
    _q(27, "ar", "Heuristic Search", "",
       "Does an estimate that guides the search explain why effort could shrink?",
       AR_OPTIONS,
       assertion="A heuristic can help reduce the search effort in an AI problem.",
       reason="A heuristic provides an estimate that can guide the search toward promising states."),
    _q(28, "ar", "Intelligent Agents", "",
       "Does 'using the information available' explain why partial information is acceptable?",
       AR_OPTIONS,
       assertion="A rational agent can work in a partially observable environment.",
       reason="Rationality requires the agent to choose actions using the information available to it."),
    _q(29, "ar", "Depth-First Search", "",
       "Judge the assertion and the reason separately. Is each one true on its own?",
       AR_OPTIONS,
       assertion="DFS always finds the shortest path in an unweighted graph.",
       reason="DFS explores a branch deeply before backtracking."),
    _q(30, "ar", "Constraint Satisfaction Problems", "",
       "Think about what 'satisfy' means in a CSP, and what constraints do.",
       AR_OPTIONS,
       assertion="A CSP solution must satisfy all specified constraints.",
       reason="Constraints restrict which combinations of variable assignments are allowed."),
    # ---------------- Section 4: Fill in the blanks ----------------
    _q(31, "fill", "Sensors and Actuators",
       "The components that collect information from an agent's environment are called ______.",
       "What do agents use to perceive? Give the plural form."),
    _q(32, "fill", "Iterative Deepening",
       "The search algorithm that repeatedly increases its depth limit is called ______.",
       "It runs depth-limited search again and again, with a larger limit each time."),
    _q(33, "fill", "Heuristic Search",
       "In heuristic search, h(n) estimates the remaining cost or distance from node n to the ______.",
       "Where is the search trying to arrive?"),
    _q(34, "fill", "Constraint Satisfaction Problems",
       "In a CSP, the set of possible values for a variable is called its ______.",
       "A variable can only take values from this set."),
    _q(35, "fill", "Means-End Analysis",
       "The problem-solving technique that reduces the difference between the current state and goal state is called ______.",
       "It compares the current state with the goal and acts on the difference."),
    # ---------------- Section 5: Matching ----------------
    _q(36, "match", "Search Algorithms",
       "Match the search algorithm to its main characteristic.",
       "Match each name to how it moves through the search tree.",
       items=["BFS", "DFS", "Iterative Deepening Search"],
       choices={"A": "Explores one branch deeply before backtracking",
                "B": "Explores nodes level by level",
                "C": "Repeatedly increases a depth limit"}),
    _q(37, "match", "Intelligent Agents",
       "Match the intelligent-agent component to its role.",
       "Which part perceives, which part acts, and which part judges success?",
       items=["Sensor", "Actuator", "Performance measure"],
       choices={"A": "Evaluates how successfully the agent performs",
                "B": "Collects information from the environment",
                "C": "Carries out actions in the environment"}),
    _q(38, "match", "Search Concepts",
       "Match the search concept to its description.",
       "Think: a peak, a record of visited states, an estimate.",
       items=["Local maximum", "Explored set", "Heuristic"],
       choices={"A": "Estimates the desirability or remaining cost of a state",
                "B": "Records states that have already been explored",
                "C": "A state better than its neighbours but not necessarily the global optimum"}),
    _q(39, "match", "Problem Formulation",
       "Match the problem-solving term to its meaning.",
       "Where you begin, where you want to end, and the moves in between.",
       items=["Initial state", "Goal state", "Operators"],
       choices={"A": "Actions that transform one state into another",
                "B": "The state from which the problem begins",
                "C": "The desired target state"}),
    _q(40, "match", "AI Applications",
       "Match the AI application or technique to its use.",
       "Match each use case to what that technique actually does.",
       items=["Recommendation system", "Constraint Satisfaction Problem", "Heuristic route estimate"],
       choices={"A": "Estimates how far a route-search state is from its destination",
                "B": "Finds assignments that satisfy a set of restrictions",
                "C": "Suggests items based on user preferences or behaviour"}),
    # ---------------- Section 6: Real-world scenarios ----------------
    _q(41, "scenario", "Smart Traffic Management",
       "A smart traffic system uses cameras and sensors to monitor vehicles. Some roads are hidden from the cameras, so the system does not have complete information. Which environment property best describes this situation?",
       "Can the system see every relevant road?",
       ["Partially observable", "Fully observable", "Completely static", "Decomposable by definition"]),
    _q(42, "scenario", "Rescue Robot",
       "A rescue robot must find a route through an unweighted grid to reach a trapped person. The robot needs a path with the fewest moves. Which algorithm is suitable?",
       "Fewest moves, with every move costing the same.",
       ["DFS", "BFS", "Random search", "Basic hill climbing"]),
    _q(43, "scenario", "Adaptive Learning Platform",
       "An online learning platform recommends exercises using a student's previous answers and learning preferences. Which application is being demonstrated?",
       "It uses past behaviour to suggest what comes next.",
       ["Recommendation system", "Blind exhaustive search only",
        "Sensor calibration", "Random-restart hill climbing"]),
    _q(44, "scenario", "Hospital Staff Scheduling",
       "A hospital must assign nurses to shifts while ensuring that no nurse works two overlapping shifts and every shift has the required staff. Which AI problem formulation is most appropriate?",
       "Variables, values, and rules that must all hold at once.",
       ["Constraint Satisfaction Problem", "Turing Test",
        "Unrestricted random search", "Image classification"]),
    _q(45, "scenario", "Robot Path Optimization",
       "A robot uses hill climbing to improve a route. It repeatedly reaches a route that cannot be improved by any small local change, even though a better route exists elsewhere. What is a suitable way to improve its chance of finding a better solution?",
       "What if the robot tried climbing from several different starting routes?",
       ["Use random restarts from different initial routes",
        "Always reuse the same starting route",
        "Remove the goal state",
        "Stop evaluating neighbouring routes"]),
    # ---------------- Section 7: Search and state space ----------------
    _q(46, "search", "BFS Traversal",
       "Consider the following tree. Children are explored from left to right.\n\n"
       "- S is the root.\n- S has children A and B.\n- A has child G.\n- B has child C.\n\n"
       "Starting at S, use BFS and stop when G is removed from the queue for goal testing. "
       "What is the order of nodes removed from the queue?",
       "BFS uses a queue: add children at the back, remove from the front.",
       ["S, A, B, G", "S, B, C, A, G", "S, A, G", "S, B, A, C, G"],
       diagram=("tree46", None)),
    _q(47, "search", "Shortest Path",
       "Consider an unweighted graph with these edges:\n\n"
       "- S-A\n- A-G\n- S-B\n- B-C\n- C-G\n\n"
       "The search begins at S. Which is the shortest path from S to G?",
       "Count edges, and check that each option only uses edges that exist.",
       ["S → A → G", "S → B → C → G", "S → B → A → G", "S → C → G"],
       diagram=("graph47", None)),
    _q(48, "search", "Heuristic Selection",
       "Greedy Best-First Search chooses the node with the lowest heuristic value h(n). The available nodes are:\n\n"
       "- A: h(A) = 7\n- B: h(B) = 3\n- C: h(C) = 5\n\n"
       "Which node is expanded next?",
       "Greedy means the smallest h(n) wins.",
       ["A", "B", "C", "All nodes are expanded simultaneously"],
       diagram=("frontier", {"A": 7, "B": 3, "C": 5})),
    _q(49, "search", "Iterative Deepening Search",
       "A goal node G is located at depth 4 from the start node. Iterative Deepening Search begins with depth limit 0 "
       "and increases the limit by 1 after each unsuccessful search. What is the first depth limit at which the goal can be found?",
       "The depth limit must be at least as large as the goal's depth.",
       ["2", "3", "4", "5"],
       diagram=("chain49", None)),
    _q(50, "search", "Timetable CSP",
       "A college needs to schedule three classes A, B, and C into time slots 1, 2, and 3. "
       "Classes A and B cannot occur at the same time, and classes B and C cannot occur at the same time. "
       "Which assignment satisfies both constraints?",
       "Test each option against both 'not at the same time' rules.",
       ["A = 1, B = 1, C = 2", "A = 1, B = 2, C = 2", "A = 1, B = 2, C = 3", "A = 3, B = 3, C = 3"],
       diagram=("csp50", None)),
]

# The answer key is kept apart from the visible question data. It is only read
# by the grading functions after the quiz has been submitted.
ANSWER_KEY = {
    1: {"answer": "B", "explanation": "AI refers to systems that perform tasks associated with intelligent behaviour, such as learning, reasoning, problem-solving, and decision-making."},
    2: {"answer": "B", "explanation": "The Turing Test evaluates whether a machine's conversational behaviour can be distinguished from a human's."},
    3: {"answer": "B", "explanation": "A rational agent selects actions that are expected to perform well according to its performance measure and available information."},
    4: {"answer": "B", "explanation": "Sensors such as cameras, radar, and lidar collect information about the surrounding environment."},
    5: {"answer": "B", "explanation": "The robot cannot observe the entire relevant state of the environment."},
    6: {"answer": "A", "explanation": "A state space contains the possible states and the transitions between them."},
    7: {"answer": "A", "explanation": "Production systems use condition-action rules, commonly represented as IF-THEN statements."},
    8: {"answer": "B", "explanation": "Decomposability means a problem can be broken into smaller subproblems that can be solved separately."},
    9: {"answer": "B", "explanation": "Search algorithms are evaluated using properties such as completeness, optimality, time complexity, and space complexity."},
    10: {"answer": "B", "explanation": "BFS uses a FIFO queue to explore nodes level by level."},
    11: {"answer": "B", "explanation": "DFS uses a stack or recursion to explore one branch deeply before backtracking."},
    12: {"answer": "B", "explanation": "Iterative deepening increases the depth limit until the goal is found."},
    13: {"answer": "A", "explanation": "Hill climbing can become trapped at a local maximum instead of reaching the global maximum."},
    14: {"answer": "A", "explanation": "A heuristic estimates the desirability or remaining cost of a state to guide search."},
    15: {"answer": "B", "explanation": "Q has the smallest heuristic value, 2."},
    16: {"answer": "A", "explanation": "Sudoku involves variables, possible values, and constraints that must be satisfied."},
    17: {"answer": "A", "explanation": "Means-end analysis identifies differences between the current and goal states and selects actions to reduce them."},
    18: {"answer": "A", "explanation": "Recommendation systems use information about users and items to suggest relevant products."},
    19: {"answer": "A", "explanation": "BFS explores nodes in increasing depth order and finds the shallowest goal."},
    20: {"answer": "A", "explanation": "Different starting points can lead the algorithm to different regions of the search space."},
    21: {"answer": "False", "explanation": "Rationality concerns selecting appropriate actions based on available information. A rational agent can operate in a partially observable environment."},
    22: {"answer": "True", "explanation": "BFS explores states in increasing distance from the start."},
    23: {"answer": "True", "explanation": "Production rules specify conditions and the actions to take when those conditions hold."},
    24: {"answer": "False", "explanation": "It may stop at local optima or plateaus."},
    25: {"answer": "True", "explanation": "A domain specifies the possible values for a CSP variable."},
    26: {"answer": "A", "explanation": "With a finite branching factor and a reachable goal at finite depth, BFS eventually explores the goal's level."},
    27: {"answer": "A", "explanation": "Heuristics help prioritize promising states and can reduce unnecessary exploration."},
    28: {"answer": "A", "explanation": "A rational agent need not have complete information; it must make appropriate decisions based on its available percepts and knowledge."},
    29: {"answer": "D", "explanation": "DFS does explore deeply before backtracking, but it does not guarantee a shortest path."},
    30: {"answer": "A", "explanation": "A valid CSP assignment must meet every constraint, and constraints define the permitted combinations."},
    31: {"answer": "Sensors", "accepted": ["sensors", "sensor"],
         "explanation": "Sensors collect information (percepts) about the environment for the agent."},
    32: {"answer": "Iterative Deepening Search",
         "accepted": ["iterative deepening search", "iterative deepening", "ids",
                      "iterative deepening depth first search", "iddfs"],
         "explanation": "Iterative Deepening Search repeatedly runs depth-limited search with an increasing depth limit until the goal is found."},
    33: {"answer": "Goal", "accepted": ["goal", "goal state", "goal node"],
         "explanation": "In heuristic search, h(n) estimates the remaining cost or distance from node n to the goal."},
    34: {"answer": "Domain", "accepted": ["domain", "domains"],
         "explanation": "In a CSP, each variable has a domain: the set of values it may take."},
    35: {"answer": "Means-End Analysis",
         "accepted": ["means end analysis", "means ends analysis", "mea"],
         "explanation": "Means-end analysis compares the current state with the goal state and chooses actions that reduce the difference."},
    36: {"answer": {1: "B", 2: "A", 3: "C"},
         "explanation": "BFS explores level by level, DFS goes deep before backtracking, and Iterative Deepening Search repeatedly increases a depth limit."},
    37: {"answer": {1: "B", 2: "C", 3: "A"},
         "explanation": "Sensors collect information, actuators carry out actions, and the performance measure evaluates how well the agent is doing."},
    38: {"answer": {1: "C", 2: "B", 3: "A"},
         "explanation": "A local maximum beats its neighbours but may not be the global best, the explored set records visited states, and a heuristic estimates desirability or remaining cost."},
    39: {"answer": {1: "B", 2: "C", 3: "A"},
         "explanation": "The initial state is where the problem begins, the goal state is the target, and operators are the actions that move between states."},
    40: {"answer": {1: "C", 2: "B", 3: "A"},
         "explanation": "Recommendation systems suggest items from preferences or behaviour, a CSP finds assignments that satisfy restrictions, and a heuristic route estimate approximates the distance to the destination."},
    41: {"answer": "A", "explanation": "The system cannot observe every relevant part of the traffic environment."},
    42: {"answer": "B", "explanation": "BFS finds a shortest path in an unweighted graph when the goal is reachable."},
    43: {"answer": "A", "explanation": "The platform uses user behaviour and preferences to recommend suitable exercises."},
    44: {"answer": "A", "explanation": "The schedule must assign values to variables while satisfying staffing and scheduling constraints."},
    45: {"answer": "A", "explanation": "Random restarts let hill climbing explore different regions of the search space."},
    46: {"answer": "A", "explanation": "BFS removes S, then A, then B, and then G from the queue. C is still behind G in the queue."},
    47: {"answer": "A", "explanation": "The path S → A → G uses two edges, fewer than the three edges in S → B → C → G. The other listed paths contain edges that were not specified."},
    48: {"answer": "B", "explanation": "Node B has the smallest heuristic value, 3."},
    49: {"answer": "C", "explanation": "A depth limit of 4 is required to reach a goal located at depth 4."},
    50: {"answer": "C", "explanation": "A and B have different slots, and B and C also have different slots."},
}

N = len(QUESTIONS)
QBY_ID = {q["id"]: q for q in QUESTIONS}


def validate_bank() -> list[str]:
    """Return a list of problems with the question bank (empty list = healthy)."""
    errs = []
    ids = [q["id"] for q in QUESTIONS]
    if ids != list(range(1, MAX_SCORE + 1)):
        errs.append("Question ids must be exactly 1..50 in order.")
    if set(ANSWER_KEY) != set(ids):
        errs.append("ANSWER_KEY must have exactly one entry per question.")
    for q in QUESTIONS:
        qid, t = q["id"], q["type"]
        key = ANSWER_KEY.get(qid)
        if t not in TYPE_INFO:
            errs.append(f"Q{qid}: unknown type {t}")
            continue
        if key is None:
            continue
        if not key.get("explanation"):
            errs.append(f"Q{qid}: missing explanation")
        if t in CHOICE_TYPES:
            if key["answer"] not in q.get("options", {}):
                errs.append(f"Q{qid}: answer not among options")
            if t != "tf" and t != "ar" and len(q["options"]) != 4:
                errs.append(f"Q{qid}: expected four options")
        elif t == "fill":
            if not key.get("accepted"):
                errs.append(f"Q{qid}: no accepted answers")
        elif t == "match":
            if set(key["answer"]) != set(range(1, len(q["items"]) + 1)):
                errs.append(f"Q{qid}: matching key does not cover every item")
            if not set(key["answer"].values()) <= set(q["choices"]):
                errs.append(f"Q{qid}: matching key uses an unknown option")
    if len(QUESTIONS) != MAX_SCORE:
        errs.append(f"Expected {MAX_SCORE} questions, found {len(QUESTIONS)}.")
    return errs


# ======================================================================
# 2. DIAGRAMS  (inline SVG, nothing external)
# ======================================================================

PINK, ROSE, LAV, MINT, PLUM = "#FCE4EF", "#E78AB4", "#E9DDFD", "#D9F3EB", "#593B55"
FONT = "Poppins,Nunito,Segoe UI,Arial,sans-serif"


def _svg(w, h, body, label):
    return (f'<div class="diagram"><svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="{html.escape(label)}" '
            f'style="width:100%;max-width:{w}px;height:auto;">{body}</svg></div>')


def _edge(p, q, label=None):
    (x1, y1), (x2, y2) = p, q
    s = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{PLUM}" '
         f'stroke-width="2" stroke-linecap="round" opacity=".55"/>')
    if label:
        s += (f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 - 8}" text-anchor="middle" font-size="18" '
              f'font-weight="600" fill="{PLUM}" font-family="{FONT}">{label}</text>')
    return s


def _node(x, y, label, fill=PINK, r=24):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{ROSE}" stroke-width="2.5"/>'
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="15" font-weight="600" '
            f'fill="{PLUM}" font-family="{FONT}">{label}</text>')


def _text(x, y, s, size=12, anchor="middle", weight="500"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" '
            f'fill="{PLUM}" font-family="{FONT}">{s}</text>')


def diagram_html(spec):
    kind, data = spec
    if kind == "tree46":
        pos = {"S": (230, 40), "A": (130, 120), "B": (330, 120), "G": (130, 200), "C": (330, 200)}
        body = "".join(_edge(pos[a], pos[b]) for a, b in [("S", "A"), ("S", "B"), ("A", "G"), ("B", "C")])
        body += "".join(_node(*pos[n], n, LAV if n == "S" else MINT if n == "G" else PINK) for n in pos)
        return _svg(460, 240, body, "Tree: S is the root with children A and B. A has child G. B has child C. "
                                    "Children are explored left to right.")
    if kind == "graph47":
        pos = {"S": (70, 120), "A": (250, 45), "G": (430, 120), "B": (160, 195), "C": (340, 195)}
        edges = [("S", "A"), ("A", "G"), ("S", "B"), ("B", "C"), ("C", "G")]
        body = "".join(_edge(pos[a], pos[b]) for a, b in edges)
        body += "".join(_node(*pos[n], n, LAV if n == "S" else MINT if n == "G" else PINK) for n in pos)
        return _svg(500, 240, body, "Unweighted graph with edges S-A, A-G, S-B, B-C and C-G.")
    if kind == "chain49":
        xs = [60, 180, 300, 420, 540]
        names = ["S", "n1", "n2", "n3", "G"]
        body = "".join(_edge((xs[i], 55), (xs[i + 1], 55)) for i in range(4))
        for i, (x, nm) in enumerate(zip(xs, names)):
            body += _node(x, 55, nm, LAV if nm == "S" else MINT if nm == "G" else PINK)
            body += _text(x, 115, f"depth {i}")
        return _svg(600, 135, body, "A path from start node S at depth 0 to goal node G at depth 4.")
    if kind == "csp50":
        pos = {"A": (90, 60), "B": (240, 60), "C": (390, 60)}
        body = _edge(pos["A"], pos["B"], "≠") + _edge(pos["B"], pos["C"], "≠")
        for n, (x, y) in pos.items():
            body += _node(x, y, n) + _text(x, 118, "domain {1, 2, 3}")
        return _svg(480, 140, body, "Constraint graph: classes A, B and C, each with domain 1, 2, 3. "
                                    "A and B must differ, and B and C must differ.")
    if kind == "frontier":
        items = list(data.items())
        w = 40 + 150 * len(items)
        body = ""
        for i, (name, h) in enumerate(items):
            x = 30 + 150 * i
            body += (f'<rect x="{x}" y="20" width="120" height="70" rx="16" fill="{PINK}" stroke="{ROSE}" stroke-width="2.5"/>'
                     + _text(x + 60, 50, f"Node {name}", 15, weight="600")
                     + _text(x + 60, 76, f"h({name}) = {h}", 14))
        body += _text(w / 2, 112, "Frontier", 12)
        return _svg(w, 124, body, "Frontier nodes with heuristic values: "
                                  + ", ".join(f"h({n}) = {h}" for n, h in items))
    return ""


# ======================================================================
# 3. GRADING
# ======================================================================

STATUS_LABEL = {"correct": "Correct", "partial": "Partial credit",
                "incorrect": "Incorrect", "unanswered": "Unanswered"}
STATUS_ICON = {"correct": "✅", "partial": "🌗", "incorrect": "❌", "unanswered": "⚪"}


def norm_text(s: str) -> str:
    s = str(s).lower().replace("-", " ").replace("_", " ")
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def fill_ok(user: str, accepted: list[str]) -> bool:
    """Case/space/punctuation-insensitive match, tolerating a leading article
    and a small typo in longer answers. Unrelated answers are rejected."""
    u = norm_text(user)
    if not u:
        return False
    acc = [norm_text(a) for a in accepted]
    u2 = re.sub(r"^(the|a|an)\s+", "", u)
    if u in acc or u2 in acc:
        return True
    return any(len(a) >= 7 and difflib.SequenceMatcher(None, u2, a).ratio() >= 0.9 for a in acc)


def is_answered(q, resp) -> bool:
    if resp is None:
        return False
    if q["type"] == "fill":
        return bool(str(resp).strip())
    if q["type"] == "match":
        return any(resp.values())
    return True


def grade(q, resp):
    """Return (points, status). Every question is worth at most 1 point."""
    if not is_answered(q, resp):
        return 0.0, "unanswered"
    key = ANSWER_KEY[q["id"]]
    t = q["type"]
    if t in CHOICE_TYPES:
        ok = resp == key["answer"]
        return (1.0, "correct") if ok else (0.0, "incorrect")
    if t == "fill":
        return (1.0, "correct") if fill_ok(resp, key["accepted"]) else (0.0, "incorrect")
    right = sum(1 for i, c in key["answer"].items() if resp.get(i) == c)
    total = len(key["answer"])
    pts = min(1.0, right / total)
    if right == total:
        return 1.0, "correct"
    return (pts, "partial") if right else (0.0, "incorrect")


def choice_text(q, letter):
    if q["type"] == "tf":
        return letter
    return f"{letter}. {q['options'][letter]}"


def build_record(q, resp):
    key = ANSWER_KEY[q["id"]]
    pts, status = grade(q, resp)
    t = q["type"]
    if t in CHOICE_TYPES:
        user = choice_text(q, resp) if resp is not None else "No answer given"
        correct = choice_text(q, key["answer"])
        short = key["answer"]
    elif t == "fill":
        user = str(resp).strip() if is_answered(q, resp) else "No answer given"
        correct = key["answer"]
        short = key["answer"]
    else:
        resp = resp or {}
        ul, cl = [], []
        for i, item in enumerate(q["items"], 1):
            c = key["answer"][i]
            u = resp.get(i)
            ctxt = f"**{c}.** {q['choices'][c]}"
            cl.append(f"- ({i}) {item} → {ctxt}")
            if not u:
                ul.append(f"- ({i}) {item} → *no match chosen*")
            else:
                mark = "✓" if u == c else "✗"
                ul.append(f"- ({i}) {item} → **{u}.** {q['choices'][u]} {mark}")
        user, correct = "\n".join(ul), "\n".join(cl)
        short = ", ".join(f"{i}-{c}" for i, c in key["answer"].items())
    return {"id": q["id"], "type": t, "category": q["category"], "status": status,
            "points": pts, "user": user, "correct": correct, "short": short,
            "explanation": key["explanation"]}


def compute_results(answers):
    recs = [build_record(q, answers.get(q["id"])) for q in QUESTIONS]
    score = round(sum(r["points"] for r in recs), 4)
    counts = {k: sum(1 for r in recs if r["status"] == k) for k in STATUS_LABEL}
    by_type = {}
    for t in TYPE_ORDER:
        rs = [r for r in recs if r["type"] == t]
        by_type[t] = (round(sum(r["points"] for r in rs), 4), len(rs))
    return {"records": recs, "score": score, "pct": round(score / MAX_SCORE * 100, 1),
            "counts": counts, "by_type": by_type}


def performance_message(pct: float) -> str:
    if pct >= 90:
        return "Stardust Supreme! You have mastered the enchanted realm."
    if pct >= 75:
        return "Fairy Scholar! Your AI magic is flourishing."
    if pct >= 50:
        return "Growing Your Wings! A little more practice will help."
    return "Your Journey Has Just Begun! Keep exploring."


def fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.2f}"


# ======================================================================
# 4. THEME
# ======================================================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500;1,600&family=Dancing+Script:wght@500&family=Playfair+Display:wght@600;700&family=Poppins:wght@400;500;600&display=swap');
:root{
  --blush:#FCE4EF; --candy:#F6BFD8; --lav:#E9DDFD; --plum:#593B55; --cream:#FFF8FC;
  --mint:#D9F3EB; --rose:#E78AB4; --berry:#B83A74; --violet:#8E73C9;
  --glass:rgba(255,248,252,.82);
  --display:'Playfair Display','Cormorant Garamond',Georgia,'Times New Roman',serif;
  --serif2:'Cormorant Garamond','Playfair Display',Georgia,serif;
  --body:'Poppins','Nunito','Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;
  --script:'Dancing Script','Segoe Script','Brush Script MT',cursive;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"]{
  background:transparent !important; font-family:var(--body); color:var(--plum);
}
.stApp{ background:linear-gradient(160deg,#FCE4EF 0%,#F7D8EE 40%,#E9DDFD 100%) fixed !important; }
[data-testid="stHeader"]{ background:transparent !important; }
#MainMenu, footer{ visibility:hidden; }
.block-container{ position:relative; z-index:1; max-width:880px; padding-top:2rem; padding-bottom:3rem; }
button, input, textarea, select{ font-family:inherit; }
h1,h2,h3,h4{ font-family:var(--display); color:var(--plum); }
a{ color:var(--berry); }

/* ---- decorations ---- */
[data-testid="stElementContainer"]:has(.deco){ position:absolute; width:0; height:0; margin:0; }
.deco{ position:fixed; inset:0; pointer-events:none; z-index:-1; overflow:hidden; }
.deco .d{ position:absolute; color:var(--rose); opacity:.5; line-height:1; animation:twinkle 5s ease-in-out infinite; }
.deco .d.l{ color:#9B7BD8; }
.deco .d.f{ animation:drift 9s ease-in-out infinite; opacity:.75; }
.deco .glow{ position:absolute; border-radius:50%; filter:blur(50px); opacity:.55; }
.deco .g1{ width:300px; height:300px; top:-90px; left:-90px; background:#F6BFD8; }
.deco .g2{ width:340px; height:340px; bottom:-120px; right:-100px; background:#D9C8FB; }
.deco.still .d{ animation:none !important; opacity:.4; }
@keyframes twinkle{ 0%,100%{opacity:.22; transform:scale(.85);} 50%{opacity:.8; transform:scale(1.12);} }
@keyframes drift{ 0%,100%{transform:translateY(0) rotate(-5deg);} 50%{transform:translateY(-14px) rotate(7deg);} }
@keyframes rise{ 0%{transform:translateY(40px) scale(.6); opacity:0;} 20%{opacity:.95;} 100%{transform:translateY(-70vh) scale(1.2); opacity:0;} }
.burst{ position:fixed; inset:0; pointer-events:none; z-index:50; overflow:hidden; }
.burst span{ position:absolute; bottom:-10px; color:#D9649A; font-size:22px; opacity:0; animation:rise 3.6s ease-out 1 forwards; }
@media (prefers-reduced-motion:reduce){
  .deco .d, .burst span{ animation:none !important; }
  .burst{ display:none; }
}

/* ---- cards / hero ---- */
.hero{ text-align:center; padding:2.4rem 1.2rem 1.8rem; background:var(--glass);
  border:1px solid rgba(231,138,180,.4); border-radius:30px;
  box-shadow:0 0 0 7px rgba(246,191,216,.25), 0 22px 60px rgba(231,138,180,.28); }
.mini{ font-family:var(--script); color:#8A3C6E; font-size:1.15rem; letter-spacing:.2em; }
.brand{ font-family:var(--display); font-weight:700; font-size:clamp(2.5rem,9vw,4.6rem); letter-spacing:.12em;
  line-height:1.08; margin:.2rem 0 .1rem; color:var(--berry);
  background:linear-gradient(90deg,#B83A74,#E0699F 45%,#8E73C9); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; }
.sub{ font-family:var(--serif2); font-style:italic; font-weight:600; font-size:clamp(1.3rem,4vw,1.8rem); color:var(--plum); }
.tagline{ font-family:var(--script); font-size:1.35rem; color:#8A3C6E; margin:.6rem 0 1rem; }
.welcome{ max-width:560px; margin:0 auto 1.2rem; line-height:1.7; font-size:1rem; }
.stats{ display:inline-block; padding:.45rem 1.1rem; border-radius:999px; background:#fff;
  border:1.5px solid var(--candy); font-weight:600; font-size:.88rem; letter-spacing:.02em; }
.card{ background:var(--glass); border:1px solid rgba(231,138,180,.4); border-radius:22px;
  padding:1.1rem 1.4rem; box-shadow:0 10px 30px rgba(231,138,180,.2); margin:1.2rem 0; line-height:1.7; }
.card h3{ margin:.1rem 0 .5rem; font-size:1.35rem; }
.card ul{ margin:.3rem 0 0 1.1rem; padding:0; }
.foot{ text-align:center; margin-top:2rem; font-family:var(--script); font-size:1.15rem; color:#8A3C6E; }
.pill{ display:inline-block; padding:.28rem .85rem; border-radius:999px; background:var(--lav);
  border:1px solid rgba(89,59,85,.2); font-size:.8rem; font-weight:500; color:var(--plum); margin:0 .35rem .35rem 0; }
.pill.pk{ background:var(--blush); } .pill.mt{ background:var(--mint); }

/* ---- quiz header / progress ---- */
.qhead{ margin-bottom:1rem; }
.qnum{ font-family:var(--display); font-size:1.6rem; font-weight:700; margin:.2rem 0 .5rem; color:var(--plum); }
.pbar{ position:relative; height:14px; border-radius:999px; background:rgba(255,255,255,.8);
  border:1.5px solid var(--candy); overflow:visible; }
.pfill{ height:100%; border-radius:999px; background:linear-gradient(90deg,#F6BFD8,#E78AB4 60%,#B983E0); transition:width .3s ease; }
.pstar{ position:absolute; top:50%; transform:translate(-50%,-52%); font-size:1.15rem; color:var(--berry); }
.pnote{ font-size:.82rem; margin-top:.35rem; color:var(--plum); }
.st-key-qcard{ background:rgba(255,248,252,.92); border:1.5px solid var(--candy); border-radius:26px;
  padding:1.4rem 1.5rem; box-shadow:0 0 0 6px rgba(246,191,216,.25), 0 18px 45px rgba(231,138,180,.28); }
.qtitle{ font-family:var(--display); font-size:1.45rem; font-weight:700; margin:.2rem 0 0; color:var(--plum); }
.st-key-qcard [data-testid="stMarkdownContainer"] p, .st-key-qcard li{ font-size:1.04rem; line-height:1.65; }
.ar{ background:#fff; border:1.5px solid var(--candy); border-left:6px solid var(--rose); border-radius:14px; padding:.4rem 1rem; }
.ar p{ margin:.55rem 0; line-height:1.6; }
.blank{ display:inline-block; min-width:110px; border-bottom:2px solid var(--berry); margin:0 .2rem; }
.matchopts{ background:#fff; border:1.5px dashed var(--rose); border-radius:14px; padding:.7rem 1rem; line-height:1.8; margin-bottom:.6rem; }
.hint{ background:var(--mint); border:1.5px dashed #5FA88E; border-radius:14px; padding:.65rem 1rem; line-height:1.6; }
.diagram{ background:#fff; border:1.5px solid var(--candy); border-radius:16px; padding:.7rem; text-align:center; margin:.3rem 0 .6rem; }

/* ---- inputs ---- */
.stRadio [role="radiogroup"]{ gap:.55rem; }
.stRadio label[data-baseweb="radio"]{ background:#fff; border:1.5px solid var(--candy); border-radius:14px;
  padding:.7rem .95rem; width:100%; transition:background .15s,border-color .15s,box-shadow .15s; }
.stRadio label[data-baseweb="radio"]:hover{ background:var(--blush); border-color:var(--rose); }
.stRadio label[data-baseweb="radio"]:has(input:checked){ background:var(--lav); border-color:#8E73C9; box-shadow:0 0 0 3px rgba(142,115,201,.28); }
.stRadio label[data-baseweb="radio"]:focus-within{ outline:3px solid var(--plum); outline-offset:2px; }
.stTextInput input{ background:#fff; border-radius:12px; color:var(--plum); }
.stTextInput [data-baseweb="input"], .stSelectbox [data-baseweb="select"] > div{ background:#fff; border:1.5px solid var(--candy); border-radius:12px; }
.stTextInput [data-baseweb="input"]:focus-within, .stSelectbox [data-baseweb="select"]:focus-within > div{ border-color:var(--berry); box-shadow:0 0 0 3px rgba(184,58,116,.25); }
[data-testid="stExpander"]{ background:rgba(255,255,255,.75); border:1px solid var(--candy) !important; border-radius:16px; }
.stTabs [data-baseweb="tab"]{ font-weight:600; color:var(--plum); }

/* ---- buttons ---- */
.stButton > button{ width:100%; border-radius:999px; border:1.5px solid var(--plum); background:var(--blush);
  min-height:2.9rem; padding:.55rem 1.1rem; transition:transform .15s, box-shadow .15s, background .15s; }
.stButton > button, .stButton > button p{ color:var(--plum) !important; font-weight:600; }
.stButton > button:hover{ transform:translateY(-1px); box-shadow:0 8px 20px rgba(231,138,180,.45); border-color:var(--plum); }
.stButton > button:focus-visible{ outline:3px solid var(--plum); outline-offset:3px; }
.stButton > button:disabled{ opacity:.45; cursor:not-allowed; transform:none; box-shadow:none; }
[class*="st-key-prev"] button{ background:var(--lav); border-color:var(--violet); }
[class*="st-key-next"] button{ background:linear-gradient(135deg,#F4A9CA,#E78AB4); border-color:#B8467F; }
[class*="st-key-next"] button, [class*="st-key-next"] button p{ color:#3B2139 !important; }
[class*="st-key-submit"] button, [class*="st-key-start"] button{
  background:linear-gradient(135deg,#CF4F87,#B83A74); border-color:#8E2A5A; box-shadow:0 0 20px rgba(207,79,135,.55); }
[class*="st-key-submit"] button, [class*="st-key-submit"] button p,
[class*="st-key-start"] button, [class*="st-key-start"] button p{ color:#fff !important; }
[class*="st-key-restart"] button{ background:var(--blush); border:2px solid var(--plum); }
.st-key-nav [data-testid="stHorizontalBlock"]{ flex-wrap:nowrap !important; gap:.7rem; }
.st-key-nav [data-testid="stColumn"], .st-key-nav [data-testid="column"]{ min-width:0 !important; flex:1 1 0 !important; width:auto !important; }

/* ---- sidebar ---- */
[data-testid="stSidebar"]{ background:linear-gradient(180deg,#FFF8FC,#F6E3F4) !important; border-right:1px solid var(--candy); }
.sbt{ font-family:var(--display); font-size:1.35rem; font-weight:700; color:var(--berry); letter-spacing:.08em; }
.sbrow{ display:flex; justify-content:space-between; font-size:.82rem; margin-top:.5rem; }
.sbrow.cur{ font-weight:700; }
.mbar{ height:6px; border-radius:999px; background:#fff; border:1px solid var(--candy); overflow:hidden; }
.mbar div{ height:100%; background:linear-gradient(90deg,#F6BFD8,#E78AB4); }

/* ---- results ---- */
.resultcard{ display:flex; flex-wrap:wrap; gap:1.6rem; align-items:center; justify-content:center; text-align:left;
  background:var(--glass); border:1px solid rgba(231,138,180,.4); border-radius:30px; padding:1.8rem 1.4rem;
  box-shadow:0 0 0 7px rgba(246,191,216,.25), 0 22px 60px rgba(231,138,180,.28); }
.donut{ width:190px; height:190px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex:0 0 auto;
  box-shadow:0 0 0 8px rgba(246,191,216,.35); }
.donut-in{ width:142px; height:142px; border-radius:50%; background:var(--cream); display:flex; flex-direction:column;
  align-items:center; justify-content:center; }
.donut-in .big{ font-family:var(--display); font-size:2.3rem; font-weight:700; line-height:1; }
.donut-in .of{ font-size:.78rem; } .donut-in .perc{ font-weight:600; color:var(--berry); margin-top:.2rem; }
.rtext{ flex:1 1 250px; min-width:230px; }
.greet{ font-family:var(--script); font-size:1.4rem; color:#8A3C6E; }
.rmsg{ font-family:var(--display); font-size:1.6rem; font-weight:700; line-height:1.3; margin:.2rem 0 .4rem; }
.tiles{ display:flex; flex-wrap:wrap; gap:.8rem; margin:1.2rem 0; }
.tile{ flex:1 1 130px; background:var(--glass); border:1.5px solid var(--candy); border-radius:18px; padding:.8rem 1rem; text-align:center; }
.tile b{ display:block; font-family:var(--display); font-size:1.8rem; }
.tile span{ font-size:.82rem; }
.brow{ margin:.7rem 0; } .brow .bl{ display:flex; justify-content:space-between; font-size:.88rem; font-weight:500; margin-bottom:.2rem; }
.revlist{ list-style:none; margin:.4rem 0 0; padding:0; }
.revlist li{ padding:.4rem .2rem; border-bottom:1px dashed var(--candy); font-size:.92rem; }
"""

DECOS = [
    ("✦", 5, 4, 20, 0.0, "l"), ("✧", 11, 90, 16, 1.1, ""), ("☾", 7, 84, 30, 0.4, "l"),
    ("♡", 26, 2, 18, 2.0, ""), ("🦋", 20, 94, 24, 0.0, "f"), ("⋆", 38, 96, 18, 1.6, "l"),
    ("✧", 46, 3, 22, 0.8, ""), ("♡", 58, 93, 16, 2.4, ""), ("✦", 66, 5, 16, 1.3, "l"),
    ("🦋", 74, 2, 22, 0.6, "f"), ("☾", 84, 91, 26, 1.0, "l"), ("✧", 90, 8, 18, 2.2, ""),
    ("⋆", 92, 70, 16, 0.3, "l"), ("✦", 3, 38, 14, 1.9, ""), ("✧", 4, 64, 18, 0.5, "l"),
    ("♡", 95, 35, 14, 1.2, ""),
]


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def flat(s: str) -> str:
    """Join an HTML snippet into one line so Markdown never treats it as code."""
    return "".join(line.strip() for line in s.strip().splitlines())


def md(s: str):
    st.markdown(flat(s), unsafe_allow_html=True)


def inject_theme():
    still = "" if st.session_state.fx_on else " still"
    spans = "".join(
        f'<span class="d {c}" style="top:{t}%;left:{l}%;font-size:{s}px;animation-delay:{d}s">{g}</span>'
        for g, t, l, s, d, c in DECOS)
    deco = f'<div class="deco{still}" aria-hidden="true"><i class="glow g1"></i><i class="glow g2"></i>{spans}</div>'
    st.markdown(f"<style>{CSS}</style>\n{deco}", unsafe_allow_html=True)


def footer():
    md('<div class="foot">Crafted with curiosity &amp; a little fairy dust. ✧</div>')


# ======================================================================
# 5. STATE + CALLBACKS
# ======================================================================

def init_state():
    s = st.session_state
    defaults = {"page": "home", "name": "", "difficulty": "Dewdrop", "current": 0, "answers": {},
                "hints_shown": set(), "started": False, "results": None, "fx_on": True,
                "restart_pending": False}
    for k, v in defaults.items():
        if k not in s:
            s[k] = v


def reset_quiz():
    s = st.session_state
    for k in [k for k in s.keys() if str(k).startswith("w_")]:
        del s[k]
    s.answers, s.hints_shown = {}, set()
    s.current, s.results = 0, None
    s.started, s.restart_pending = False, False


def go(page):
    st.session_state.page = page


def goto_q(i):
    if i is None:
        return

    if isinstance(i, str):
        import re
        match = re.search(r"Q(\d+)", i)
        if match:
            i = int(match.group(1)) - 1
        else:
            return
    else:
        i = int(i)

    st.session_state.current = max(0, min(N - 1, i))


def jump_cb():
    goto_q(st.session_state.jump_sel)


def _set_fx(k):
    st.session_state.fx_on = bool(st.session_state[k])


def fx_toggle(where):
    st.toggle("Sparkle motion", value=st.session_state.fx_on, key=f"fx_{where}",
              on_change=_set_fx, args=(f"fx_{where}",),
              help="Turn off moving sparkles and the celebration. Decorations stay, but stop moving.")


def save_choice(qid):
    st.session_state.answers[qid] = st.session_state[f"w_{qid}"]


def save_text(qid):
    v = st.session_state.get(f"w_{qid}") or ""
    if v.strip():
        st.session_state.answers[qid] = v
    else:
        st.session_state.answers.pop(qid, None)


def save_match(qid, i):
    v = st.session_state.get(f"w_{qid}_{i}")
    d = st.session_state.answers.setdefault(qid, {})
    if v:
        d[i] = v
    else:
        d.pop(i, None)


def reveal_hint(qid):
    s = st.session_state
    limit = DIFFICULTIES[s.difficulty]["hints"]
    if limit is None or len(s.hints_shown) < limit:
        s.hints_shown.add(qid)


def begin_setup():
    st.session_state.page = "setup"


def resume():
    st.session_state.page = "quiz"


def finish_setup():
    s = st.session_state
    name = (s.get("name_input") or "").strip()
    if not name:
        s.setup_error = "Please tell the fairies your name first."
        return
    s.setup_error = ""
    s.name = name[:40]
    s.difficulty = s.get("diff_input", "Dewdrop")
    s.page = "instructions"


def begin_quiz():
    reset_quiz()
    st.session_state.started = True
    st.session_state.page = "quiz"


def submit_quiz():
    s = st.session_state
    s.results = compute_results(s.answers)
    s.page = "results"


def restart_ask():
    st.session_state.restart_pending = True


def restart_no():
    st.session_state.restart_pending = False


def restart_yes():
    reset_quiz()
    st.session_state.started = True
    st.session_state.page = "quiz"


def try_again():
    reset_quiz()
    st.session_state.page = "setup"


def back_home():
    reset_quiz()
    st.session_state.page = "home"


# ======================================================================
# 6. PAGES
# ======================================================================

def render_home():
    s = st.session_state
    md("""
    <div class="hero">
      <div class="mini">✧ ⋆ ☾ ⋆ ✧</div>
      <div class="brand">FAIRYVERSE</div>
      <div class="sub">The Enchanted AI Quiz</div>
      <div class="tagline">“Sprinkle some stardust on your brain cells.”</div>
      <p class="welcome">Welcome, little stardust. Slip through the shimmering gate and step into the magical world
      of Artificial Intelligence, where agents sense their surroundings, search spaces glitter, and every clever answer
      lights up another star.</p>
      <div class="stats">50 Questions • 7 Question Types • 1 Magical Challenge</div>
    </div>""")
    st.write("")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if s.started and s.results is None:
            st.button("Resume your quest →", key="resume_btn", on_click=resume)
        st.button("Enter the Fairy Realm ✨", key="start_home", on_click=begin_setup)
    md("""
    <div class="card"><h3>What the enchantment covers</h3>
    This quiz covers Artificial Intelligence fundamentals, intelligent agents, search algorithms, heuristics, and
    constraint satisfaction. It also visits production systems and real-world AI applications.
    Everything runs offline. There are no accounts, no API keys and no tracking.</div>""")
    fx_toggle("home")
    footer()


def render_setup():
    s = st.session_state
    md('<div class="card"><h3>✦ Who goes there?</h3>Tell the fairies your name and choose your path. '
       'Difficulty only changes how many fairy hints you may use. Scoring is identical for every level.</div>')
    st.text_input("Your name", value=s.name, max_chars=40, key="name_input", placeholder="e.g. Kanitha")
    names = list(DIFFICULTIES)
    st.radio("Choose your path", names, index=names.index(s.difficulty), key="diff_input",
             captions=[DIFFICULTIES[n]["blurb"] for n in names])
    fx_toggle("setup")
    if s.get("setup_error"):
        st.error(s.setup_error)
    c1, c2 = st.columns(2)
    with c1:
        st.button("← Back", key="prev_setup", on_click=go, args=("home",))
    with c2:
        st.button("Continue ✨", key="start_setup", on_click=finish_setup)
    footer()


def render_instructions():
    s = st.session_state
    md(f"""
    <div class="card"><h3>✧ Welcome, {esc(s.name)}</h3>
    <span class="pill pk">Path: {esc(s.difficulty)}</span><span class="pill">50 questions</span>
    <ul>
    <li>You will see one question at a time. Use <b>Previous</b> and <b>Next</b>, or the jump menu in the sidebar.</li>
    <li>Your answers are saved as you move around. Nothing is reset when you go back.</li>
    <li>Correct answers stay hidden until you submit the quiz.</li>
    <li>Each question is worth 1 point, so the quiz is out of 50. In matching questions every correct pair earns a share of that point.</li>
    <li>Fill-in-the-blank answers ignore capitalisation, spacing and punctuation, and accept sensible equivalents.</li>
    <li>You can submit with unanswered questions. They simply score zero.</li>
    </ul></div>""")
    c1, c2 = st.columns(2)
    with c1:
        st.button("← Change name", key="prev_instr", on_click=go, args=("setup",))
    with c2:
        st.button("Begin the Quiz ✨", key="start_instr", on_click=begin_quiz)
    footer()


def question_body(q):
    """Render the prompt + input widget(s) for one question."""
    s = st.session_state
    qid, t = q["id"], q["type"]
    stored = s.answers.get(qid)
    if t == "ar":
        md(f'<div class="ar"><p><b>Assertion:</b> {esc(q["assertion"])}</p>'
           f'<p><b>Reason:</b> {esc(q["reason"])}</p></div>')
    else:
        st.markdown(q["text"].replace("______", '<span class="blank"></span>'), unsafe_allow_html=True)
    if q.get("diagram"):
        st.markdown(diagram_html(q["diagram"]), unsafe_allow_html=True)

    if t in CHOICE_TYPES:
        opts = q["options"]
        keys = list(opts)
        idx = keys.index(stored) if stored in keys else None
        val = st.radio("Choose one answer", keys, index=idx, key=f"w_{qid}",
                       format_func=lambda k: k if t == "tf" else f"{k}. {opts[k]}",
                       label_visibility="collapsed", on_change=save_choice, args=(qid,))
        if val is not None:
            s.answers[qid] = val
    elif t == "fill":
        val = st.text_input("Type your answer", value=stored or "", max_chars=60, key=f"w_{qid}",
                            placeholder="Type your answer…", on_change=save_text, args=(qid,))
        if val.strip():
            s.answers[qid] = val
    else:
        ch = q["choices"]
        lines = "<br>".join(f"<b>{k}.</b> {esc(v)}" for k, v in ch.items())
        md(f'<div class="matchopts"><b>Options</b><br>{lines}</div>')
        cur = stored or {}
        for i, item in enumerate(q["items"], 1):
            keys = list(ch)
            idx = keys.index(cur[i]) if cur.get(i) in keys else None
            v = st.selectbox(f"({i}) {item}", keys, index=idx, key=f"w_{qid}_{i}",
                             format_func=lambda k: f"{k}. {ch[k]}", placeholder="Choose a match…",
                             on_change=save_match, args=(qid, i))
            if v:
                s.answers.setdefault(qid, {})[i] = v


def hint_area(q):
    s = st.session_state
    qid = q["id"]
    limit = DIFFICULTIES[s.difficulty]["hints"]
    if qid in s.hints_shown:
        md(f'<div class="hint"><b>Fairy guidance:</b> {esc(q["hint"])}</div>')
    elif limit == 0:
        st.caption("Hints are asleep on the Stardust path.")
    elif limit is not None and len(s.hints_shown) >= limit:
        st.caption("You have used all of your fairy hints.")
    else:
        st.button("🪄 Need a little fairy guidance?", key=f"hint_{qid}", on_click=reveal_hint, args=(qid,))
        if limit is not None:
            st.caption(f"{limit - len(s.hints_shown)} hint(s) left on this path.")


def render_sidebar():
    s = st.session_state
    answered = sum(is_answered(q, s.answers.get(q["id"])) for q in QUESTIONS)
    cur_type = QUESTIONS[s.current]["type"]
    with st.sidebar:
        md('<div class="sbt">✦ FAIRYVERSE</div>')
        md(f'<span class="pill pk">{esc(s.name)}</span><span class="pill">{esc(s.difficulty)}</span>')
        md(f'<div class="sbrow"><span>Answered</span><span>{answered}/{N}</span></div>'
           f'<div class="mbar"><div style="width:{answered / N * 100}%"></div></div>')
        rows = ""
        for t in TYPE_ORDER:
            qs = [q for q in QUESTIONS if q["type"] == t]
            done = sum(is_answered(q, s.answers.get(q["id"])) for q in qs)
            rows += (f'<div class="sbrow{" cur" if t == cur_type else ""}"><span>{TYPE_INFO[t][1]} · {TYPE_INFO[t][0]}</span>'
                     f'<span>{done}/{len(qs)}</span></div><div class="mbar"><div style="width:{done / len(qs) * 100}%"></div></div>')
        md(rows)
        st.write("")
        s["jump_sel"] = s.current
        labels = [f"{'●' if is_answered(x, s.answers.get(x['id'])) else '○'}  Q{x['id']:02d} · {x['category']}"
                  for x in QUESTIONS]
        st.selectbox("Jump to question", range(N), key="jump_sel", on_change=jump_cb,
                     format_func=lambda i: labels[i])
        limit = DIFFICULTIES[s.difficulty]["hints"]
        if limit != 0:
            st.caption(f"Hints used: {len(s.hints_shown)}" + ("" if limit is None else f" of {limit}"))
        fx_toggle("side")
        st.button("Finish & Submit 🪄", key="submit_side", on_click=go, args=("confirm",))
        if s.restart_pending:
            st.warning("This clears every answer and starts again.")
            st.button("Yes, restart", key="restart_yes", on_click=restart_yes)
            st.button("Keep going", key="restart_no", on_click=restart_no)
        else:
            st.button("Restart quiz", key="restart_side", on_click=restart_ask)
        st.button("Save & leave to home", key="restart_home", on_click=go, args=("home",))


def render_quiz():
    s = st.session_state
    cur = s.current
    q = QUESTIONS[cur]
    render_sidebar()
    answered = sum(is_answered(x, s.answers.get(x["id"])) for x in QUESTIONS)
    pct = (cur + 1) / N * 100
    md(f"""
    <div class="qhead">
      <span class="pill pk">✧ {esc(s.name)}</span><span class="pill">{esc(TYPE_INFO[q['type']][1])} · {esc(TYPE_INFO[q['type']][0])}</span>
      <div class="qnum">Question {cur + 1:02d} of {N}</div>
      <div class="pbar" role="progressbar" aria-label="Quiz progress" aria-valuemin="1" aria-valuemax="{N}" aria-valuenow="{cur + 1}">
        <div class="pfill" style="width:{pct}%"></div><span class="pstar" style="left:{pct}%">✦</span></div>
      <div class="pnote">{answered} of {N} answered</div>
    </div>""")
    with st.container(key="qcard"):
        md(f'<span class="pill mt">{esc(q["category"])}</span>')
        question_body(q)
        hint_area(q)
    st.write("")
    with st.container(key="nav"):
        c1, c2 = st.columns(2)
        with c1:
            st.button("← Previous", key="prev_btn", on_click=goto_q, args=(cur - 1,), disabled=cur == 0)
        with c2:
            if cur < N - 1:
                st.button("Next →", key="next_btn", on_click=goto_q, args=(cur + 1,))
            else:
                st.button("Submit Quiz 🪄", key="submit_main", on_click=go, args=("confirm",))
    st.caption("You can submit at any time from the sidebar. Unanswered questions score zero.")


def render_confirm():
    s = st.session_state
    unanswered = [q["id"] for q in QUESTIONS if not is_answered(q, s.answers.get(q["id"]))]
    done = N - len(unanswered)
    extra = ""
    if unanswered:
        extra = ("<p>Still unanswered: " + ", ".join(f"Q{i}" for i in unanswered) + ".</p>")
    md(f"""
    <div class="card"><h3>✧ Ready to reveal your results, {esc(s.name)}?</h3>
    <p>You have answered <b>{done}</b> of <b>{N}</b> questions.</p>{extra}
    <p>Once you submit, the correct answers and explanations are revealed and your answers are locked in.</p></div>""")
    c1, c2 = st.columns(2)
    with c1:
        st.button("← Back to the quiz", key="prev_confirm", on_click=go, args=("quiz",))
    with c2:
        st.button("Yes, submit my quiz ✨", key="submit_final", on_click=submit_quiz)


def bar_row(label, score, total):
    p = score / total * 100 if total else 0
    return (f'<div class="brow"><div class="bl"><span>{esc(label)}</span><span>{fmt(score)} / {total}</span></div>'
            f'<div class="mbar" role="img" aria-label="{esc(label)}: {fmt(score)} of {total}"><div style="width:{p}%"></div></div></div>')


def review_item(rec):
    q = QBY_ID[rec["id"]]
    title = (f"{STATUS_ICON[rec['status']]} Q{rec['id']:02d} · {rec['category']} — "
             f"{STATUS_LABEL[rec['status']]} ({fmt(rec['points'])}/1)")
    with st.expander(title):
        if q["type"] == "ar":
            st.markdown(f"**Assertion:** {q['assertion']}\n\n**Reason:** {q['reason']}")
        else:
            st.markdown(q["text"].replace("______", '<span class="blank"></span>'), unsafe_allow_html=True)
        if q.get("diagram"):
            st.markdown(diagram_html(q["diagram"]), unsafe_allow_html=True)
        if q["type"] == "match":
            st.markdown("**Your matches:**\n" + rec["user"])
            st.markdown("**Correct matches:**\n" + rec["correct"])
        else:
            st.markdown(f"**Your answer:** {rec['user']}")
            st.markdown(f"**Correct answer:** {rec['correct']}")
        st.markdown(f"**Explanation:** {rec['explanation']}")


def render_results():
    s = st.session_state
    r = s.results
    pct, score, c = r["pct"], r["score"], r["counts"]
    if pct >= 75 and s.fx_on:
        stars = "".join(f'<span style="left:{5 + i * 6.5}%;animation-delay:{(i % 5) * .25}s">✦</span>' for i in range(15))
        md(f'<div class="burst" aria-hidden="true">{stars}</div>')
    md(f"""
    <div class="resultcard">
      <div class="donut" role="img" aria-label="Score {fmt(score)} out of {MAX_SCORE}, {pct} percent"
           style="background:conic-gradient(#D9649A 0 {pct}%, #F6D9E8 {pct}% 100%)">
        <div class="donut-in"><span class="big">{fmt(score)}</span><span class="of">out of {MAX_SCORE}</span>
        <span class="perc">{pct}%</span></div></div>
      <div class="rtext"><div class="greet">Your stardust report, {esc(s.name)} ✦</div>
        <div class="rmsg">{esc(performance_message(pct))}</div>
        <span class="pill pk">Path: {esc(s.difficulty)}</span><span class="pill">Hints used: {len(s.hints_shown)}</span></div>
    </div>""")
    md(f"""
    <div class="tiles">
      <div class="tile"><b>{c['correct']}</b><span>Correct</span></div>
      <div class="tile"><b>{c['incorrect']}</b><span>Incorrect</span></div>
      <div class="tile"><b>{c['partial']}</b><span>Partial credit</span></div>
      <div class="tile"><b>{c['unanswered']}</b><span>Unanswered</span></div>
    </div>""")

    tab1, tab2 = st.tabs(["✨ Overview", "📖 Answer review"])
    with tab1:
        md('<div class="card"><h3>Your score by question type</h3>'
           + "".join(bar_row(TYPE_INFO[t][0], *r["by_type"][t]) for t in TYPE_ORDER) + "</div>")
        missed = [x for x in r["records"] if x["status"] != "correct"]
        if missed:
            items = "".join(
                f"<li><b>Q{x['id']:02d}</b> · {esc(x['category'])} — {STATUS_LABEL[x['status']]}. "
                f"Correct: <b>{esc(x['short'])}</b></li>" for x in missed)
            md(f'<div class="card"><h3>Questions to revisit ({len(missed)})</h3><ul class="revlist">{items}</ul>'
               f'<p>Open the <b>Answer review</b> tab for full explanations.</p></div>')
        else:
            md('<div class="card"><h3>A perfect score</h3>Every question is correct. Nothing to revisit.</div>')
    with tab2:
        mode = st.radio("Show", ["Needs another look", "All questions"], horizontal=True, key="review_filter")
        shown = [x for x in r["records"] if mode == "All questions" or x["status"] != "correct"]
        if not shown:
            st.success("Everything was correct. Switch to “All questions” to read the explanations.")
        for rec in shown:
            review_item(rec)
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        st.button("Try Again, Little Stardust", key="start_again", on_click=try_again)
    with b2:
        st.button("Return to the Fairy Realm", key="restart_return", on_click=back_home)
    footer()


PAGES = {"home": render_home, "setup": render_setup, "instructions": render_instructions,
         "quiz": render_quiz, "confirm": render_confirm, "results": render_results}


def main():
    st.set_page_config(page_title="FAIRYVERSE · The Enchanted AI Quiz", page_icon="✨",
                       layout="centered", initial_sidebar_state="expanded")
    init_state()
    problems = validate_bank()
    if problems:
        st.error("The question bank has problems:\n\n" + "\n".join(f"- {p}" for p in problems))
        st.stop()
    inject_theme()
    page = st.session_state.page
    if page in ("quiz", "confirm") and not st.session_state.started:
        page = st.session_state.page = "home"
    if page == "results" and st.session_state.results is None:
        page = st.session_state.page = "home"
    PAGES[page]()


if __name__ == "__main__":
    main()
