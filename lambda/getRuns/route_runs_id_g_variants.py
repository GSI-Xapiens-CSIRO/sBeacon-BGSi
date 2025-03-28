from collections import defaultdict
import base64
import json

from shared.variantutils import perform_variant_search
from shared.utils import ENV_ATHENA
from shared.athena import (
    run_custom_query,
    parse_datasets_with_samples,
    entity_search_conditions,
)
from shared.apiutils import (
    RequestParams,
    Granularity,
    IncludeResultsetResponses,
    DefaultSchemas,
    build_beacon_count_response,
    build_beacon_boolean_response,
    build_beacon_resultset_response,
    bundle_response,
    get_variant_entry,
)


def datasets_query(conditions):
    query = f"""
    SELECT D.id, D._projectname, D._datasetname, D._vcflocations, D._vcfchromosomemap, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}" A
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}" D
    ON A._datasetid = D.id
    WHERE A.runid= ?
    AND D._assemblyid= ?
    {(' AND ' + conditions) if len(conditions) > 0 else ''} 
    GROUP BY D.id, D._projectname, D._datasetname, D._vcflocations, D._vcfchromosomemap 
    """
    return query


def route(request: RequestParams, run_id):
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, "analyses", "runs", id_modifier="A.id", with_where=False
    )
    query_params = request.query.request_parameters
    query = datasets_query(conditions)

    if execution_parameters:
        execution_parameters = [
            f"'{run_id}'",
            f"'{query_params.assembly_id}'",
        ] + execution_parameters
    else:
        execution_parameters = [f"'{run_id}'", f"'{query_params.assembly_id}'"]

    exec_id = run_custom_query(
        query,
        return_id=True,
        execution_parameters=execution_parameters,
        projects=request.projects,
        sub=request.sub,
    )
    datasets, samples = parse_datasets_with_samples(exec_id)
    check_all = check_all = request.query.include_resultset_responses in (
        IncludeResultsetResponses.HIT,
        IncludeResultsetResponses.ALL,
    )

    variants = set()
    results = list()
    # key=pos-ref-alt
    # val=counts
    variant_call_counts = defaultdict(int)
    variant_allele_counts = defaultdict(int)
    variant_info_mapping = defaultdict(lambda: {"projectName": "", "datasetName": ""})
    exists = False

    query_responses = perform_variant_search(
        datasets=datasets,
        reference_name=query_params.reference_name,
        reference_bases=query_params.reference_bases,
        alternate_bases=query_params.alternate_bases,
        start=query_params.start,
        end=query_params.end,
        variant_type=query_params.variant_type,
        variant_min_length=query_params.variant_min_length,
        variant_max_length=query_params.variant_max_length,
        requested_granularity=request.query.requested_granularity,
        include_datasets=request.query.include_resultset_responses,
        dataset_samples=samples,
    )

    for query_response in query_responses:
        exists = exists or query_response.exists

        if exists:
            if check_all:
                variants.update(query_response.variants)

                for variant in query_response.variants:
                    chrom, pos, ref, alt, typ = variant.split("\t")
                    idx = f"{pos}_{ref}_{alt}"
                    variant_call_counts[idx] += query_response.call_count
                    variant_allele_counts[idx] += query_response.all_alleles_count
                    internal_id = (
                        f"{query_params.assembly_id}\t{chrom}\t{pos}\t{ref}\t{alt}"
                    )
                    project_name = query_response.project_name
                    dataset_name = query_response.dataset_name

                    variant_internal_id = base64.b64encode(
                        f"{internal_id}".encode()
                    ).decode()
                    results.append(
                        get_variant_entry(
                            variant_internal_id,
                            query_params.assembly_id,
                            ref,
                            alt,
                            int(pos),
                            int(pos) + len(alt),
                            typ,
                        )
                    )
                    variant_info_mapping[variant_internal_id] = {
                        "projectName": project_name,
                        "datasetName": dataset_name,
                    }

    if request.query.requested_granularity == Granularity.BOOLEAN:
        response = build_beacon_boolean_response(
            {}, 1 if exists else 0, request, {}, DefaultSchemas.GENOMICVARIATIONS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        response = build_beacon_count_response(
            {}, len(variants), request, {}, DefaultSchemas.GENOMICVARIATIONS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        response = build_beacon_resultset_response(
            results,
            len(variants),
            request,
            {},
            DefaultSchemas.GENOMICVARIATIONS,
            variant_info_mapping,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == "__main__":
    pass
