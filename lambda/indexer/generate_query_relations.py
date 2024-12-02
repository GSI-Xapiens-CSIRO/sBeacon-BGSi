QUERY = """
CREATE TABLE sbeacon_relations
WITH (
    format = 'ORC',
    write_compression = 'SNAPPY',
    external_location = '{uri}',
    bucketed_by = ARRAY['individualid', 'biosampleid', 'runid', 'analysisid'],
    bucket_count = 50
) 
AS
SELECT 
    D.id as datasetid,
    I.id AS individualid, 
    B.id AS biosampleid, 
    R.id AS runid,  
    A.id AS analysisid
FROM 
    "sbeacon_datasets" as D
    LEFT OUTER JOIN "sbeacon_individuals" I
        on D.id = I._datasetid
    LEFT OUTER JOIN "sbeacon_biosamples" B
        ON I.id = B."individualid"
    LEFT OUTER JOIN "sbeacon_runs" R
        ON B.id = R."biosampleid"
    LEFT OUTER JOIN "sbeacon_analyses" A
        ON R.id = A."runid"
"""
