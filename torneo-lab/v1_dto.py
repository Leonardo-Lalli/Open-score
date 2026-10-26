"""Response schemas shared with clients through generated OpenAPI."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict


class Output(BaseModel):
    model_config = ConfigDict(extra='forbid')


T = TypeVar('T')


class Page(Output, Generic[T]):
    items: list[T]
    next_cursor: int | None


class Id(Output):
    id: int


class Csrf(Output):
    csrf_token: str


class User(Output):
    id: int
    display_name: str
    role: str
    organization_id: int | None


class Login(Output):
    user: User
    csrf_token: str


class Team(Output):
    id: int
    tournament_id: int
    name: str
    group_id: int | None
    source_id: int | None
    display_order: int
    max_members: int | None
    archived: int
    version: int


class TeamBrief(Output):
    id: int
    name: str
    group_id: int | None
    display_order: int


class StudentTeam(TeamBrief):
    version: int


class TeamsPage(Page[Team | StudentTeam]):
    order_version: int


class Student(Output):
    id: int
    tournament_id: int
    user_id: int | None
    display_name: str
    team_id: int | None
    version: int


class Participation(Output):
    student: Student | None


class Enrollment(Output):
    id: int
    tournament_id: int
    user_id: int
    team_id: int | None
    invite_id: int | None
    status: str
    reason: str | None
    version: int


class FieldRef(Output):
    id: int
    name: str
    venue_id: int | None


class Match(Output):
    id: int
    tournament_id: int
    stage_id: int
    group_id: int | None
    round_no: int
    position: int
    home_team_id: int | None
    away_team_id: int | None
    source_home: int | None
    source_away: int | None
    home_score: int | None
    away_score: int | None
    winner_team_id: int | None
    is_bye: int
    version: int
    scheduled_at: str | None
    location: str | None
    duration: int
    field_id: int | None
    timezone: str | None
    score: dict[str, Any] | None
    field: FieldRef | None
    kind: str
    status: str


class Standing(Output):
    team_id: int
    name: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    penalty_points: int = 0
    sets_for: int | None = None
    sets_against: int | None = None
    set_difference: int | None = None
    rallies_for: int | None = None
    rallies_against: int | None = None
    rally_difference: int | None = None


class Stage(Output):
    id: int
    tournament_id: int
    ordinal: int
    kind: str


class Group(Output):
    id: int
    stage_id: int
    name: str
    standings: list[Standing]


class Progress(Output):
    completed: int
    total: int


class Tournament(Output):
    id: int
    name: str
    sport: str
    format: str
    description: str
    participant_kind: str
    win_points: int
    draw_points: int
    loss_points: int
    legs: int
    group_count: int
    qualifiers: int
    variant_id: str | None
    created_at: str
    rules: dict[str, Any] | None
    version: int | None = None
    order_version: int | None = None
    published: bool | None = None
    public_slug: str | None = None


class Audit(Output):
    id: int
    action: str
    created_at: str
    actor_id: int | None


class Detail(Output):
    tournament: Tournament
    teams: list[TeamBrief]
    matches: list[Match]
    groups: list[Group]
    stages: list[Stage]
    standings: list[Standing]
    champion_team_id: int | None
    status: str
    progress: Progress
    public: bool
    audit: list[Audit] | None = None


class Summary(Tournament):
    status: str
    progress: Progress
    team_count: int
    champion_team_id: int | None


class Review(Output):
    id: int
    tournament_id: int
    match_id: int
    proposal_id: int | None
    reviewed_by: int
    decision: str
    reason: str
    created_at: str


class Proposal(Output):
    id: int
    tournament_id: int
    match_id: int | None
    original_match_id: int
    submitted_by: int
    score: dict[str, Any]
    match_version: int
    version: int
    status: str
    created_at: str
    review: Review | None
    stale: bool


class Official(Output):
    id: int | None
    match_id: int
    score: dict[str, Any]
    approved_by: int | None
    approved_at: str | None
    source_proposal_id: int | None
    winner_team_id: int | None
    version: int
    provenance: str | None = None


class Result(Output):
    official_result: Official | None
    match_version: int


class ResultMutation(Result):
    invalidated_match_ids: list[int]
    invalidated: int = 0


class ProposalReview(ResultMutation):
    proposal: Proposal


class Statistics(Output):
    team_count: int
    matches_total: int
    matches_completed: int
    matches_remaining: int
    completion_percentage: float
    phases_pending_generation: bool
    champion_team_id: int | None
    qualified_team_ids: list[int]
    standings: list[Standing]
    groups: list[Group]
    sport_statistics: dict[str, int]
    student_count: int | None = None
    pending_proposals: int | None = None


class Venue(Output):
    id: int
    owner_id: int
    organization_id: int
    name: str


class Field(Venue):
    venue_id: int | None
    sport_variant_ids: list[str]
    availability: list[dict[str, str]]
    archived: bool
    version: int
    description: str = ''
    availability_note: str = ''


class Invite(Output):
    id: int
    tournament_id: int
    team_id: int | None
    expires_at: str
    max_uses: int
    used: int
    require_approval: bool
    revoked: bool
    version: int


class CreatedInvite(Invite):
    token: str
    url: str


class Publication(Output):
    published: bool
    public_slug: str
    public_url: str
    version: int


class Order(Output):
    ordered_team_ids: list[int]
    version: int


class Penalty(Output):
    team_id: int
    points: int
    version: int


class Rules(Output):
    variant_id: str | None
    config: dict[str, Any] | None
    version: int


class RulesSchema(Output):
    variant_id: str
    defaults: dict[str, Any]
    rules_schema: dict[str, Any]
    result_schema: dict[str, Any]
    administrative_result_schema: dict[str, Any]
    standings_criteria: list[str]


class Standings(Output):
    rows: list[Standing]
    groups: list[Group]
    criteria: list[str]


class NextSlot(Output):
    match_id: int
    slot: str


class OfficialBrief(Output):
    score: dict[str, Any] | None
    winner_team_id: int | None


class BracketMatch(Match):
    next: NextSlot | None
    official_result: OfficialBrief | None


class Round(Output):
    round_no: int
    matches: list[BracketMatch]


class BracketStage(Output):
    id: int
    rounds: list[Round]


class Bracket(Output):
    stages: list[BracketStage]
    champion_team_id: int | None


class InviteValidation(Output):
    valid: bool
    tournament_name: str
    team_name: str | None
    expires_at: str
    requires_login: bool


class Error(Output):
    detail: str | list[dict[str, Any]]
    code: str
    current_version: int | None = None
