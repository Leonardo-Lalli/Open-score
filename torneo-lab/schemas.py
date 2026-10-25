from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Score = Annotated[int, Field(strict=True, ge=0, le=999)]
Sport = Literal['Calcio', 'Calcio a 5', 'Basket', 'Pallamano', 'Badminton', 'Tennis', 'Pallavolo']
Format = Literal['round_robin', 'knockout', 'groups']
ParticipantKind = Literal['team', 'individual']
TournamentType = Literal['general', 'championship', 'cup']
ScoringSystem = Literal['points', 'sets', 'time']
Seed = Annotated[int, Field(strict=True, ge=0, le=2147483647)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class TournamentInput(Input):
    name: Title
    sport: Sport = 'Calcio'
    sport_id: Optional[int] = None
    format: Format = 'round_robin'
    description: str = Field(default='', max_length=1000)
    participant_kind: ParticipantKind = 'team'
    win_points: int = Field(default=3, strict=True, ge=0, le=10)
    draw_points: int = Field(default=1, strict=True, ge=0, le=10)
    loss_points: int = Field(default=0, strict=True, ge=0, le=10)
    legs: int = Field(default=1, strict=True, ge=1, le=2)
    group_count: int = Field(default=2, strict=True, ge=2, le=8)
    qualifiers: int = Field(default=2, strict=True, ge=1, le=2)
    random_seed: Optional[Seed] = None
    team_names: list[Name] = Field(default_factory=list, max_length=32)
    tournament_type: TournamentType = 'general'
    scoring_system: ScoringSystem = 'points'

    @model_validator(mode='after')
    def names_unique(self):
        if len({n.casefold() for n in self.team_names}) != len(self.team_names):
            raise ValueError('Nomi dei partecipanti duplicati')
        if self.format == 'knockout' and self.legs != 1:
            raise ValueError('La demo knockout prevede una sola gara per incontro')
        return self


class TournamentUpdate(Input):
    """Partial update. Structural fields are accepted only while the tournament is a draft."""

    name: Optional[Title] = None
    sport: Optional[Sport] = None
    sport_id: Optional[int] = None
    format: Optional[Format] = None
    description: Optional[str] = Field(default=None, max_length=1000)
    participant_kind: Optional[ParticipantKind] = None
    win_points: Optional[int] = Field(default=None, strict=True, ge=0, le=10)
    draw_points: Optional[int] = Field(default=None, strict=True, ge=0, le=10)
    loss_points: Optional[int] = Field(default=None, strict=True, ge=0, le=10)
    legs: Optional[int] = Field(default=None, strict=True, ge=1, le=2)
    group_count: Optional[int] = Field(default=None, strict=True, ge=2, le=8)
    qualifiers: Optional[int] = Field(default=None, strict=True, ge=1, le=2)
    random_seed: Optional[Seed] = None
    tournament_type: Optional[TournamentType] = None
    scoring_system: Optional[ScoringSystem] = None

    @model_validator(mode='after')
    def updatable(self):
        if not self.model_fields_set:
            raise ValueError('Nessun campo da aggiornare')
        if self.name is not None and len(self.name) < 2:
            raise ValueError('Il nome del torneo è troppo corto')
        if self.format == 'knockout' and self.legs not in (None, 1):
            raise ValueError('La demo knockout prevede una sola gara per incontro')
        return self


class TeamInput(Input):
    name: Name


class ResultInput(Input):
    home_score: Score
    away_score: Score
    version: int = Field(strict=True, ge=1)
    invalidate: bool = False


class ClearInput(Input):
    version: int = Field(strict=True, ge=1)
    invalidate: bool = False


class ScheduleInput(Input):
    scheduled_at: datetime | None = None
    location: str = Field(default='', max_length=80)
    duration: int = Field(default=20, strict=True, ge=1, le=240)
    version: int = Field(strict=True, ge=1)

    @model_validator(mode='after')
    def timezone_required(self):
        if self.scheduled_at and self.scheduled_at.utcoffset() is None:
            raise ValueError('La data deve includere il fuso orario')
        return self
