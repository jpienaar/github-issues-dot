import json
import os
import re
import subprocess
import sys
from textwrap import wrap
from unionfind import unionfind

include_closed = True

class Issue:
  def __init__(self, title, state, milestone):
    self.title = '"{}"'.format(
        "<br/>".join(wrap(re.sub('"', '_', title), width=20, break_long_words=False)))
    self.state = state
    self.milestone = milestone

def load_issues():
  dec = json.JSONDecoder()
  t = []
  pos = 0
  with open("issues.json", "rt") as f:
    data = f.read().rstrip()
    while not pos == len(str(data)):
      j, read = dec.raw_decode(str(data)[pos:])
      pos += read
      t.append(j)
  issues = {}
  for iss in t:
    issues_data = iss["data"]["repository"]["issues"]["nodes"]
    for issue in issues_data:
      issues[issue["number"]] = Issue(issue["title"], issue["state"], issue["milestone"])
  return issues

def load_milestones():
  with open("milestones.json", "rt") as f:
    nodes = json.load(f)["data"]["repository"]["milestones"]["nodes"]
    milestones = {}
    for m in nodes:
      if False and not include_closed and m["closed"]:
        continue
      milestones[m["number"]] = m["title"]
    return milestones

def load_cross_referenced(issues):
  dec = json.JSONDecoder()
  t = []
  pos = 0
  with open("cross_referenced.json", "rt") as f:
    data = f.read().rstrip()
    while not pos == len(str(data)):
      j, read = dec.raw_decode(str(data)[pos:])
      pos += read
      t.append(j)
  ret = {}
  for c in t:
    for i in c["data"]["repository"]["issues"]["edges"]:
      num = i["node"]["number"]
      if not include_closed and issues[num].state == "CLOSED":
        continue
      ret[num] = []
      for j in i["node"]["timelineItems"]["nodes"]:
        if j["isCrossRepository"] or not j["source"] or not j["source"]["number"]:
          continue
        ret[num].append(j["source"]["number"])
  return ret

issues = load_issues()
milestones = load_milestones()
cross_referenced = load_cross_referenced(issues)

filtered_milestones = set()

u = unionfind(max(issues.keys()) + 1)
for src in cross_referenced.keys():
  for dst in cross_referenced[src]:
    u.unite(src, dst)

def include_node(n):
  key = 9368
  return u.issame(n, key)

with open("out.mmd", "w") as f:
  f.write("flowchart TB\n")
  for src in cross_referenced.keys():
    for dst in cross_referenced[src]:
      if not include_node(src):
        continue
      f.write(f'  {src} --> {dst}\n')
      if issues[dst].milestone:
        filtered_milestones.add(issues[dst].milestone["number"])
      if issues[src].milestone:
        filtered_milestones.add(issues[src].milestone["number"])

  for m in milestones.keys():
    if m not in filtered_milestones:
      continue
    f.write(f'  subgraph {milestones[m]}\n')
    for k in issues.keys():
      if not include_node(k):
        continue
      if issues[k].milestone and issues[k].milestone["number"] == m:
        f.write(f'    {k}({issues[k].title})\n')
        f.write(f'    click {k} https://github.com/openxla/iree/issues/{k}\n')
    f.write('  end')
  for k in issues.keys():
    if not include_node(k):
      continue
    if not issues[k].milestone:
      f.write(f'  {k}({issues[k].title})\n')
      f.write(f'    click {k} "https://github.com/openxla/iree/issues/{k}"\n')

