export const examples = [
  {
    text: `Records of female <strong>(karyotypic sex = XX)</strong> individuals.`,
    scope: 'individuals',
    body: {
      query: {
        filters: [
          {
            id: 'karyotypicSex',
            operator: '=',
            value: 'XX',
          },
        ],
        pagination: {
          skip: 0,
          limit: 10,
        },
        requestedGranularity: 'record',
      },
      meta: {
        apiVersion: 'v2.0',
      },
    },
  },
  {
    text: `Records of biosamples entries with a minor blood groups - finding <strong>(SNOMED:365641003)</strong>.`,
    scope: 'biosamples',
    body: {
      query: {
        filters: [
          {
            id: 'SNOMED:365641003',
          },
        ],
        pagination: {
          skip: 0,
          limit: 10,
        },
        requestedGranularity: 'record',
      },
      meta: {
        apiVersion: 'v2.0',
      },
    },
  },
  {
    text: `Records of individuals entries <strong>(karyotypic sex = XXY)</strong> and underwent procedure <strong>(NCIT:C79426)</strong>.`,
    scope: 'individuals',
    body: {
      query: {
        filters: [
          {
            id: 'karyotypicSex',
            operator: '=',
            value: 'XYY',
          },
          {
            id: 'NCIT:C79426',
          },
        ],
        pagination: {
          skip: 0,
          limit: 10,
        },
        requestedGranularity: 'record',
      },
      meta: {
        apiVersion: 'v2.0',
      },
    },
  },
  {
    text: `Records of individuals entries <strong>(karyotypic sex = XXY)</strong>, underwent procedure <strong>(NCIT:C79426)</strong> <br>and with a respiratory specimen sample<strong>(SNOMED:258603007)</strong> from India <strong>(SNOMED:223600005)</strong>.`,
    scope: 'individuals',
    body: {
      query: {
        filters: [
          {
            id: 'karyotypicSex',
            operator: '=',
            value: 'XYY',
          },
          {
            id: 'NCIT:C79426',
          },
          {
            id: 'SNOMED:223600005',
          },
          {
            id: 'SNOMED:258603007',
            scope: 'biosamples',
          },
        ],
        pagination: {
          skip: 0,
          limit: 10,
        },
        requestedGranularity: 'record',
      },
      meta: {
        apiVersion: 'v2.0',
      },
    },
  },
  {
    text: `Genomic variant entries for <strong>(Chromosome 1)</strong> in the range <strong>546801-546810</strong>.`,
    scope: 'g_variants',
    body: {
      query: {
        requestedGranularity: 'record',
        filters: [],
        pagination: {
          skip: 0,
          limit: 10,
        },
        requestParameters: {
          assemblyId: 'GRCH38',
          referenceBases: 'N',
          start: [546801],
          end: [546810],
          referenceName: '1',
        },
      },
      meta: {
        apiVersion: 'v2.0',
      },
    },
  },
  {
    text: 'Individuals having a SNP between 546801 and 546810',
    scope: 'g_variants',
    return: 'individuals',
    id: 'R1JDSDM4CTEJNTQ2ODAyCUcJQw==',
    customReturn: true,
    body: {
      query: {
        filters: [],
        requestedGranularity: 'record',
        pagination: {
          skip: 0,
          limit: 25,
        },
      },
      meta: {
        apiVersion: 'v2.0',
      },
    },
  },
];
