import time
import re
import csv
import json

import boto3
from smart_open import open as sopen

from shared.ontoutils import get_ontology_details
from shared.utils import ENV_ATHENA, ENV_DYNAMO


athena = boto3.client("athena")
dynamodb = boto3.client("dynamodb")
pattern = re.compile(r"^\w[^:]+:.+$")

# If we hit one of these keywords, the window for a WHERE clause has closed
# https://docs.aws.amazon.com/athena/latest/ug/select.html
POST_WHERE_KEYWORDS = {
    "GROUP",
    "HAVING",
    "UNION",
    "INTERSECT",
    "EXCEPT",
    "ORDER",
    "OFFSET",
    "LIMIT",
    ";",
}
POST_TABLE_WORDS = {
    "LEFT",
    "RIGHT",
    "INNER",
    "OUTER",
    "FULL",
    "CROSS" "JOIN",
    "ON",
    "USING",
}

# These tables need to be filtered by project name
PROJECT_NAME_TABLES = {
    ENV_ATHENA.ATHENA_DATASETS_TABLE,
    ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE,
    ENV_ATHENA.ATHENA_BIOSAMPLES_TABLE,
    ENV_ATHENA.ATHENA_RUNS_TABLE,
    ENV_ATHENA.ATHENA_ANALYSES_TABLE,
}


class ApprovedProjects:
    def __init__(self, project_names=None, user_sub=None):
        self.requested_projects = project_names
        self.user_sub = user_sub
        self.approved_projects = None

    def validate_arguments(self):
        assert isinstance(
            self.requested_projects, list
        ), f"project_names must be a list, got {type(self.requested_projects)}"
        assert isinstance(
            self.user_sub, str
        ), f"user_sub must be a string, got {type(self.user_sub)}"

    def get_approved_projects(self):
        if self.approved_projects is None:
            self.validate_arguments()
            self.approved_projects = self.lookup_approved_projects()
        return self.approved_projects

    def lookup_approved_projects(self):
        """Returns a list of projects that the user has access to"""
        if not (self.requested_projects and self.user_sub):
            return []
        all_approved_projects = []
        kwargs = {
            "TableName": ENV_DYNAMO.DYNAMO_PROJECT_USERS_TABLE,
            "IndexName": ENV_DYNAMO.DYNAMO_PROJECT_USERS_UID_INDEX,
            "KeyConditionExpression": "uid = :uid",
            "ProjectionExpression": "#name",
            "ExpressionAttributeNames": {
                "#name": "name",
            },
            "ExpressionAttributeValues": {
                ":uid": {
                    "S": self.user_sub,
                },
            },
        }
        last_evaluated_key = True
        while last_evaluated_key:
            print(f"Calling dynamodb.query with kwargs: {json.dumps(kwargs)}")
            response = dynamodb.query(**kwargs)
            print(f"Received response: {json.dumps(response, default=str)}")
            all_approved_projects.extend(
                item["name"]["S"] for item in response.get("Items", [])
            )
            last_evaluated_key = response.get("LastEvaluatedKey", {})
            kwargs["ExclusiveStartKey"] = last_evaluated_key
        return [
            project_name
            for project_name in self.requested_projects
            if project_name in all_approved_projects
        ]


def get_projects_filter(tables, project_names):
    words = []
    execution_parameters = []
    for table in tables:
        words.append(f"REGEXP_LIKE( {table}._projectname, ? )")
        execution_parameters.append(f"'^{'|'.join(project_names)}$'")
        words.append("AND")
    return words, execution_parameters


def add_project_names(query, execution_parameters, project_names, user_sub):
    # I'm not writing a full parser, so I hope all the inputs are in the execution parameters
    # Because we're about to split by spaces
    # This will probably break if someone names a database, table, or column with a space
    # It will also break if there are complex nesting queries. It's designed to break in a way
    # that causes an error, rather than silently allowing a _projectnames table to be missed.
    # This will fail if a WHERE clause contains a top-level OR because the _projectnames filter
    # will only apply to the first part. Currently we don't have any of those.
    if execution_parameters is None:
        execution_parameters = []
    new_execution_parameters = []
    # This may crash on nested FROM clauses, of which we currently have none
    tables = []
    words = query.split(" ")
    new_words = []
    approved_projects = ApprovedProjects(project_names=project_names, user_sub=user_sub)
    next_is_table = False
    possible_alias = False
    for word in words:
        # Remove brackets for matching
        stripped_word = word.strip("()")
        upper_word = stripped_word.upper()
        if not word:
            # Just a consecutive space or a parenthesis
            pass
        elif next_is_table:
            next_is_table = False
            if any(table in stripped_word for table in PROJECT_NAME_TABLES):
                tables.append(stripped_word)
                possible_alias = True
        elif upper_word == "?":
            new_execution_parameters.append(next(execution_parameters))
        elif upper_word in ("FROM", "JOIN"):
            possible_alias = False
            next_is_table = True
        elif upper_word == "WHERE":
            # Stick our filter as the first element in the WHERE clause
            possible_alias = False
            if tables:
                new_words.append(word)
                words_to_insert, execution_parameters_to_insert = get_projects_filter(
                    tables, approved_projects.get_approved_projects()
                )
                new_words.extend(words_to_insert)
                new_execution_parameters.extend(execution_parameters_to_insert)
                tables = []
                continue  # We've already added the WHERE keyword
        elif upper_word in POST_WHERE_KEYWORDS:
            # We've hit a keyword that means a WHERE clause is not coming; make it ourselves
            possible_alias = False
            if tables:
                new_words.append("WHERE")
                words_to_insert, execution_parameters_to_insert = get_projects_filter(
                    tables, approved_projects.get_approved_projects()
                )
                del words_to_insert[-1]  # Remove the trailing AND
                new_words.extend(words_to_insert)
                new_execution_parameters.extend(execution_parameters_to_insert)
                tables = []
        elif upper_word in POST_TABLE_WORDS:
            possible_alias = False
        elif possible_alias and upper_word != "AS":
            possible_alias = False
            # Replace the table name with its alias
            tables[-1] = stripped_word
        new_words.append(word)
    return " ".join(new_words), new_execution_parameters or None


# Perform database level operations based on the queries


class AthenaModel:
    """
    This is a higher level abstraction class
    user is only required to write queries in the following form

    SELECT * FROM "{{database}}"."{{table}}" WHERE <CONDITIONS>;

    table name is fetched from the child class, database is injected
    in this class. Helps write cleaner code without so many constants
    repeated everywhere.
    """

    @classmethod
    def get_by_query(
        cls, query, /, *, queue=None, execution_parameters=None, projects=None, sub=None
    ):
        query = query.format(
            database=ENV_ATHENA.ATHENA_METADATA_DATABASE, table=cls._table_name
        )
        exec_id = run_custom_query(
            query,
            queue=None,
            return_id=True,
            execution_parameters=execution_parameters,
            projects=projects,
            sub=sub,
        )

        if exec_id:
            if queue is None:
                return cls.parse_array(exec_id)
            else:
                queue.put(cls.parse_array(exec_id))
        return []

    @classmethod
    def get_existence_by_query(
        cls, query, /, *, queue=None, execution_parameters=None, projects=None, sub=None
    ):
        query = query.format(
            database=ENV_ATHENA.ATHENA_METADATA_DATABASE, table=cls._table_name
        )
        result = run_custom_query(
            query,
            queue=None,
            execution_parameters=execution_parameters,
            projects=projects,
            sub=sub,
        )

        if not len(result) > 0:
            return []
        elif queue is None:
            return len(result) > 1
        else:
            queue.put(len(result) > 1)

    @classmethod
    def parse_array(cls, exec_id):
        instances = []
        var_list = list()
        case_map = {k.lower(): k for k in cls().__dict__.keys()}

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
        ) as s3f:
            reader = csv.reader(s3f)

            for n, row in enumerate(reader):
                if n == 0:
                    var_list = row
                else:
                    instance = cls()
                    for attr, val in zip(var_list, row):
                        if not attr in case_map:
                            continue
                        try:
                            val = json.loads(val)
                        except:
                            val = val
                        instance.__dict__[case_map[attr]] = val
                    instances.append(instance)

        return instances

    @classmethod
    def get_count_by_query(
        cls, query, /, *, queue=None, execution_parameters=None, projects=None, sub=None
    ):
        query = query.format(
            database=ENV_ATHENA.ATHENA_METADATA_DATABASE, table=cls._table_name
        )
        result = run_custom_query(
            query,
            queue=None,
            execution_parameters=execution_parameters,
            projects=projects,
            sub=sub,
        )

        if not len(result) > 0:
            return []
        elif queue is None:
            return int(result[1]["Data"][0]["VarCharValue"])
        else:
            queue.put(int(result[1]["Data"][0]["VarCharValue"]))


def extract_terms(array):
    for item in array:
        if type(item) == dict:
            for key, value in item.items():
                if type(value) == str:
                    if key == "id" and pattern.match(value):
                        label = item.get("label", "")
                        ontology = get_ontology_details(value.split(":")[0])
                        typ = (ontology.name if ontology else "") or ""
                        yield value, label, typ
                if type(value) == dict:
                    yield from extract_terms([value])
                elif type(value) == list:
                    yield from extract_terms(value)
        if type(item) == str:
            continue
        elif type(item) == list:
            yield from extract_terms(item)


def run_custom_query(
    query,
    /,
    *,
    database=ENV_ATHENA.ATHENA_METADATA_DATABASE,
    workgroup=ENV_ATHENA.ATHENA_WORKGROUP,
    queue=None,
    return_id=False,
    execution_parameters=None,
    projects=None,
    sub=None,
):
    query = query.replace("\n", " ")
    print(f"{query=}")
    print(f"{execution_parameters=}")
    query, execution_parameters = add_project_names(
        query, execution_parameters, projects, sub
    )
    print(f"After projects filter: {query=}")
    print(f"After projects filter: {execution_parameters=}")

    if execution_parameters is None:
        response = athena.start_query_execution(
            QueryString=query,
            # ClientRequestToken='string',
            QueryExecutionContext={"Database": database},
            WorkGroup=workgroup,
        )
    else:
        response = athena.start_query_execution(
            QueryString=query,
            # ClientRequestToken='string',
            QueryExecutionContext={"Database": database},
            WorkGroup=workgroup,
            ExecutionParameters=execution_parameters,
        )

    retries = 0
    while True:
        exec = athena.get_query_execution(QueryExecutionId=response["QueryExecutionId"])
        status = exec["QueryExecution"]["Status"]["State"]

        if status in ("QUEUED", "RUNNING"):
            time.sleep(0.1)
            retries += 1

            if retries == 300:
                print("Timed out")
                return None
            continue
        elif status in ("FAILED", "CANCELLED"):
            print("Error: ", exec["QueryExecution"]["Status"])
            return None
        else:
            if return_id:
                return response["QueryExecutionId"]
            else:
                data = athena.get_query_results(
                    QueryExecutionId=response["QueryExecutionId"], MaxResults=1000
                )
                if queue is not None:
                    return queue.put(data["ResultSet"]["Rows"])
                else:
                    return data["ResultSet"]["Rows"]
