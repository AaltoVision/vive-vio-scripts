# python scripts/plot_distances.py -i data/processed/arcore-new-better-ds1000.jsonl
python scripts/find_position_jumps.py -i data/processed/arcore-new-better-ds1000.jsonl
# jq -c 'select(.time>15.0)' data/processed/arcore-new-better-ds1000.jsonl
