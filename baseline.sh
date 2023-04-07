#!/usr/bin/env bash

GH_ORG="jpienaar"
GH_NAME="github-issues-dot"

# Get all milestones
gh api graphql --paginate \
   -F owner=$GH_ORG -F name=$GH_NAME -f query='
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

# Get ~all issues
gh api graphql --paginate -F owner=$GH_ORG -F name=$GH_NAME -f query='
  query ListIssues($name: String!, $owner: String!, $endCursor: String) {
     repository(owner: $owner, name: $name) {
       issues(first: 100, after: $endCursor) {
         totalCount
         pageInfo {
           startCursor
           hasNextPage
           endCursor
         }
         nodes {
           number
           title
           state
           labels(first: 100) {
             totalCount
             pageInfo {
               startCursor
               hasNextPage
               endCursor
             }
             ... on LabelConnection {
               edges {
                 node {
                   id
                 }
               }
             }
           }
           milestone {
             number
           }
           trackedIssues(first: 100) {
             totalCount
             pageInfo {
               startCursor
               hasNextPage
               endCursor
             }
             ... on IssueConnection {
               nodes {
                 number
               }
             }
           }
         }
       }
     }
   }' > issues.json

# Get cross references
gh api graphql --paginate \
   -F owner=$GH_ORG -F name=$GH_NAME -f query='
  query($owner: String!, $name: String!, $endCursor:String) {
    repository(owner: $owner, name: $name) {
      issues(first: 100, after: $endCursor) {
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

