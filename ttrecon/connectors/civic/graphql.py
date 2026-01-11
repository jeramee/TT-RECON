from __future__ import annotations

EVIDENCE_ITEMS_QUERY = """query EvidenceItems($geneName: String, $variantName: String, $status: EvidenceStatusFilter, $after: String, $first: Int) {
  evidenceItems(geneName: $geneName, variantName: $variantName, status: $status, after: $after, first: $first) {
    totalCount
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      id
      status
      evidenceType
      evidenceLevel
      evidenceRating
      evidenceDirection
      description
      drugInteractionType
      source {
        id
        citation
        sourceType
      }
      gene {
        id
        name
      }
      variant {
        id
        name
      }
      disease {
        id
        name
        doid
      }
      drugs {
        id
        name
        ncitId
      }
    }
  }
}
"""
