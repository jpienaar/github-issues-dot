import json
import os
import re
import subprocess
import sys
from textwrap import wrap
from unionfind import unionfind

# Select all of key and milestone
issue_key = 3 # 12070 # 9368
milestone_key = 1
# [ i for i in milestones if milestones[i] == 'JAX Integration Completeness'][0]
gh_org = "jpienaar"
gh_name = "github-issues-dot"
# Whether to include closed issues
include_closed = True

# Colors per milestone number (random)
colorArray = [
    '#CAFF70',
    '#BCEE68',
    '#A2CD5A',
    '#6E8B3D',
    '#8FBC8F',
    '#C1FFC1',
    '#B4EEB4',
    '#9BCD9B',
    '#698B69',
    '#228B22',
    '#ADFF2F',
    '#7CFC00',
    '#90EE90',
    '#20B2AA',
    '#32CD32',
    '#3CB371',
    '#00FA9A',
    '#F5FFFA',
    '#6B8E23',
    '#C0FF3E',
    '#B3EE3A',
    '#9ACD32',
    '#698B22',
    '#98FB98',
    '#9AFF9A',
    '#90EE90',
    '#7CCD7C',
    '#548B54',
    '#2E8B57',
    '#54FF9F',
    '#4EEE94',
    '#43CD80',
    '#2E8B57',
    '#00FF7F',
    '#00FF7F',
    '#00EE76',
    '#00CD66',
    '#008B45',
    '#9ACD32',
    '#7FFF00',
    '#7FFF00',
    '#76EE00',
    '#66CD00',
    '#458B00',
    '#00FF00',
    '#00FF00',
    '#00EE00',
    '#00CD00',
    '#008B00',
    '#F0E68C',
    '#FFF68F',
    '#EEE685',
    '#CDC673',
    '#8B864E',
    '#B0E0E6',
    '#ADD8E6',
    '#87CEFA',
    '#87CEEB',
    '#00BFFF',
    '#B0C4DE',
    '#1E90FF',
    '#6495ED',
    '#4682B4',
    '#4169E1',
    '#0000FF',
    '#0000CD',
    '#00008B',
    '#000080',
    '#7B68EE',
    '#6A5ACD',
    '#483D8B',
    '#E6E6FA',
    '#D8BFD8',
    '#DDA0DD',
    '#EE82EE',
    '#DA70D6',
    '#FF00FF',
    '#FF00FF',
    '#BA55D3',
    '#9370DB',
    '#8A2BE2',
    '#9400D3',
    '#9932CC',
    '#8B008B',
    '#800080',
    '#4B0082',
    '#E0FFFF',
    '#00FFFF',
    '#00FFFF',
    '#7FFFD4',
    '#66CDAA',
    '#AFEEEE',
    '#40E0D0',
    '#48D1CC',
    '#00CED1',
    '#20B2AA',
    '#5F9EA0',
    '#008B8B',
    '#008080',
]


class Issue:

  def __init__(self, title, state, milestone, trackedIssues):
    self.title = '"{}"'.format(
        '<br/>'.join(
            wrap(re.sub('"', '_', title), width=20, break_long_words=False)
        )
    )
    self.state = state
    self.milestone = milestone
    self.trackedIssues = trackedIssues


def load_issues():
  dec = json.JSONDecoder()
  t = []
  pos = 0
  with open('issues.json', 'rt') as f:
    data = f.read().rstrip()
    while not pos == len(str(data)):
      j, read = dec.raw_decode(str(data)[pos:])
      pos += read
      t.append(j)
  issues = {}
  for iss in t:
    issues_data = iss['data']['repository']['issues']['nodes']
    for issue in issues_data:
      issues[issue['number']] = Issue(
          issue['title'],
          issue['state'],
          issue['milestone'],
          set([val['number'] for val in issue['trackedIssues']['nodes']]),
      )
  return issues


def load_milestones():
  with open('milestones.json', 'rt') as f:
    nodes = json.load(f)['data']['repository']['milestones']['nodes']
    milestones = {}
    for m in nodes:
      if False and not include_closed and m['closed']:
        continue
      milestones[m['number']] = m['title']
    return milestones


def load_cross_referenced(issues):
  dec = json.JSONDecoder()
  t = []
  pos = 0
  with open('cross_referenced.json', 'rt') as f:
    data = f.read().rstrip()
    while not pos == len(str(data)):
      j, read = dec.raw_decode(str(data)[pos:])
      pos += read
      t.append(j)
  ret = {}
  for c in t:
    for i in c['data']['repository']['issues']['edges']:
      num = i['node']['number']
      if not include_closed and issues[num].state == 'CLOSED':
        continue
      ret[num] = []
      for j in i['node']['timelineItems']['nodes']:
        if (
            j['isCrossRepository']
            or not j['source']
            or not j['source']['number']
        ):
          continue
        ret[num].append(j['source']['number'])
  return ret


issues = load_issues()
milestones = load_milestones()
cross_referenced = load_cross_referenced(issues)


u = unionfind(max(issues.keys()) + 1)
for src in cross_referenced.keys():
  for dst in cross_referenced[src]:
    u.unite(src, dst)

for k in issues.keys():
  if (
      milestone_key
      and issues[k].milestone
      and issues[k].milestone['number'] == milestone_key
  ):
    u.unite(k, issue_key)


def include_node(n):
  return u.issame(n, issue_key)


with open('out.mmd', 'w') as f:
  f.write('flowchart TB\n')
  filtered_milestones = set()
  for dst in cross_referenced.keys():
    for src in cross_referenced[dst]:
      if not include_node(src):
        continue

      # Handle tracked by explicitly.
      if dst in issues[src].trackedIssues:
        f.write(f'  {src} --> {dst}\n')
      elif src in issues[dst].trackedIssues:
        f.write(f'  {dst} --> {src}\n')
      # If both reference one another, don't guess.
      elif src in cross_referenced[dst]:
        cross_referenced[dst].remove(src)
        f.write(f'  {src} -.-> {dst}\n')
      else:
        f.write(f'  {src} --- {dst}\n')
      if issues[dst].milestone:
        filtered_milestones.add(issues[dst].milestone['number'])
      if issues[src].milestone:
        filtered_milestones.add(issues[src].milestone['number'])

  for m in milestones.keys():
    if m not in filtered_milestones:
      continue
    f.write(f'  m{m}{{{{"{milestones[m]}"}}}}\n')
    f.write(f'  click m{m} "https://github.com/{gh_org}/{gh_name}/milestone/{m}"\n')
    f.write(f'  class m{m} m{m}\n')
    f.write(
        f'  classDef m{m} fill:{colorArray[m]},stroke:#333,stroke-width:4px;\n'
    )
    f.write(
        f'  classDef m{m}_d fill:{colorArray[m]},fill-opacity:0.4;\n'
    )
    for k in issues.keys():
      if not include_node(k):
        continue
      if issues[k].milestone and issues[k].milestone['number'] == m:
        f.write(f'  {k}({issues[k].title})\n')
        f.write(f'  click {k} "https://github.com/{gh_org}/{gh_name}/issues/{k}"\n')
        f.write(f'  m{m} --> {k}\n')
        f.write(f'  class {k} m{m}{"_d" if issues[k].state == "CLOSED" else ""}\n')
  for k in issues.keys():
    if not include_node(k):
      continue
    if not issues[k].milestone:
      f.write(f'  {k}({issues[k].title})\n')
      f.write(f'  click {k} "https://github.com/{gh_org}/{gh_name}/issues/{k}"\n')
      if issues[k].state == "CLOSED":
        f.write(f'  class {k} closed\n')
  f.write('  classDef closed fill-opacity:0,4;\n')
