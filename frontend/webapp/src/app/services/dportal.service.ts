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
  createProject(
    name: string,
    description: string,
    vcf: string,
    tbi: string,
    json: string,
  ) {
    console.log('create project');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        'dportal/admin/projects',
        {
          body: { name, description, vcf, tbi, json },
        },
      ),
    );
  }

  getProjects() {
    console.log('get projects');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        'dportal/admin/projects',
        {},
      ),
    );
  }

  deleteProject(project: string) {
    console.log('delete project');
    return from(
      API.del(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${project}`,
        {},
      ),
    );
  }

  // project admin users actions
  indexData() {
    console.log('index datasets');
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'index', {
        body: { reIndexTables: true, reIndexOntologyTerms: true },
      }),
    );
  }

  getProjectUsers(project: string) {
    console.log('get project users');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/admin/projects/${project}/users`,
        {},
      ),
    );
  }

  addUserToProject(project: string, email: string) {
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

  removeUserFromProject(project: string, email: string) {
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

  getMyProjectFile(project: string, file: string) {
    console.log('get my project file');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/projects/${project}/file`,
        {
          queryStringParameters: { file },
        },
      ),
    );
  }

  createNotebookInstance(
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

  getNotebookStatus(name: string) {
    console.log('get my notebook status');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}`,
        {},
      ),
    );
  }

  stopNotebook(name: string) {
    console.log('stop my notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/stop`,
        {},
      ),
    );
  }

  startNotebook(name: string) {
    console.log('start my notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/start`,
        {},
      ),
    );
  }

  deleteNotebook(name: string) {
    console.log('delete my notebook');
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `dportal/notebooks/${name}/delete`,
        {},
      ),
    );
  }

  updateNotebook(name: string, instanceType: string, volumeSize: number) {
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

  getNotebookUrl(name: string) {
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
