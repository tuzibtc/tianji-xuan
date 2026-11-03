# tianji-xuan

[中文](README.md) | English

A command-line toolkit for Zi Wei Dou Shu (紫微斗数) in the *Tianji* (《天纪》) tradition: chart casting, 13-topic natal readings, yearly / monthly / decade luck, compatibility (hepan), I Ching divination (卜卦), house feng shui (阳宅), face and palm reading (相法), character divination (测字), and feedback-based calibration. One entry point: `xuan`.

> Everything it outputs is a reference from a traditional-culture perspective, not a prediction, diagnosis, or investment or medical advice. Every conclusion ends with "仅供参考" (for reference only).

The data and command output are in Chinese. An assistant built on this tool should explain the results in whatever language the user speaks.

## Install

Requires git, Node.js ≥ 18 and Python ≥ 3.9.

```bash
git clone https://github.com/tuzibtc/tianji-xuan.git tianji-xuan && cd tianji-xuan
python3 -m pip install -r requirements.txt
bin/xuan setup            # clones the pinned upstream engine, runs npm ci, downloads and verifies the dataset (~155 MB)
bin/xuan info             # shows install status
```

All data lives in `XUAN_HOME` (default `~/.local/share/tianji-xuan`): the engine, dataset, models, people file, logs and calibration state. The repository itself contains no data.

Optional: `bin/xuan train` trains the rebuilt reading model from the local dataset, for natal readings of people born before 1950 or after 2026 (a full run needs about 15 GB of RAM and several hours; see `xuan train -h` for a small trial run).

## Usage

```bash
xuan chart  --date 1988-03-21 --gender female --clock 14:30 --lon 121.47   # chart (clock time → true solar time)
xuan natal  --date 1988-03-21 --gender female --hour 7 --topics wealth,career
xuan year   --date 1988-03-21 --gender female --hour 7 --year 2027
xuan month  --date 1988-03-21 --gender female --hour 7 --year 2026 --month 10   # lunar month
xuan hepan  --a-date 1988-03-21 --a-gender female --a-hour 7 --b-date 1986-11-02 --b-gender male --b-hour 2
xuan bugua  cast --asker user --q "Is this job change a good idea?" --coins 101100   # bottom line first, 1 = yang
xuan fengshui --rooms '{"西北":"厨房","东":"卧室"}' --people '{"男主人":"东"}'
xuan xiang  --part face      # face-reading rules
xuan cezi                    # character-divination rules
xuan log feedback <id> --verdict 准|不准|部分|未应 --note "what actually happened"   # accurate / inaccurate / partly / not yet
xuan calib-status
```

`--hour` is the double-hour index 0–11 (0 = 子 23:00–01:00, 1 = 丑, …). To use `--person <id>`, copy the format of `people.example.json` into `XUAN_HOME/people.json`.

## Public mode

`XUAN_PUBLIC=1` is the default: no internal confidence labels, no source attributions, episode numbers or timecodes, and "仅供参考" at the end of each conclusion. Set `XUAN_PUBLIC=0` during development to see the internal labels.

## Calibration

Each method (divination, feng shui, physiognomy, character divination, luck periods) keeps its own log. Accurate = 1, partly = 0.5, inaccurate = 0; "not yet" and test runs don't count. A method is reviewed after every 30 new feedback entries, and it passes once it has at least 100 entries since its last rule change with ≥ 90% accuracy.

## License and sources

- Code: MIT (see `LICENSE`, which keeps the upstream engine's copyright notice).
- The chart engine and the reading dataset come from upstream [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu). They are downloaded at install time, not distributed here; the dataset is CC BY 4.0, with attribution in `NOTICE`.
- This repository contains no text, lecture notes or transcripts from *Tianji*; rules and method notes are written in our own words.
