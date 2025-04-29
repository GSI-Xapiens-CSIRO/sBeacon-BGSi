import csv
import json
from collections import defaultdict
import subprocess

from smart_open import open as sopen

from shared.athena import Individual, entity_search_conditions
from shared.apiutils import RequestParams, Granularity, RequestQueryParams
from shared.athena.common import ApprovedProjects
from shared.utils import ENV_ATHENA, get_matching_chromosome

from utils import run_custom_query, generate_aliases


def _generate_query(conditions=""):
    query = f"""
    SELECT {generate_aliases()}
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}"  individuals
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_BIOSAMPLES_TABLE}"  biosamples
    ON individuals.id = biosamples.individualId AND individuals._projectName = biosamples._projectName
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_RUNS_TABLE}"  runs
    ON individuals.id = runs.individualId AND individuals._projectName = runs._projectName
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"  analyses
    ON individuals.id = analyses.individualId AND individuals._projectName = analyses._projectName
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}"  datasets
    ON individuals._datasetid = datasets.id AND individuals._projectName = datasets._projectName
    {conditions}
    """
    return query


def gather_metadata(request: RequestParams):
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters,
        "individuals",
        "individuals",
        id_modifier="individuals.id",
    )

    assert (
        request.query.requested_granularity == Granularity.RECORD
    ), "Granularity must be RECORD"

    approved_projects = ApprovedProjects(
        project_names=request.projects, user_sub=request.sub
    ).get_approved_projects()
    projects_statement = ",".join([" ? " for a in approved_projects])

    if conditions:
        conditions += f"""
        AND individuals._projectName IN ({projects_statement})
        AND biosamples._projectName IN ({projects_statement})
        AND runs._projectName IN ({projects_statement})
        AND analyses._projectName IN ({projects_statement})
        AND datasets._projectName IN ({projects_statement})
        """
        execution_parameters += approved_projects * 5
    else:
        conditions = f"""
        WHERE individuals._projectName IN ({projects_statement})
        AND biosamples._projectName IN ({projects_statement})
        AND runs._projectName IN ({projects_statement})
        AND analyses._projectName IN ({projects_statement})
        AND datasets._projectName IN ({projects_statement})
        """
        execution_parameters = approved_projects * 5
    # this is the query we will run
    query = _generate_query(conditions)

    exec_id = run_custom_query(
        query,
        execution_parameters=execution_parameters,
        sub=request.sub,
        projects=approved_projects,
        return_id=True,
    )

    metadata_file_name = (
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
    )
    return metadata_file_name


def extract_vcfs(job_path, metadata_file_path, variants: RequestQueryParams = None):
    # this contains samples we must extract from relevant vcf files
    vcf_samples = defaultdict(set)
    vcf_chromosome_map = dict()

    with sopen(metadata_file_path) as s3file:
        reader = csv.DictReader(s3file)

        for row in reader:
            vcf_sample_id = row["analyses_vcfSampleId"]
            project_name = row["datasets_projectName"]
            dataset_id = row["datasets_datasetName"]
            vcfs = json.loads(row["datasets_vcfLocations"])

            for vcf in vcfs:
                vcf_samples[(project_name, dataset_id, vcf)].add(vcf_sample_id)
                vcf_chromosome_map[(project_name, dataset_id, vcf)] = [
                    entry["chromosomes"]
                    for entry in json.loads(row["datasets_vcfChromosomeMap"])
                    if entry["vcf"] == vcf
                ][0]

    vcf_rename = dict()
    for (
        (project_name, dataset_id, vcf),
        samples,
    ) in vcf_samples.items():
        samples = list(samples)
        file_name = vcf.split("/")[-1]

        if file_name.endswith(".gz"):
            file_name = file_name[:-3]

        vcf_rename[vcf] = f"{job_path}/{project_name}-{dataset_id}-{file_name}"
        args = ["bcftools", "view", "-s", ",".join(samples)]

        if variants:
            start = variants.start
            end = variants.end
            reference_name = variants.reference_name
            
            chromosome_name = get_matching_chromosome(
                vcf_chromosome_map[(project_name, dataset_id, vcf)], reference_name
            )

            # if this vcf does not have the chromosome name, skip it
            if not chromosome_name:
                continue

            assert len(start) == len(end) == 1, "start and end must not be intervals"
            start = start[0]
            end = end[0]

            args += [
                "-r",
                f"{chromosome_name}:{start}-{end}",
            ]
        args += [f'{vcf}']

        print(f"Running command: {' '.join(args)}")
        query_process = subprocess.Popen(
            args, stdout=subprocess.PIPE, cwd="/tmp", encoding="ascii"
        )

        with sopen(vcf_rename[vcf], mode="w") as s3file:
            s3file.write(query_process.stdout.read())

    with sopen(metadata_file_path) as s3infile, sopen(
        f"{job_path}/cohort-metadata.csv", "w"
    ) as s3outfile:
        reader = csv.DictReader(s3infile)
        writer = csv.DictWriter(
            s3outfile,
            fieldnames=[
                field
                for field in reader.fieldnames
                if field != "datasets_vcfChromosomeMap"
            ],
        )
        writer.writeheader()

        for row in reader:
            del row["datasets_vcfChromosomeMap"]

            vcfs = [vcf_rename[vcf] for vcf in json.loads(row["datasets_vcfLocations"])]
            row["datasets_vcfLocations"] = json.dumps(vcfs)

            writer.writerow(row)
