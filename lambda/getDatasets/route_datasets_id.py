import json

import jsons

from shared.athena import Dataset
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_collection_response,
    build_beacon_count_response,
    bundle_response,
)


def get_record_query():
    query = f"""
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"= ?
    LIMIT 1;
    """

    return query


def route(request: RequestParams, dataset_id):
    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_record_query()
        count = (
            1
            if Dataset.get_existence_by_query(
                query,
                projects=request.projects,
                sub=request.sub,
                execution_parameters=[f"'{dataset_id}'"],
            )
            else 0
        )
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.DATASETS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_record_query()
        count = (
            1
            if Dataset.get_existence_by_query(
                query,
                projects=request.projects,
                sub=request.sub,
                execution_parameters=[f"'{dataset_id}'"],
            )
            else 0
        )
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.DATASETS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query()
        datasets = Dataset.get_by_query(
            query,
            projects=request.projects,
            sub=request.sub,
            execution_parameters=[f"'{dataset_id}'"],
        )
        response = build_beacon_collection_response(
            jsons.dump(datasets, strip_privates=True),
            len(datasets),
            request,
            lambda x, y: x,
            DefaultSchemas.DATASETS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)
