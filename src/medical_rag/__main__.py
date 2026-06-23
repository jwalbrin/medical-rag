"""
Entry point for `python -m medical_rag` and the `medical-rag` CLI command.

Usage:
    medical-rag load
    medical-rag embed
    medical-rag query "what causes sepsis?"
    medical-rag pipeline
"""

import argparse
import sys

from .config import Settings, settings as default_settings


def cmd_load(args, settings: Settings):
    if args.pql:
        settings.pql = args.pql
    if args.pqu:
        settings.pqu = args.pqu
    if args.db:
        settings.db = args.db
    from . import load_data
    load_data.run(settings)


def cmd_embed(args, settings: Settings):
    from . import embed
    embed.run(settings)


def cmd_query(args, settings: Settings):
    from . import query
    query.run(settings, question=args.question)


def cmd_pipeline(args, settings: Settings):
    from . import load_data, embed
    load_data.run(settings)
    embed.run(settings)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="medical-rag",
        description="RAG pipeline over PubMedQA",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # load
    p_load = sub.add_parser("load", help="Load PubMedQA JSON files into SQLite")
    p_load.add_argument("--pql", type=str, default=None, help="Override PQL env var")
    p_load.add_argument("--pqu", type=str, default=None, help="Override PQU env var")
    p_load.add_argument("--db", type=str, default=None, help="Override DB env var")

    # embed
    sub.add_parser("embed", help="Embed documents into a vector store")

    # query
    p_query = sub.add_parser("query", help="Query the RAG pipeline")
    p_query.add_argument("question", type=str, help="Question to ask")

    # pipeline
    sub.add_parser("pipeline", help="Run all stages end-to-end")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "load": cmd_load,
        "embed": cmd_embed,
        "query": cmd_query,
        "pipeline": cmd_pipeline,
    }
    dispatch[args.command](args, default_settings)


if __name__ == "__main__":
    main()
