"""Strict input contracts for the authenticated API."""
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AwareDatetime,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
    model_validator,
)

from platform_schemas import Input, Name, Title
from sports import Score

Version = Annotated[int, Field(strict=True, ge=1)]
Identifier = Annotated[int, Field(strict=True, ge=1)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class VersionInput(Input):
    version: Version


class Credentials(Input):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr

    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        value = value.strip().casefold()
        if value.count('@') != 1 or any(c.isspace() for c in value) or not all(value.split('@')):
            raise ValueError('Indirizzo email non valido')
        return value

    @field_validator('password')
    @classmethod
    def password_valid(cls, value):
        if not 12 <= len(value.get_secret_value()) <= 128:
            raise ValueError('La password richiede 12–128 caratteri')
        return value


class RegisterInput(Credentials):
    display_name: Name


class TournamentCreate(Input):
    name: Title
    description: str = Field(default='', max_length=1000)
    variant_id: str = 'football-5'
    config: dict = Field(default_factory=dict)
    format: Literal['round_robin', 'knockout', 'groups'] = 'round_robin'
    team_names: list[Name] = Field(default_factory=list, max_length=32)
    legs: int = Field(default=1, strict=True, ge=1, le=2)
    group_count: int = Field(default=2, strict=True, ge=2, le=8)
    qualifiers: int = Field(default=2, strict=True, ge=1, le=2)
    random_seed: Annotated[int, Field(strict=True, ge=0, le=2147483647)] | None = None


class TournamentEdit(VersionInput):
    name: Title | None = None
    description: str | None = Field(default=None, max_length=1000)


class RulesInput(VersionInput):
    variant_id: str
    config: dict


class TeamCreate(Input):
    name: Name
    max_members: Annotated[int, Field(strict=True, ge=1, le=1000)] | None = None


class TeamEdit(TeamCreate, VersionInput):
    pass


class OrderInput(VersionInput):
    ordered_team_ids: list[Identifier] = Field(max_length=32)


class PenaltyInput(VersionInput):
    points: int = Field(strict=True, ge=0, le=999)
    reason: Reason


class StudentInput(Input):
    display_name: Name
    user_id: Identifier | None = None


class TeamAssignment(VersionInput):
    team_id: Identifier | None


class EnrollmentInput(Input):
    team_id: Identifier | None = None
    team_version: Version | None = None


class EnrollmentReview(VersionInput):
    decision: Literal['approve', 'reject']
    reason: str = Field(default='', max_length=500)


class ProposalInput(Input):
    match_version: Version
    score: Score


class ResultInput(Input):
    match_version: Version
    score: Score
    reason: Reason
    invalidate: bool = Field(default=False, strict=True)


class ResultClear(Input):
    match_version: Version
    reason: Reason
    invalidate: bool = Field(default=False, strict=True)


class ProposalReview(Input):
    decision: Literal['approve', 'reject', 'correct']
    proposal_version: Version
    match_version: Version
    invalidate: bool = Field(default=False, strict=True)
    score: Score | None = None
    reason: str = Field(default='', max_length=500)

    @model_validator(mode='after')
    def review_fields(self):
        if self.decision in ('reject', 'correct') and not self.reason.strip():
            raise ValueError('Specificare una motivazione')
        if (self.decision == 'correct') != (self.score is not None):
            raise ValueError('Il punteggio sostitutivo è richiesto soltanto per correct')
        return self


class PublicationInput(VersionInput):
    published: bool = Field(strict=True)


class InviteInput(Input):
    team_id: Identifier | None = None
    expires_at: AwareDatetime
    max_uses: int = Field(strict=True, ge=1, le=1000)
    require_approval: bool = Field(default=True, strict=True)


class TokenInput(Input):
    token: str = Field(min_length=20, max_length=200)


class VenueInput(Input):
    name: Name


class Availability(Input):
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode='after')
    def interval(self):
        if self.ends_at <= self.starts_at:
            raise ValueError('Intervallo non valido')
        return self


class FieldInput(Input):
    name: Name
    venue_id: Identifier | None = None
    sport_variant_ids: list[str] = Field(min_length=1, max_length=20)
    availability: list[Availability] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def intervals(self):
        ordered = sorted(self.availability, key=lambda x: x.starts_at)
        if any(a.ends_at > b.starts_at for a, b in zip(ordered, ordered[1:])):
            raise ValueError('Disponibilità sovrapposte')
        return self


class FieldEdit(FieldInput, VersionInput):
    pass


class ScheduleInput(VersionInput):
    scheduled_at: AwareDatetime | None
    timezone: str
    field_id: Identifier | None
    duration: int = Field(strict=True, ge=1, le=240)

    @model_validator(mode='after')
    def valid_zone(self):
        try:
            zone = ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Timezone IANA non valida')
        if self.scheduled_at and self.scheduled_at.astimezone(zone).utcoffset() != self.scheduled_at.utcoffset():
            raise ValueError('Offset incoerente con la timezone nella data indicata')
        if self.field_id is not None and self.scheduled_at is None:
            raise ValueError('Un campo richiede data e ora')
        return self
