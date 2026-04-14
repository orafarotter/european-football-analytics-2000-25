-- Staging model for match data

with source as (

    select * from {{ source('eu_football_raw', 'raw_matches') }}

),

renamed as (

    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['Division', 'MatchDate', 'HomeTeam', 'AwayTeam', 'FTHome', 'FTAway']) }}  as match_id,

        -- Match metadata
        Division                                        as division,

        safe_cast(MatchDate as DATE)                    as match_date,

        HomeTeam                                        as home_team,
        AwayTeam                                        as away_team,

        -- Full-time goals
        safe_cast(FTHome as INT64)                      as home_goals_ft,
        safe_cast(FTAway as INT64)                      as away_goals_ft,
        FTResult                                        as full_time_result,

        -- Half-time goals
        safe_cast(HTHome as INT64)                      as home_goals_ht,
        safe_cast(HTAway as INT64)                      as away_goals_ht,
        HTResult                                        as half_time_result,

        -- ELO ratings and recent form
        safe_cast(HomeElo    as FLOAT64)                as home_elo,
        safe_cast(AwayElo    as FLOAT64)                as away_elo,
        safe_cast(Form3Home  as FLOAT64)                as form_3_home,
        safe_cast(Form5Home  as FLOAT64)                as form_5_home,
        safe_cast(Form3Away  as FLOAT64)                as form_3_away,
        safe_cast(Form5Away  as FLOAT64)                as form_5_away,

        -- Match stats
        safe_cast(HomeShots   as INT64)                 as home_shots,
        safe_cast(AwayShots   as INT64)                 as away_shots,
        safe_cast(HomeTarget  as INT64)                 as home_shots_on_target,
        safe_cast(AwayTarget  as INT64)                 as away_shots_on_target,
        safe_cast(HomeFouls   as INT64)                 as home_fouls,
        safe_cast(AwayFouls   as INT64)                 as away_fouls,
        safe_cast(HomeCorners as INT64)                 as home_corners,
        safe_cast(AwayCorners as INT64)                 as away_corners,
        safe_cast(HomeYellow  as INT64)                 as home_yellow_cards,
        safe_cast(AwayYellow  as INT64)                 as away_yellow_cards,
        safe_cast(HomeRed     as INT64)                 as home_red_cards,
        safe_cast(AwayRed     as INT64)                 as away_red_cards,

        -- Average market odds
        safe_cast(OddHome as FLOAT64)                   as odds_home,
        safe_cast(OddDraw as FLOAT64)                   as odds_draw,
        safe_cast(OddAway as FLOAT64)                   as odds_away,

        -- Maximum market odds
        safe_cast(MaxHome as FLOAT64)                   as odds_max_home,
        safe_cast(MaxDraw as FLOAT64)                   as odds_max_draw,
        safe_cast(MaxAway as FLOAT64)                   as odds_max_away,

        -- Over / Under 2.5 goals market
        safe_cast(Over25    as FLOAT64)                 as odds_over_25,
        safe_cast(Under25   as FLOAT64)                 as odds_under_25,
        safe_cast(MaxOver25  as FLOAT64)                as odds_max_over_25,
        safe_cast(MaxUnder25 as FLOAT64)                as odds_max_under_25

    from source
    where MatchDate is not null
      and HomeTeam  is not null
      and AwayTeam  is not null

),

with_league_info as (

    select
        r.*,
        l.country,
        l.league_name,
        extract(year from r.match_date)                 as match_year
    from renamed r
    left join {{ ref('leagues') }} l
        on r.division = l.code

)

select * from with_league_info