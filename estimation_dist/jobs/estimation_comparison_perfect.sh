#!/bin/bash
source /home/pgnair/envs/squid_env2.0/bin/activate

/home/pgnair/envs/squid_env2.0/bin/python -W ignore /home/pgnair/stage/estimation_dist/estimation_comparison_var.py perfect

echo estimation_comparison_job executed on $(date) >> /home/pgnair/stage/estimation_dist/logs/jobs.log