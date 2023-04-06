# github-issues-dot

Convert issues into a simple diagram showing dependencies.

Currently very hardcoded and executing is simply

```sh
# Query Github to get data required (slow)
bash baseline.sh
# Use data to generate out.mmd
python process.py
```

Note: This is in "ugly but useful" category of intent, not refined tool area.
