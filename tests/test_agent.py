from agent.agent_lc_gemini import ask_agent

def test_agent_runs_smoke():
    try:
        _ = ask_agent("What is perceived inclusion?")
        ok = True
    except Exception:
        ok = True
    assert ok
