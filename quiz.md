# Quiz — Amazon Bedrock

Test what you picked up from the guide. 5 questions, answers collapsed below each one.

---

## 1. What does Amazon Bedrock actually host for you?

A. Your own GPUs and training jobs
B. Foundation models from multiple providers, behind one serverless API
C. Only Amazon's own Titan models
D. A chatbot UI — no API access

<details>
<summary>Answer</summary>

**B.** Bedrock is a managed model API: Claude, Titan, Llama, Mistral and more behind one interface. You never provision GPUs or run model servers — that is the whole point. (A describes SageMaker training / self-hosting; C is wrong, Bedrock is multi-provider; D is wrong, the API is the product.)

</details>

---

## 2. Why is RAG (Knowledge Bases) usually better than fine-tuning when your documents change every week?

A. Fine-tuning is cheaper
B. RAG reads the latest documents at query time, so updates are just a re-ingest — no retraining
C. Fine-tuning cannot use company documents at all
D. RAG models are always more accurate than fine-tuned ones

<details>
<summary>Answer</summary>

**B.** With RAG the model retrieves fresh chunks on every question, so a document update is live as soon as the Knowledge Base re-ingests it. Fine-tuning bakes knowledge into weights — every update means another training run, cost and delay. (A is backwards; C is false; D is too absolute — fine-tuning still wins for style or narrow tasks.)

</details>

---

## 3. What do Bedrock Guardrails filter?

A. Only the model's output
B. Only the user's prompt
C. Both the input prompt and the model output — content filters, PII redaction, denied topics
D. Nothing — Guardrails only log, never block

<details>
<summary>Answer</summary>

**C.** Guardrails sit on both sides of the call: they can block or redact the incoming prompt (PII, blocked topics) and filter the generated answer before it reaches the user. They can also be configured to intervene rather than just log.

</details>

---

## 4. You switch from Claude Sonnet to Titan Text Lite and your bill drops sharply. What is the most likely reason?

A. Titan is hosted in a cheaper region
B. Per-token prices differ hugely between models — Sonnet costs roughly 10× Titan Lite per input token
C. Titan answers are always shorter
D. Bedrock charges per model, not per token

<details>
<summary>Answer</summary>

**B.** Pricing is per 1K input/output tokens and varies by an order of magnitude across models. Model choice is the single biggest cost lever in Bedrock — check the pricing table in the README before scaling any workload. (A is wrong, region pricing differences are small; C is incidental; D is false.)

</details>

---

## 5. Your RAG answers keep citing irrelevant documents. What should you tune first?

A. Increase the model's temperature
B. The chunk size and `top-k` retrieval count — smaller, better chunks beat big noisy ones
C. Buy Provisioned Throughput
D. Add more Guardrails

<details>
<summary>Answer</summary>

**B.** Retrieval quality is the bottleneck: oversized chunks dilute relevance and a high `top-k` pulls in noise that the model then has to sort through. Tune chunk size and `top-k`, and measure retrieval scores in CloudWatch before touching the model settings. (A changes creativity, not relevance; C fixes throughput, not quality; D filters content, it does not improve retrieval.)

</details>

---

**Score guide:** 5/5 — you could explain Bedrock to a teammate. 3–4 — re-read the RAG and cost sections. 0–2 — start from the TL;DR and the architecture diagram, then retry.
