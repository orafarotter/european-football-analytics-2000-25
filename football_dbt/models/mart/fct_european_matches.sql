-- Fact table: 10 strongest European Leagues only, with calculated metrics.
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
        'E0',   -- England:    Premier League
        'SP1',  -- Spain:      La Liga
        'I1',   -- Italy:      Serie A
        'D1',   -- Germany:    Bundesliga
        'F1',   -- France:     Ligue 1
        'B1',   -- Belgium:    Pro League
        'P1',   -- Portugal:   Primeira Liga
        'E1',   -- England:    Championship        
        'DEN',  -- Denmark:    Superliga
        'POL'   -- Poland:     Ekstraklasa
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

        case full_time_result
            when 'H' then 'Home Win'
            when 'A' then 'Away Win'
            when 'D' then 'Draw'
        end                                             as match_result_label,

        case 
            when home_goals_ft > away_goals_ft then home_goals_ft - away_goals_ft
            when away_goals_ft > home_goals_ft then away_goals_ft - home_goals_ft
            else 0
        end                                             as goal_difference,

        case 
            when (home_goals_ht + away_goals_ht)>0 and (home_goals_ht + away_goals_ht) = (home_goals_ft + away_goals_ft) then 'All Goals in First Half'
            when (home_goals_ht + away_goals_ht)=0 and (home_goals_ft + away_goals_ft)>0 then 'All Goals in Second Half'
            when (home_goals_ht + away_goals_ht)=0 and (home_goals_ft + away_goals_ft)=0 then 'No Goals'
            else 'Goals in Both Halves'
        end                                             as goal_timing,                     

        case
            when home_goals_ft + away_goals_ft = 0 then 'Goalless'
            when home_goals_ft + away_goals_ft <= 2 then 'Low Scoring'
            when home_goals_ft + away_goals_ft <= 4 then 'Normal'
            else 'High Scoring'
        end                                             as scoring_category

    from european_matches

)

select * from enriched