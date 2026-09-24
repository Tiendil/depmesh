from llm_tool_cli.core.errors import EnvironmentError

from depmesh.skills.entities import SkillDocument


class SkillUnreadable(EnvironmentError):
    code: str = "skill_unreadable"
    message: str = "could not read skill document `{error.document}`: {error.reason}"
    document: SkillDocument
    reason: str
