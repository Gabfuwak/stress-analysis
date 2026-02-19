#!/usr/bin/env python
import pandas as pd
import glob
import re
import os


def parse_condition_intervals(subject_id, folder='data'):
    PARIS_OFFSET_MS = 3_600_000
    lines = []
    with open(f"{folder}/{subject_id}/{subject_id}_input.csv", 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(';') if p.strip()]

            # Extract name and timestamp
            match = re.match(r'start\s*-\s*(.*?)\s*-\s*([\d.]+)', parts[0])
            if not match:
                continue
            name = match.group(1).strip()
            timestamp = int(parts[1])
            rep = None
            for p in parts[2:]:
                if 'rep' in p:
                    rep = int(p.split('=')[-1].strip())
            lines.append({'name': name, 'timestamp': timestamp, 'rep': rep})

    def get_condition(name):
        # LevelXX_ES_point -> ES, LevelXX_NE_point_empty -> NE_empty
        name = re.sub(r'^Level\d+_', '', name)  # strip Level00_
        name = name.replace('_point', '')        # strip _point
        return name

    level_rows = []
    condition_counts = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        # Start of a condition block: Level line with rep
        if line['rep'] is not None and re.match(r'Level00_', line['name']):
            condition = get_condition(line['name'])
            start_ts = line['timestamp']

            # Skip to the empty00 after this block
            j = i + 1
            while j < len(lines) and lines[j]['rep'] is not None:
                j += 1
            # lines[j] should be the empty00
            end_ts = lines[j]['timestamp'] if j < len(lines) else None

            rep_count = condition_counts.get(condition, 0)
            condition_counts[condition] = rep_count + 1

            # Extract per-level intervals within this block
            block_lines = lines[i:j]  # all Level lines in this block
            for k, lvl_line in enumerate(block_lines):
                level_num = int(re.match(r'Level(\d+)_', lvl_line['name']).group(1))
                lvl_start = lvl_line['timestamp']
                lvl_end = block_lines[k + 1]['timestamp'] if k + 1 < len(block_lines) else end_ts
                level_rows.append({
                    'condition': condition, 'rep': rep_count,
                    'level': level_num, 'start': lvl_start*1000 - PARIS_OFFSET_MS, 'end': lvl_end*1000 - PARIS_OFFSET_MS # convert timestamp in seconds to miliseconds to match shimmer data and correct time zone
                })


            i = j  # continue from the empty00
        else:
            i += 1

    return pd.DataFrame(level_rows)


def process_subject(data_files, level_intervals):
    # Concatenate all raw sensor files
    sensor_df = pd.concat(data_files, ignore_index=True)
    ts_col = 'Shimmer_A679_TimestampSync_Unix_CAL'

    exp_start = level_intervals["start"].min()
    exp_end   = level_intervals["end"].max()
    sensor_df = sensor_df[
        (sensor_df[ts_col] >= exp_start) & (sensor_df[ts_col] < exp_end)
    ].copy()

    segments = []
    for _, row in level_intervals.iterrows():
        mask = (sensor_df[ts_col] >= row['start']) & (sensor_df[ts_col] < row['end'])
        segment = sensor_df[mask].copy()
        segment['condition'] = row['condition']
        segment['rep'] = row['rep']
        segment['level'] = row['level']
        segments.append(segment)

    result = pd.concat(segments, ignore_index=True)

    # Reorder columns so tags come first
    tag_cols = ['condition', 'rep', 'level', ts_col]
    other_cols = [c for c in result.columns if c not in tag_cols]
    return result[tag_cols + other_cols]

def load_shimmer(f):
    df = pd.read_csv(f, sep='\t', skiprows=[0, 2])
    return df.drop(columns=[c for c in df.columns if c.startswith('Unnamed')])


def extract_data_from_folder(folder='data'):
    subject_ids = [d for d in os.listdir(folder) if os.path.isdir(f'{folder}/{d}')]

    all_subjects = {}
    for subject_id in subject_ids:
        raw_data_files = [f for f in glob.glob(f"{folder}/{subject_id}/*/*.csv") 
                          if not os.path.basename(os.path.dirname(f)).startswith('!')]
        try:
            data_files = [load_shimmer(f) for f in raw_data_files]
            level_intervals = parse_condition_intervals(subject_id, folder)
            all_subjects[subject_id] = process_subject(data_files, level_intervals)
            print(f"Loaded {subject_id}: {len(all_subjects[subject_id])} rows")
        except Exception as e:
            print(f"Error processing {subject_id}: {e}")

    return all_subjects


if __name__ == "__main__":
    all_subjects = extract_data_from_folder()

    for subject_id, df in all_subjects.items():
        print(f"\n{subject_id}: {list(df.columns)}")

