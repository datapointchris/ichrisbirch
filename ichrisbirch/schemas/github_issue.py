from pydantic import BaseModel


class GithubIssueCreate(BaseModel):
    title: str
    description: str = ''
    labels: list[str] = []


class GithubIssueResponse(BaseModel):
    html_url: str
    number: int
    title: str
