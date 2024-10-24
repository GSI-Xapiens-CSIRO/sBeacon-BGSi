import { Injectable } from '@angular/core';
import { API } from 'aws-amplify';
import { from } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class DportalService {
  constructor() {}

  submitData(s3path: string) {
    console.log('submit dataset', s3path);
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'submit_dataset', {
        body: { s3Payload: s3path },
      }),
    );
  }

  indexData() {
    console.log('index datasets');
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'index', {
        body: { reIndexTables: true, reIndexOntologyTerms: true },
      }),
    );
  }

  // data portal user actions
  createNotebookInstance(
    instanceName: string,
    instanceType: string,
    volumeSize: number,
  ) {
    console.log('create my notebook');
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'dportal/notebooks', {
        body: { instanceName, instanceType, volumeSize },
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
