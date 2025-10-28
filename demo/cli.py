import argparse
from agent.logging_conf import setup_logging
from agent.build_index import build_index
from agent.agent_lc_gemini import ask_agent

if __name__ == "__main__":
    setup_logging()
    p = argparse.ArgumentParser()
    p.add_argument("--cmd", choices=["index", "ask"], required=True)
    p.add_argument("--q")
    p.add_argument("--corpus", default="./corpus")
    args = p.parse_args()

    if args.cmd == "index":
        build_index(args.corpus)
    elif args.cmd == "ask":
        if not args.q: raise SystemExit("--q is required for ask")
        print(ask_agent(args.q))
