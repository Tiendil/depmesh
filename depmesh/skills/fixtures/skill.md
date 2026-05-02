# depmesh usage

`depmesh` prints configured dependencies for one or more artifacts.

- Use `depmesh --protocol llm dependencies ARTIFACT...` when invoking it as a coding-agent tool.
- Use `depmesh --protocol automation dependencies ARTIFACT...` when JSON Lines output is required.
- Use `depmesh relations` to list configured relations.
- Use `depmesh dependencies --relation RELATION_ID ARTIFACT...` to limit output to configured relations.
- Reverse lookups require explicitly configured reverse relations.
