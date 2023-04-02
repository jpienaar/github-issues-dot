#!/usr/bin/env bash

# Get all milestones
gh api graphql --paginate \
   -F owner='openxla' -F name='iree' -f query='
    query ListMilestones($name: String!, $owner: String!, $endCursor: String) {
        repository(owner: $owner, name: $name) {
            milestones(first: 100, after: $endCursor) {
                nodes {
                    title
                    number
                    description
                    dueOn
                    url
                    state
                    closed
                    closedAt
                    updatedAt
                }
            }
        }
    }
' > milestones.json
# Convert to CSV
jq '.data.repository.milestones.nodes[] | select(.closed == false) | [.title, .number] | @csv ' milestones.json > milestones.csv

echo "digraph {" > out.dot
# Get all issues
gh issue list -L20000 -s open -R openxla/iree --json number,title,state,labels,milestone > issues.json
# Convert into nodes
jq -r '.[] | "\(.number) [tooltip = \"\(.title | gsub( "\""; "_"))\" URL = \"https://github.com/openxla/iree/issues/\(.number)\" shape = \"\( if .state == "open" then "circle" else "invhouse" end)\" ]"' issues.json >> out.dot

# Get cross references
gh api graphql --paginate \
   -F owner='openxla' -F name='iree' -f query='
query($endCursor:String) {
  repository(owner: "openxla", name: "iree") {
    issues(first: 100, states: OPEN, after: $endCursor) {
      totalCount
      pageInfo {
        startCursor
        hasNextPage
        endCursor
      }
      edges {
        node {
          number
          timelineItems(first: 200, itemTypes: CROSS_REFERENCED_EVENT) {
            totalCount
            pageInfo {
              startCursor
              hasNextPage
              endCursor
            }
            nodes {
              ... on CrossReferencedEvent {
                isCrossRepository
                source {
                  ... on Issue {
                    number
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}' > cross_referenced.json

# Convert into edges.
jq -r '.data.repository.issues.edges[] as $in | $in.node.number as $num | $in.node.timelineItems.nodes[] | select( .isCrossRepository == false and .source.number != null ) | "\($num)->\(.source.number)"' cross_referenced.json >> out.dot

echo "}" >> out.dot
