#!/bin/bash
source /home/pgnair/envs/squid_env2.0/bin/activate

/home/pgnair/envs/squid_env2.0/bin/python -W ignore /home/pgnair/stage/new_verif/running_estimation.py 0.05 400 optimhf

echo t05_400_iters_job executed on $(date) >> /home/pgnair/stage/new_verif/logs/running_estimation_jobs.log