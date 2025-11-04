import { DifyDataset, ParsedDocument, DifyConfig } from './types'

export const MOCK_CONFIG: DifyConfig = {
  api_key: 'dataset-xxxxxxxxxxxx',
  base_url: 'http://kca-ai.kro.kr:5001/v1'
}

export const MOCK_DATASETS: DifyDataset[] = [
  {
    id: 'dataset-1',
    name: 'Technical Documentation',
    description: 'API and technical docs',
    document_count: 25,
    word_count: 50000,
    created_at: '2025-01-15T10:00:00Z'
  },
  {
    id: 'dataset-2',
    name: 'Legal Documents',
    description: 'Contracts and agreements',
    document_count: 10,
    word_count: 30000,
    created_at: '2025-01-20T14:30:00Z'
  },
  {
    id: 'dataset-3',
    name: 'User Manuals',
    description: 'Product manuals and guides',
    document_count: 15,
    word_count: 42000,
    created_at: '2025-01-18T09:20:00Z'
  },
  {
    id: 'dataset-4',
    name: 'Research Papers',
    description: 'Academic research and publications',
    document_count: 8,
    word_count: 28000,
    created_at: '2025-01-22T16:45:00Z'
  }
]

export const MOCK_PARSED_DOCUMENTS: ParsedDocument[] = [
  {
    path: 'output/sample/sample.md',
    name: 'sample.md',
    size: 15234,
    created_at: '2025-01-25T09:15:00Z'
  },
  {
    path: 'output/contract_agreement/contract_agreement.md',
    name: 'contract_agreement.md',
    size: 28945,
    created_at: '2025-01-24T14:30:00Z'
  },
  {
    path: 'output/technical_spec/technical_spec.md',
    name: 'technical_spec.md',
    size: 42156,
    created_at: '2025-01-23T11:20:00Z'
  },
  {
    path: 'output/user_manual/user_manual.md',
    name: 'user_manual.md',
    size: 19823,
    created_at: '2025-01-22T08:45:00Z'
  },
  {
    path: 'output/research_paper/research_paper.md',
    name: 'research_paper.md',
    size: 56789,
    created_at: '2025-01-21T13:10:00Z'
  }
]
