#!/bin/bash
source /home/pgnair/envs/squid_env2.0/bin/activate

/home/pgnair/envs/squid_env2.0/bin/python -W ignore /home/pgnair/stage/estimation_dist/estimation_comparison_seeded_var.py perfect 10000

echo perfect_seeded_job executed on $(date) >> /home/pgnair/stage/estimation_dist/logs/seeded_jobs.log