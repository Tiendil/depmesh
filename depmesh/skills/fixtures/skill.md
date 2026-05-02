# depmesh usage

`depmesh` prints configured dependencies for one or more artifacts.

- Use `depmesh --protocol llm show ARTIFACT...` when invoking it as a coding-agent tool.
- Use `depmesh --protocol automation show ARTIFACT...` when JSON Lines output is required.
- Use `depmesh show --relation BACKWARD_RELATION_ID ARTIFACT...` to query dependencies in the opposite direction.
- Use `depmesh show --relation RELATION_ID ARTIFACT...` to limit output to configured relations.
