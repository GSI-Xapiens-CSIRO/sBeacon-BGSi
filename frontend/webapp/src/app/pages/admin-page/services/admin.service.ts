import { Injectable } from '@angular/core';
import { API } from 'aws-amplify';
import { environment } from 'src/environments/environment';
import { from } from 'rxjs';

@Injectable()
export class AdminService {
  constructor() {}

  createUser(firstName: string, lastName: string, email: string) {
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'admin/users', {
        body: {
          first_name: firstName,
          last_name: lastName,
          email,
        },
      }),
    );
  }

  listUsers(
    limit: number = 10,
    pageToken: string | null = null,
    key: string | null = null,
    query: string | null = null,
  ) {
    return from(
      API.get(environment.api_endpoint_sbeacon.name, 'admin/users', {
        queryStringParameters: {
          pagination_token: pageToken,
          key,
          query,
          limit: limit,
        },
      }),
    );
  }

  listUsersGroups(email: string) {
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `admin/users/${email}/groups`,
        {},
      ),
    );
  }

  deleteUser(email: string) {
    return from(
      API.del(
        environment.api_endpoint_sbeacon.name,
        `admin/users/${email}`,
        {},
      ),
    );
  }

  updateUsersGroups(email: string, groups: any) {
    return from(
      API.post(
        environment.api_endpoint_sbeacon.name,
        `admin/users/${email}/groups`,
        {
          body: {
            groups,
          },
        },
      ),
    );
  }
}
