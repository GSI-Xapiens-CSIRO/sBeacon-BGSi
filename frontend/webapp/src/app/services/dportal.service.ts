import { Injectable } from '@angular/core';
import { API, Auth } from 'aws-amplify';
import { from } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class DportalService {
  constructor() {}

  // data portal admin project actions
  adminCreateProject(name: string, description: string, files: string[]) {
    console.log('create project');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        'dportal/admin/projects',
        {
          body: { name, description, files },
        },
      ),
    );
  }

  adminUpdateProject(name: string, description: string, files: string[]) {
    console.log('update project');
    return from(
      API.put(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${name}`,
        {
          body: { description, files },
        },
      ),
    );
  }

  getAdminProjects() {
    console.log('get projects');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        'dportal/admin/projects',
        {},
      ),
    );
  }

  deleteAdminProject(project: string) {
    console.log('delete project');
    return from(
      API.del(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${project}`,
        {},
      ),
    );
  }

  // data portal admin notebook actions
  getAdminNotebooks() {
    console.log('get my notebooks');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        'dportal/admin/notebooks',
        {},
      ),
    );
  }

  stopAdminNotebook(name: string) {
    console.log('stop admin notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/notebooks/${name}/stop`,
        {},
      ),
    );
  }

  deleteAdminNotebook(name: string) {
    console.log('stop admin notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/notebooks/${name}/delete`,
        {},
      ),
    );
  }

  getAdminNotebookStatus(name: string) {
    console.log('get admin notebook status');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/notebooks/${name}`,
        {},
      ),
    );
  }

  // project admin users actions
  indexAdminData() {
    console.log('index datasets');
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'index', {
        body: { reIndexTables: true, reIndexOntologyTerms: true },
      }),
    );
  }

  adminGetProjectUsers(project: string) {
    console.log('get project users');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${project}/users`,
        {},
      ),
    );
  }

  adminAddUserToProject(project: string, email: string) {
    console.log('add user to project');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${project}/users`,
        {
          body: { emails: [email] },
        },
      ),
    );
  }

  adminRemoveUserFromProject(project: string, email: string) {
    console.log('remove user from project');
    return from(
      API.del(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${project}/users/${email}`,
        {},
      ),
    );
  }

  // data portal user actions
  getMyProjects() {
    console.log('get my projects');
    return from(
      API.get(environment.api_endpoint_sbeacon.name, 'dportal/projects', {}),
    );
  }

  getMyProjectFile(project: string, prefix: string) {
    console.log('get my project file');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/projects/${project}/file`,
        {
          queryStringParameters: { prefix },
        },
      ),
    );
  }

  createMyNotebookInstance(
    instanceName: string,
    instanceType: string,
    volumeSize: number,
  ) {
    console.log('create my notebook');

    return from(
      Auth.currentCredentials().then((credentials) => {
        const identityId = credentials.identityId;
        return API.post(
          environment.api_endpoint_sbeacon.name,
          'dportal/notebooks',
          {
            body: { instanceName, instanceType, volumeSize, identityId },
          },
        );
      }),
    );
  }

  getMyNotebooks() {
    console.log('get my notebooks');
    return from(
      API.get(environment.api_endpoint_sbeacon.name, 'dportal/notebooks', {}),
    );
  }

  getMyNotebookStatus(name: string) {
    console.log('get my notebook status');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}`,
        {},
      ),
    );
  }

  stopMyNotebook(name: string) {
    console.log('stop my notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/stop`,
        {},
      ),
    );
  }

  startMyNotebook(name: string) {
    console.log('start my notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/start`,
        {},
      ),
    );
  }

  deleteMyNotebook(name: string) {
    console.log('delete my notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/delete`,
        {},
      ),
    );
  }

  updateMyNotebook(name: string, instanceType: string, volumeSize: number) {
    console.log('update my notebook');
    return from(
      API.put(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}`,
        {
          body: { instanceType, volumeSize },
        },
      ),
    );
  }

  getMyNotebookUrl(name: string) {
    console.log('get my notebook url');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/url`,
        {},
      ),
    );
  }
}
