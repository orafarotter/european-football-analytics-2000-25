-- models/mart/fct_european_matches.sql
-- Fact table: main European leagues only, with calculated metrics.
--
-- Partitioned by match_date (YEAR granularity) → efficient time-range queries.
-- Clustered by division, league_name → efficient per-league queries in Looker Studio.

{{
    config(
        materialized='table',
        partition_by={
            "field": "match_date",
            "data_type": "date",
            "granularity": "year"
        },
        cluster_by=["division", "league_name"]
    )
}}

with european_matches as (

    select *
    from {{ ref('stg_matches') }}
    where division in (
        -- Top-flight leagues
        'E0',   -- England:     Premier League
        'SP1',  -- Spain:       La Liga
        'D1',   -- Germany:     Bundesliga
        'I1',   -- Italy:       Serie A
        'F1',   -- France:      Ligue 1
        'N1',   -- Netherlands: Eredivisie
        'B1',   -- Belgium:     Pro League
        'P1',   -- Portugal:    Primeira Liga
        'T1',   -- Turkey:      Süper Lig
        'SC0',  -- Scotland:    Premiership
        'G1',   -- Greece:      Super League
        -- Second-tier leagues (included to allow cross-tier analysis)
        'E1',   -- England:     Championship
        'SP2',  -- Spain:       Segunda División
        'D2',   -- Germany:     2. Bundesliga
        'I2',   -- Italy:       Serie B
        'F2'    -- France:      Ligue 2
    )
    and match_date     is not null
    and home_goals_ft  is not null
    and away_goals_ft  is not null

),

enriched as (

    select
        -- Keys
        match_id,

        -- Context
        division,
        country,
        league_name,
        match_date,
        match_year,

        -- Teams
        home_team,
        away_team,

        -- Goals (full-time)
        home_goals_ft,
        away_goals_ft,

        -- Goals (half-time — may be null)
        home_goals_ht,
        away_goals_ht,

        -- Results
        full_time_result,
        half_time_result,

        -- Performance metrics
        home_elo,
        away_elo,
        form_3_home,
        form_5_home,
        form_3_away,
        form_5_away,

        -- Match stats (sparse)
        home_shots,
        away_shots,
        home_shots_on_target,
        away_shots_on_target,
        home_corners,
        away_corners,
        home_yellow_cards,
        away_yellow_cards,
        home_red_cards,
        away_red_cards,

        -- Calculated metrics
        home_goals_ft + away_goals_ft                   as total_goals,
        home_goals_ft - away_goals_ft                   as goal_difference,

        case full_time_result
            when 'H' then 'Home Win'
            when 'A' then 'Away Win'
            when 'D' then 'Draw'
        end                                             as match_result_label,

        case
            when home_goals_ft + away_goals_ft = 0 then 'Goalless'
            when home_goals_ft + away_goals_ft <= 2 then 'Low Scoring'
            when home_goals_ft + away_goals_ft <= 4 then 'Normal'
            else 'High Scoring'
        end                                             as scoring_category,

        -- Betting odds
        odds_home,
        odds_draw,
        odds_away,
        odds_over_25,
        odds_under_25

    from european_matches

)

select * from enriched