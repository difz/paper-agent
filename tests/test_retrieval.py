import os
from agent.build_index import build_index
from agent.tools_gemini import retrieve_passages

def test_index_and_retrieve_smoke():
    # Skip if no PDFs; still keep CI green
    if not os.path.isdir("./corpus") or not any(f.endswith(".pdf") for f in os.listdir("./corpus")):
        assert True; return
    build_index("./corpus")
    out = retrieve_passages("test query")
    assert isinstance(out, str)
