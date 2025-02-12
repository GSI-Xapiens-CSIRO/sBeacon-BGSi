import json

import jsons

from shared.athena import Individual
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_resultset_response,
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


def route(request: RequestParams, individual_id):
    if request.query.requested_granularity == "boolean":
        query = get_record_query()
        count = (
            1
            if Individual.get_existence_by_query(
                query,
                projects=request.projects,
                sub=request.sub,
                execution_parameters=[f"'{individual_id}'"],
            )
            else 0
        )
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == "count":
        query = get_record_query()
        count = (
            1
            if Individual.get_existence_by_query(
                query,
                projects=request.projects,
                sub=request.sub,
                execution_parameters=[f"'{individual_id}'"],
            )
            else 0
        )
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query()
        individuals = Individual.get_by_query(
            query,
            projects=request.projects,
            sub=request.sub,
            execution_parameters=[f"'{individual_id}'"],
        )
        response = build_beacon_resultset_response(
            jsons.dump(individuals, strip_privates=True),
            len(individuals),
            request,
            {},
            DefaultSchemas.INDIVIDUALS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)
