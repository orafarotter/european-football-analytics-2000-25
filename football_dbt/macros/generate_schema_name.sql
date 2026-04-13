-- macros/generate_schema_name.sql
--
-- Override dbt's default schema naming behaviour.
-- Without this macro, dbt generates names like "<target_schema>_eu_football_staging",
-- which would NOT match the BigQuery datasets created by Terraform.
-- With this macro, the exact dataset name configured in dbt_project.yml is used.

{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}