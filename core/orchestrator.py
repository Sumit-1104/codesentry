from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

from reviewer.static_analyzer import analyze_file
from reviewer.security_scanner import scan_file
from reviewer.doc_generator import generate_docstrings
from reviewer.test_generator import generate_tests


# Step 1: State define karo - ye sabhi agents ke beech shared "dictionary" hai
class GraphState(TypedDict):
    filepath: str
    static_results: List[Dict[str, Any]]
    security_results: List[Dict[str, Any]]
    doc_results: str
    test_results: str


# Step 2: Har agent ko ek "node function" mein wrap karo
# Har function state leta hai, apna kaam karta hai, state update karke return karta hai

def run_static_analyzer(state: GraphState) -> GraphState:
    print("Running static analyzer...")
    return {"static_results": analyze_file(state["filepath"])}


def run_security_scanner(state: GraphState) -> GraphState:
    print("Running security scanner...")
    return {"security_results": scan_file(state["filepath"])}


def run_doc_generator(state: GraphState) -> GraphState:
    print("Running doc generator...")
    return {"doc_results": generate_docstrings(state["filepath"])}


def run_test_generator(state: GraphState) -> GraphState:
    print("Running test generator...")
    return {"test_results": generate_tests(state["filepath"])}


# Step 3: Aggregator - jab sab agents complete ho jaye, final report banao
def aggregator(state: GraphState) -> GraphState:
    print("\n===== FINAL REPORT =====")
    print("\n--- Static Analysis ---")
    for issue in state.get("static_results", []):
        print(issue)
    print("\n--- Security Issues ---")
    for issue in state.get("security_results", []):
        print(issue)
    print("\n--- Suggested Docstrings ---")
    print(state.get("doc_results", ""))
    print("\n--- Suggested Tests ---")
    print(state.get("test_results", ""))
    return state


# Step 4: Graph banao aur nodes add karo
builder = StateGraph(GraphState)

builder.add_node("static_analyzer", run_static_analyzer)
builder.add_node("security_scanner", run_security_scanner)
builder.add_node("doc_generator", run_doc_generator)
builder.add_node("test_generator", run_test_generator)
builder.add_node("aggregator", aggregator)

# Step 5: Edges banao - START se sab 4 agents tak (fan-out/parallel)
builder.add_edge(START, "static_analyzer")
builder.add_edge(START, "security_scanner")
builder.add_edge(START, "doc_generator")
builder.add_edge(START, "test_generator")

# Step 6: Sab 4 agents se aggregator tak (fan-in)
builder.add_edge("static_analyzer", "aggregator")
builder.add_edge("security_scanner", "aggregator")
builder.add_edge("doc_generator", "aggregator")
builder.add_edge("test_generator", "aggregator")

builder.add_edge("aggregator", END)

# Step 7: Graph ko compile karo (ready-to-run banao)
graph = builder.compile()


if __name__ == "__main__":
    initial_state = {"filepath": "data/sample_code.py"}
    graph.invoke(initial_state)