# Specification: AI-Enabled Profile Site

## 1. Profile Schema (JSON)
The profile data is structured under profile.json with the following schema:

```json
{
  "person": {
    "name": "Jeevan Gowda Kumaraswamy",
    "role": "Computer Science Senior @ Trinity College",
    "bio": "Developer specializing in polyglot backends, microservices, and applied cryptographic systems."
  },
  "projects": [
    {
      "name": "Campus Events Navigator",
      "what_is_this": "A polyglot microservices platform for tracking and discovering campus events.",
      "why_this_choice": "Built to explore Kubernetes orchestration, Python FastAPI, and Spring Boot service integration.",
      "what_breaks": "High latency during initial cold starts when scaling down container pods under low resources.",
      "what_did_i_learn": "Managing inter-service communication via NGINX Ingress and containerized state management using Redis."
    }
  ],
  "shipped_skills": ["Python", "Java", "Docker", "Kubernetes", "Git", "Spring Boot", "FastAPI"],
  "learning_goals": ["Zero-Knowledge Proofs (zk-SNARKs)", "Neo4j Graph Processing"]
}
```

## 2. Not Yet Inventory
Skills and tools deliberately not prioritized at present:

1. C++ Game Engine Development: Prioritized web microservices and cryptographic backend architectures over low-level graphics rendering.
2. Kubernetes Production Cluster Administration: Focused on application-level container orchestration in local homelabs rather than enterprise multi-region cloud ops.
3. Mobile App Development (React Native / Swift): Focused on backend REST API development and browser-based frontends rather than mobile platforms.

## 3. Language & Model Decisions

- Frontend/Backend Stack: Static HTML/CSS frontend with a Python FastAPI serverless backend function.
- Primary Model: anthropic/claude-3.5-haiku via OpenRouter.
- Alternative Model for Comparison: nvidia/nemotron-3-ultra-550b-a55b:free or openai/gpt-4o-mini.
