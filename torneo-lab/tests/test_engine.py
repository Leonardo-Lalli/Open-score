import pytest
from engine import round_robin, knockout_plan, build_standings


@pytest.mark.parametrize('n',[2,3,4,5,8,16,32])
@pytest.mark.parametrize('legs',[1,2])
def test_round_robin_invariants(n,legs):
    fixtures=round_robin(list(range(1,n+1)),legs)
    assert len(fixtures)==n*(n-1)//2*legs
    pairs=[tuple(sorted((a,b))) for _,a,b in fixtures]
    assert len(set(pairs))==n*(n-1)//2
    assert all(pairs.count(pair)==legs for pair in set(pairs))
    for r in {r for r,_,_ in fixtures}:
        participants=[p for turn,a,b in fixtures if r==turn for p in (a,b)]
        assert len(set(participants))==len(participants)
    if legs==2:
        assert {(a,b) for _,a,b in fixtures}=={(a,b) for a in range(1,n+1) for b in range(1,n+1) if a!=b}


@pytest.mark.parametrize('n',range(2,33))
def test_bracket_tree_and_byes(n):
    plan=knockout_plan(list(range(1,n+1)))
    first=[m for m in plan if m['round_no']==1]
    participants=[p for m in first for p in (m['home_team_id'],m['away_team_id']) if p is not None]
    assert sorted(participants)==list(range(1,n+1))
    assert len(plan)==(1<<(n-1).bit_length())-1
    assert sum(not m['is_bye'] for m in plan)==n-1
    assert first[0]['home_team_id']==1
    for i,m in enumerate(plan):
        if m['source_home'] is not None:
            assert m['source_home']<i and m['source_away']<i


def test_seed_reproducible():
    ids=list(range(1,17))
    assert knockout_plan(ids,42)==knockout_plan(ids,42)
    assert knockout_plan(ids,42)!=knockout_plan(ids,43)
    assert ids==list(range(1,17))


@pytest.mark.parametrize('ids',[[1],[1,1],list(range(33))])
def test_invalid_participants(ids):
    with pytest.raises(ValueError):round_robin(ids)
    with pytest.raises(ValueError):knockout_plan(ids)


def test_standings_ignore_unplayed_and_count_zero_draw():
    teams=[dict(id=1,name='Alfa'),dict(id=2,name='Beta'),dict(id=3,name='Gamma')]
    games=[dict(home_team_id=1,away_team_id=2,home_score=0,away_score=0),
           dict(home_team_id=1,away_team_id=3,home_score=None,away_score=None)]
    table=build_standings(teams,games)
    assert table[0]['points']==1 and table[0]['drawn']==1
    assert table[2]['played']==0
    assert sum(t['played'] for t in table)==2


def test_custom_points_and_correction():
    teams=[dict(id=1,name='Alfa'),dict(id=2,name='Beta')]
    games=[dict(home_team_id=1,away_team_id=2,home_score=3,away_score=1)]
    assert build_standings(teams,games,2,1,0)[0]['points']==2
    games[0]['away_score']=4
    assert build_standings(teams,games)[0]['team_id']==2
