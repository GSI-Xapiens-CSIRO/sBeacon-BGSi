export const endpoint = 'individuals';
export const result = {
  meta: {
    beaconId: 'au.csiro-serverless.beacon',
    apiVersion: 'v2.0.0',
    returnedGranularity: 'record',
    receivedRequestSummary: {
      apiVersion: 'v2.0',
      requestedSchemas: [],
      filters: [],
      req_params: {},
      includeResultsetResponses: 'HIT',
      pagination: {
        skip: 0,
        limit: 10,
      },
      requestedGranularity: 'record',
      testMode: false,
    },
    returnedSchemas: [
      {
        entityType: 'individual',
        schema: 'beacon-individual-v2.0.0',
      },
    ],
  },
  responseSummary: {
    exists: true,
    numTotalResults: 60,
  },
  response: {
    resultSets: [
      {
        id: '',
        setType: '',
        exists: true,
        resultsCount: 10,
        results: [
          {
            diseases: '',
            ethnicity: {
              id: 'SNOMED:52075006',
              label: 'Congolese',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223688001',
              label: 'United States of America',
            },
            id: 'AXE_1-1',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C79426',
                },
              },
              {
                procedureCode: {
                  id: 'NCIT:C64264',
                },
              },
            ],
            karyotypicSex: 'XXY',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407378000',
              label: 'Surgically transgendered transsexual, male-to-female',
            },
            treatments: '',
          },
          {
            diseases: '',
            ethnicity: {
              id: 'SNOMED:76460008',
              label: 'Yanomama',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223688001',
              label: 'United States of America',
            },
            id: 'AXE_1-10',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C64264',
                },
              },
            ],
            karyotypicSex: 'XXXY',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:248153007',
              label: 'Male',
            },
            treatments: '',
          },
          {
            diseases: [
              {
                diseaseCode: {
                  id: 'SNOMED:734099007',
                  label: 'Neuroblastoma of central nervous system',
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:135811000119107',
                  label:
                    'Lewy body dementia with behavioral disturbance (disorder)',
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:23853001',
                  label: 'Disorder of the central nervous system',
                },
              },
            ],
            ethnicity: {
              id: 'SNOMED:12556008',
              label: 'Tamils',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223688001',
              label: 'United States of America',
            },
            id: 'AXE_1-2',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C79426',
                },
              },
              {
                procedureCode: {
                  id: 'NCIT:C64264',
                },
              },
            ],
            karyotypicSex: 'XXYY',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407378000',
              label: 'Surgically transgendered transsexual, male-to-female',
            },
            treatments: '',
          },
          {
            diseases: [
              {
                diseaseCode: {
                  id: 'SNOMED:26929004',
                  label: "Alzheimer's disease",
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:23853001',
                  label: 'Disorder of the central nervous system',
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:359642000',
                  label: 'Diabetes mellitus type 2 in nonobese (disorder)',
                },
              },
            ],
            ethnicity: {
              id: 'SNOMED:113170005',
              label: 'Aymara',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223688001',
              label: 'United States of America',
            },
            id: 'AXE_1-3',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C79426',
                },
              },
              {
                procedureCode: {
                  id: 'NCIT:C64263',
                },
              },
            ],
            karyotypicSex: 'XXX',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407374003',
              label: 'Transsexual',
            },
            treatments: '',
          },
          {
            diseases: '',
            ethnicity: {
              id: 'SNOMED:10432001',
              label: 'Onge',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223600005',
              label: 'India',
            },
            id: 'AXE_1-4',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C79426',
                },
              },
              {
                procedureCode: {
                  id: 'NCIT:C64264',
                },
              },
            ],
            karyotypicSex: 'XYY',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407377005',
              label: 'Female-to-male transsexual',
            },
            treatments: '',
          },
          {
            diseases: [
              {
                diseaseCode: {
                  id: 'SNOMED:254955001',
                  label: 'Pituitary carcinoma',
                },
              },
            ],
            ethnicity: {
              id: 'SNOMED:12556008',
              label: 'Tamils',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223498002',
              label: 'Africa',
            },
            id: 'AXE_1-5',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C64263',
                },
              },
              {
                procedureCode: {
                  id: 'NCIT:C64264',
                },
              },
            ],
            karyotypicSex: 'XXXX',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407374003',
              label: 'Transsexual',
            },
            treatments: '',
          },
          {
            diseases: [
              {
                diseaseCode: {
                  id: 'SNOMED:56265001',
                  label: 'Heart disease (disorder)',
                },
              },
            ],
            ethnicity: {
              id: 'SNOMED:17789004',
              label: 'Papuans',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223713009',
              label: 'Argentina',
            },
            id: 'AXE_1-6',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C93025',
                },
              },
            ],
            karyotypicSex: 'XX',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:248152002',
              label: 'Female',
            },
            treatments: '',
          },
          {
            diseases: '',
            ethnicity: {
              id: 'SNOMED:77502007',
              label: 'Atacamenos',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223498002',
              label: 'Africa',
            },
            id: 'AXE_1-7',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C79426',
                },
              },
            ],
            karyotypicSex: 'XXXY',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407377005',
              label: 'Female-to-male transsexual',
            },
            treatments: '',
          },
          {
            diseases: [
              {
                diseaseCode: {
                  id: 'SNOMED:359642000',
                  label: 'Diabetes mellitus type 2 in nonobese (disorder)',
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:312991009',
                  label: 'Senile dementia of the Lewy body type (disorder)',
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:81531005',
                  label: 'Diabetes mellitus type 2 in obese (disorder)',
                },
              },
            ],
            ethnicity: {
              id: 'SNOMED:89026003',
              label: 'Alacaluf',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223498002',
              label: 'Africa',
            },
            id: 'AXE_1-8',
            info: '',
            interventionsOrProcedures: [
              {
                procedureCode: {
                  id: 'NCIT:C64263',
                },
              },
            ],
            karyotypicSex: 'XX',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407378000',
              label: 'Surgically transgendered transsexual, male-to-female',
            },
            treatments: '',
          },
          {
            diseases: [
              {
                diseaseCode: {
                  id: 'SNOMED:26929004',
                  label: "Alzheimer's disease",
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:81531005',
                  label: 'Diabetes mellitus type 2 in obese (disorder)',
                },
              },
              {
                diseaseCode: {
                  id: 'SNOMED:135811000119107',
                  label:
                    'Lewy body dementia with behavioral disturbance (disorder)',
                },
              },
            ],
            ethnicity: {
              id: 'SNOMED:10292001',
              label: 'Guamians',
            },
            exposures: '',
            geographicOrigin: {
              id: 'SNOMED:223498002',
              label: 'Africa',
            },
            id: 'AXE_1-9',
            info: '',
            interventionsOrProcedures: '',
            karyotypicSex: 'XXXX',
            measures: '',
            pedigrees: '',
            phenotypicFeatures: '',
            sex: {
              id: 'SNOMED:407377005',
              label: 'Female-to-male transsexual',
            },
            treatments: '',
          },
        ],
        resultsHandover: null,
      },
    ],
  },
  beaconHandovers: [],
};

export const query = {
  query: {
    filters: [
      {
        scope: 'biosamples',
        id: 'SNOMED:365641003',
        includeDescendantTerms: true,
      },
    ],
    requestedGranularity: 'record',
    pagination: {
      skip: 0,
      limit: 10,
    },
  },
  meta: {
    apiVersion: 'v2.0',
  },
};
