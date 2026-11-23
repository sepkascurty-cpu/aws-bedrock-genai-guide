#!/usr/bin/env python3
"""Amazon Bedrock demo — Converse API, RAG via Knowledge Bases, cost estimate.

Read-only by default. --ask / --kb only call Bedrock; nothing is created.
Requires: pip install boto3 ; AWS credentials with bedrock:InvokeModel
and bedrock:Retrieve permissions (or run with --dry-run to print only).

Usage:
    python bedrock_demo.py --ask "Explain VPC peering in one paragraph"
    python bedrock_demo.py --kb kb-ABC123 --ask "What is our refund policy?"
    python bedrock_demo.py --list-models
    python bedrock_demo.py --estimate --input-tokens 1000000 --output-tokens 200000
    python bedrock_demo.py --ask "..." --dry-run
"""
import argparse
import json
import sys

# Approximate on-demand prices per 1K tokens (Nov 2026, us-east-1).
# Verify against the live Bedrock pricing page before budgeting.
MODEL_PRICES = {
    "anthropic.claude-sonnet-4-5-20250929-v1:0": (0.003, 0.015),
    "anthropic.claude-haiku-4-5-20250929-v1:0": (0.001, 0.005),
    "amazon.titan-text-lite-v1": (0.0003, 0.0004),
    "amazon.titan-text-express-v1": (0.0008, 0.0016),
    "meta.llama3-1-70b-instruct-v1:0": (0.00265, 0.0035),
    "mistral.mistral-large-2407-v1:0": (0.004, 0.012),
}

DEFAULT_MODEL = "anthropic.claude-haiku-4-5-20250929-v1:0"
SYSTEM_PROMPT = (
    "You are a helpful AWS cloud engineering assistant. "
    "Answer concisely, with a concrete example when it helps. "
    "If retrieved context is provided, ground your answer in it and say "
    "when the context does not contain the answer."
)


def get_clients(region):
    import boto3

    return boto3.client("bedrock-runtime", region_name=region), boto3.client(
        "bedrock-agent-runtime", region_name=region
    )


def ask_model(runtime, model_id, question, context_chunks=None):
    """One Converse API call, optionally grounded in retrieved chunks."""
    user_text = question
    if context_chunks:
        context = "\n\n".join(
            f"[Source {i + 1}] {c}" for i, c in enumerate(context_chunks)
        )
        user_text = (
            f"Use the context below to answer. If the answer is not in the "
            f"context, say so.\n\nContext:\n{context}\n\nQuestion: {question}"
        )
    response = runtime.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        inferenceConfig={"maxTokens": 1024, "temperature": 0.3},
    )
    text = "".join(
        block["text"] for block in response["output"]["message"]["content"]
        if "text" in block
    )
    usage = response.get("usage", {})
    return text, usage


def retrieve(agent_runtime, kb_id, question, top_k=5):
    """Retrieve top-k chunks from a Knowledge Base (no generation)."""
    resp = agent_runtime.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": question},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": top_k}
        },
    )
    chunks = []
    for r in resp.get("retrievalResults", []):
        chunks.append(r["content"]["text"])
        print(f"  - score {r.get('score', 0):.3f} | "
              f"{r.get('location', {}).get('s3Location', {}).get('uri', '?')}")
    return chunks


def estimate(model_id, input_tokens, output_tokens):
    in_price, out_price = MODEL_PRICES[model_id]
    cost = (input_tokens / 1000) * in_price + (output_tokens / 1000) * out_price
    print(f"Model: {model_id}")
    print(f"  Input : {input_tokens:,} tokens x ${in_price:.5f}/1K = "
          f"${(input_tokens / 1000) * in_price:,.2f}")
    print(f"  Output: {output_tokens:,} tokens x ${out_price:.5f}/1K = "
          f"${(output_tokens / 1000) * out_price:,.2f}")
    print(f"  Total: ${cost:,.2f}")
    return cost


def main():
    parser = argparse.ArgumentParser(description="Amazon Bedrock demo")
    parser.add_argument("--ask", help="Question to send to the model")
    parser.add_argument("--kb", help="Knowledge Base ID for RAG retrieval")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model ID")
    parser.add_argument("--top-k", type=int, default=5, help="Chunks to retrieve")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--list-models", action="store_true",
                        help="Print priced models and exit")
    parser.add_argument("--estimate", action="store_true",
                        help="Estimate cost for token volumes")
    parser.add_argument("--input-tokens", type=int, default=1_000_000)
    parser.add_argument("--output-tokens", type=int, default=200_000)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the request, call nothing")
    args = parser.parse_args()

    if args.list_models:
        print("Models with approximate on-demand pricing (per 1K tokens):")
        for model, (inp, out) in MODEL_PRICES.items():
            print(f"  {model}\n    in ${inp:.5f} / out ${out:.5f}")
        return 0

    if args.estimate:
        return 0 if estimate(args.model, args.input_tokens,
                             args.output_tokens) is not None else 1

    if not args.ask:
        parser.error("--ask is required (or use --list-models / --estimate)")

    if args.dry_run:
        print(json.dumps({
            "modelId": args.model,
            "knowledgeBaseId": args.kb,
            "system": SYSTEM_PROMPT,
            "question": args.ask,
            "topK": args.top_k,
        }, indent=2))
        return 0

    runtime, agent_runtime = get_clients(args.region)

    chunks = []
    if args.kb:
        print(f"Retrieving top-{args.top_k} chunks from KB {args.kb} ...")
        chunks = retrieve(agent_runtime, args.kb, args.ask, args.top_k)
        if not chunks:
            print("No chunks retrieved — answering without grounding.")

    print(f"Asking {args.model} ...")
    answer, usage = ask_model(runtime, args.model, args.ask, chunks)
    print("\n--- Answer ---\n" + answer)
    print("\n--- Usage ---")
    print(f"Input tokens: {usage.get('inputTokens')}, "
          f"output tokens: {usage.get('outputTokens')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
