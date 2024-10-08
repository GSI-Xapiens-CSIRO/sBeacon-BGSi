export interface Filter {
  type: FilterTypes;
  id: string;
  scope: string;
  operator?: string;
  value?: string;
  includeDescendantTerms?: boolean;
}

export enum FilterTypes {
  ALPHANUMERIC = 'alphanumeric',
  ONTOLOGY = 'ontology',
  CUSTOM = 'custom',
}

export enum ScopeTypes {
  INDIVIDUALS = 'individuals',
  BIOSAMEPLES = 'biosamples',
  RUNS = 'runs',
  ANALYSES = 'analyses',
  GENOMIC_VARIANTS = 'g_variants',
  DATASETS = 'datasets',
  COHORTS = 'cohorts',
}
