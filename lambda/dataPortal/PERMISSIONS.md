# Data Portal Lambda Permissions Documentation

This documentation contains a list of all endpoints and required permissions in the Data Portal Lambda.

---

## Permission Format

Permission format follows the pattern: `resource.action`

**Available actions:**
- `create` - Create a new resource
- `read` - Read/view a resource
- `update` - Modify an existing resource
- `delete` - Delete a resource
- `download` - Download a file

---

## Permissions by File

### 1. admin_dportal_functions.py

#### File Management

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/admin/folders` | `file_management.read` | `list_folders` | List all folders |
| DELETE | `/dportal/admin/folders/{folder}` | `file_management.delete` | `delete_folder` | Delete a folder |

#### Project Management

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/admin/projects` | `project_management.read` | `list_projects` | List all projects |
| POST | `/dportal/admin/projects` | `project_management.create` | `create_project` | Create a new project |
| GET | `/dportal/admin/projects/{name}/users` | `project_management.read` | `list_project_users` | List users in a project |
| POST | `/dportal/admin/projects/{name}/users` | `project_management.update` | `add_user_to_project` | Add user to a project |
| DELETE | `/dportal/admin/projects/{name}/users/{email}` | `project_management.delete` | `remove_project_user` | Remove user from a project |
| POST | `/dportal/admin/projects/{name}/users/{email}/upload` | `project_management.create` | `admin_user_cli_add_upload` | Create CLI upload for user |
| DELETE | `/dportal/admin/projects/{name}/users/{email}/upload/{upload_id}` | `project_management.delete` | `admin_user_cli_remove_upload` | Delete CLI upload |
| GET | `/dportal/admin/projects/{name}/upload` | `project_management.read` | `admin_get_project_uploads` | List uploads in a project |
| DELETE | `/dportal/admin/projects/{name}` | `project_management.delete` | `delete_project` | Delete a project |
| PUT | `/dportal/admin/projects/{name}` | `project_management.update` | `update_project` | Update a project |
| DELETE | `/dportal/admin/projects/{name}/errors` | `project_management.delete` | `delete_project_errors` | Delete project errors |

#### sBeacon Management

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/admin/projects/{name}/ingest/{dataset}` | `project_management.create` | `ingest_dataset_to_sbeacon` | Ingest dataset to sBeacon |
| DELETE | `/dportal/admin/projects/{name}/ingest/{dataset}` | `project_management.delete` | `un_ingest_dataset_from_sbeacon` | Un-ingest dataset from sBeacon |
| POST | `/dportal/admin/sbeacon/index` | `project_management.create` | `index_sbeacon` | Trigger sBeacon indexing |

---

### 2. admin_notebook_functions.py

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/admin/notebooks` | `notebook_management.read` | `list_notebooks` | List all notebooks |
| GET | `/dportal/admin/notebooks/{name}` | `notebook_management.read` | `get_notebook` | Get notebook details |
| POST | `/dportal/admin/notebooks/{name}/stop` | `notebook_management.update` | `stop_notebook` | Stop a notebook |
| POST | `/dportal/admin/notebooks/{name}/delete` | `notebook_management.delete` | `delete_notebook` | Delete a notebook |

---

### 3. admin_user_functions.py

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/admin/users` | `project_management.read` | `get_users_in_projects` | List users in projects |

---

### 4. user_functions.py

#### My Project

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/projects` | `my_project.read` | `get_projects` | List user's projects |
| GET | `/dportal/my-projects` | `my_project.read` | `get_my_projects` | List my projects |
| GET | `/dportal/projects/{name}/file` | `my_project.download` | `get_project_file` | Download project file |

#### sBeacon Query

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/queries` | `sbeacon_query.read` | `get_queries` | List saved queries |
| POST | `/dportal/queries` | `sbeacon_query.create` | `save_query` | Save a new query |
| DELETE | `/dportal/queries/{name}` | `sbeacon_query.delete` | `delete_query` | Delete a saved query |
| POST | `/dportal/cohort` | `sbeacon_query.create` | `create_cohort` | Create a new cohort |

---

### 5. notebook_functions.py

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/notebooks` | `my_notebook.create` | `create_notebook` | Create a new notebook |
| GET | `/dportal/notebooks` | `my_notebook.read` | `list_notebooks` | List my notebooks |
| GET | `/dportal/notebooks/{name}` | `my_notebook.read` | `get_notebook` | Get notebook details |
| POST | `/dportal/notebooks/{name}/stop` | `my_notebook.update` | `stop_notebook` | Stop a notebook |
| POST | `/dportal/notebooks/{name}/start` | `my_notebook.update` | `start_notebook` | Start a notebook |
| POST | `/dportal/notebooks/{name}/delete` | `my_notebook.delete` | `delete_notebook` | Delete a notebook |
| PUT | `/dportal/notebooks/{name}` | `my_notebook.update` | `update_notebook` | Update a notebook |
| GET | `/dportal/notebooks/{name}/url` | `my_notebook.read` | `get_notebook_url` | Get notebook URL |

---

### 6. clinic_functions.py

#### Clinical Workflow Execution

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| GET | `/dportal/projects/{project}/clinical-workflows` | `clinical_workflow_execution.read` | `list_clinical_workflows` | List clinical workflows |
| GET | `/dportal/projects/{project}/clinical-workflows/{workflow_id}` | `clinical_workflow_execution.read` | `get_clinical_workflow` | Get workflow details |
| DELETE | `/dportal/projects/{project}/clinical-workflows/{workflow_id}` | `clinical_workflow_execution.delete` | `delete_clinical_workflow` | Delete a workflow |

#### Clinic Workflow Annotation

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/annotations` | `clinic_workflow_annotation.create` | `create_annotation` | Create an annotation |
| GET | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/annotations` | `clinic_workflow_annotation.read` | `list_annotations` | List annotations |
| DELETE | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/annotations/{annotation_id}` | `clinic_workflow_annotation.delete` | `delete_annotation` | Delete an annotation |

#### Clinic Workflow Result

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results` | `clinic_workflow_result.create` | `create_result` | Create a result |
| GET | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results` | `clinic_workflow_result.read` | `list_results` | List results |
| DELETE | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results/{result_id}` | `clinic_workflow_result.delete` | `delete_result` | Delete a result |

#### Clinic Result Validation

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results/{result_id}/validations` | `clinic_result_validation.create` | `create_validation` | Create a validation |
| DELETE | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results/{result_id}/validations/{validation_id}` | `clinic_result_validation.delete` | `delete_validation` | Delete a validation |
| POST | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results/{result_id}/interpretations` | `clinic_result_validation.create` | `create_interpretation` | Create an interpretation |
| DELETE | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/results/{result_id}/interpretations/{interpretation_id}` | `clinic_result_validation.delete` | `delete_interpretation` | Delete an interpretation |

#### Report Generation

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/projects/{project}/clinical-workflows/{workflow_id}/report` | `generate_report.create` | `generate_report` | Generate a report |

---

### 7. cli_functions.py

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/cli` | `my_data.read` | `cli_upload` | CLI upload handler |

---

### 8. user_info_functions.py

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/userinfo` | `profile.update` | `update_user_info` | Update user info |
| GET | `/dportal/userinfo/{uid}` | `profile.read` | `get_user_info` | Get user info |

---

### 9. quota_function.py

| Method | Endpoint | Permission | Function | Description |
|--------|----------|------------|----------|-------------|
| POST | `/dportal/quota` | `my_data.update` | `update_quota` | Update quota |
| GET | `/dportal/quota/{userIdentity}` | `my_data.read` | `get_quota` | Get quota info |
| POST | `/dportal/quota/{userIdentity}/increment_usagecount` | `my_data.update` | `increment_usage` | Increment usage count |

---

## Permission Resources Summary

| Resource | Description |
|----------|-------------|
| `file_management` | Admin folder/file management |
| `project_management` | Admin project management |
| `notebook_management` | Admin notebook management |
| `my_project` | User's own project access |
| `my_notebook` | User's own notebook access |
| `my_data` | User's own data access |
| `sbeacon_query` | User's sBeacon query access |
| `clinical_workflow_execution` | Clinical workflow execution |
| `clinic_workflow_annotation` | Clinical workflow annotations |
| `clinic_workflow_result` | Clinical workflow results |
| `clinic_result_validation` | Clinical result validations |
| `generate_report` | Report generation |
| `profile` | User profile |

---

## Notes

1. Permissions are sent via `X-Permissions-Token` header in JWT format (unsigned, alg: none)
2. Token contains an array of permission strings in the `permissions` field
3. The `require_permissions()` middleware returns 401 if the permission is not found
4. For endpoints without permission requirements (public), no `require_permissions` middleware is needed
