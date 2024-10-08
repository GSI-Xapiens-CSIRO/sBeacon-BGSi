import {
  ChangeDetectorRef,
  Component,
  Injectable,
  OnInit,
  ViewChild,
} from '@angular/core';
import { AdminService } from './services/admin.service';
import {
  FormBuilder,
  FormGroup,
  Validators,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { Subject, catchError, of, startWith, switchMap } from 'rxjs';
import * as _ from 'lodash';
import {
  MatPaginator,
  MatPaginatorIntl,
  MatPaginatorModule,
} from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { GlobalSpinnerComponent } from '../../components/global-spinner/global-spinner.component';
import { MatTableModule } from '@angular/material/table';
import { MatOptionModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { ComponentSpinnerComponent } from '../../components/component-spinner/component-spinner.component';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { SpinnerService } from 'src/app/services/spinner.service';
// import { testUsers } from './test_responses/test_users';

// Docs: https://material.angular.io/components/paginator/examples
// Paginator internationalization
@Injectable()
export class MyCustomPaginatorIntl implements MatPaginatorIntl {
  changes = new Subject<void>();

  // For internationalization, the `$localize` function from
  // the `@angular/localize` package can be used.
  firstPageLabel = $localize`First page`;
  itemsPerPageLabel = $localize`Items per page:`;
  lastPageLabel = $localize`Last page`;

  // You can set labels to an arbitrary string too, or dynamically compute
  // it through other third-party internationalization libraries.
  nextPageLabel = 'Next page';
  previousPageLabel = 'Previous page';

  getRangeLabel(page: number, pageSize: number, length: number): string {
    return $localize`Page ${page + 1}`;
  }
}

@Component({
  selector: 'app-admin-page',
  templateUrl: './admin-page.component.html',
  styleUrls: ['./admin-page.component.scss'],
  providers: [
    { provide: MatPaginatorIntl, useClass: MyCustomPaginatorIntl },
    AdminService,
  ],
  standalone: true,
  imports: [
    MatCardModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    ComponentSpinnerComponent,
    MatSelectModule,
    MatOptionModule,
    MatTableModule,
    MatPaginatorModule,
  ],
})
export class AdminPageComponent implements OnInit {
  protected newUserForm: FormGroup;
  protected filterUsersForm: FormGroup;
  protected loading: boolean = false;
  protected usersLoading: boolean = false;
  protected usersTableDisplayedColumns: string[] = [
    'First name',
    'Last name',
    'Email',
    'Confirmed',
  ];
  protected usersTableDataSource: any = [];
  protected pageSize = 10;
  @ViewChild('paginator')
  paginator!: MatPaginator;
  private pageTokens: (string | null)[] = [];
  private lastPage: number = 0;

  constructor(
    private adminServ: AdminService,
    private fb: FormBuilder,
    private cd: ChangeDetectorRef,
    private dg: MatDialog,
    private sb: MatSnackBar,
    private ss: SpinnerService,
  ) {
    this.newUserForm = this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
    });
    this.filterUsersForm = this.fb.group({
      key: [false],
      query: [{ value: '', disabled: true }],
    });

    this.filterUsersForm.controls['key'].valueChanges.subscribe((key) => {
      if (key) {
        this.filterUsersForm.controls['query'].enable();
      } else {
        this.filterUsersForm.controls['query'].disable();
      }
    });
  }

  ngOnInit(): void {
    this.listUsers();
    this.usersTableDataSource.paginator = this.paginator;
    this.cd.detectChanges();

    this.paginator.page.subscribe(() => {
      if (this.pageSize != this.paginator.pageSize) {
        this.resetPagination();
        return this.listUsers();
      }

      if (
        _.isEmpty(this.pageTokens.at(-1)) &&
        !_.isEmpty(this.pageTokens) &&
        this.lastPage < this.paginator.pageIndex
      ) {
        // last page
        this.paginator.pageIndex--;
      } else if (this.lastPage < this.paginator.pageIndex) {
        this.lastPage++;
        this.listUsers();
      } else if (this.lastPage > this.paginator.pageIndex) {
        this.lastPage--;
        // remove next page token
        this.pageTokens.pop();
        // remove current page token
        this.pageTokens.pop();
        this.listUsers();
      }
    });
  }

  async userClick(row: any) {
    const { AdminUserClickDialogComponent } = await import(
      'src/app/pages/admin-page/components/admin-user-click-dialog/admin-user-click-dialog.component'
    );
    const dialog = this.dg.open(AdminUserClickDialogComponent, {
      data: {
        name: `${row['First name']} ${row['Last name']}`,
        email: row.Email,
      },
    });
    dialog.afterClosed().subscribe((data) => {
      if (_.get(data, 'reload', false)) {
        this.resetPagination();
        this.listUsers();
      }
    });
  }

  createUser() {
    const form = this.newUserForm.value;
    this.ss.start();
    this.adminServ
      .createUser(form.firstName, form.lastName, form.email)
      .pipe(
        catchError((e) => {
          if (
            _.get(e, 'response.data.error', '') === 'UsernameExistsException'
          ) {
            this.sb.open('This user already exist in the system!', 'Okay', {
              duration: 60000,
            });
            this.newUserForm.reset();
          }
          return of(null);
        }),
      )
      .subscribe((response) => {
        this.ss.end();

        if (response) {
          this.newUserForm.reset();
          this.sb.open('User created successfully!', 'Okay', {
            duration: 60000,
          });
        }
      });
  }

  resetPagination() {
    this.pageTokens = [];
    this.lastPage = 0;
    this.paginator.pageIndex = 0;
    this.pageSize = this.paginator.pageSize;
  }

  filterUsers() {
    this.resetPagination();
    this.listUsers();
  }

  listUsers() {
    const form = this.filterUsersForm.value;
    console.log;
    let key = null;
    let query = null;
    this.usersLoading = true;

    if (form.key && !_.isEmpty(form.query)) {
      key = form.key;
      query = form.query;
    }

    this.adminServ
      .listUsers(this.pageSize, this.pageTokens.at(-1) || null, key, query)
      .pipe(catchError(() => of(null)))
      .subscribe((response) => {
        if (response) {
          this.pageTokens.push(response.pagination_token);
          this.usersTableDataSource = _.map(
            _.get(response, 'users', []),
            (user: any) => ({
              Email: _.get(
                _.find(user.Attributes, { Name: 'email' }),
                'Value',
                '',
              ),
              'First name': _.get(
                _.find(user.Attributes, { Name: 'given_name' }),
                'Value',
                '',
              ),
              'Last name': _.get(
                _.find(user.Attributes, { Name: 'family_name' }),
                'Value',
                '',
              ),
              Confirmed:
                _.get(user, 'UserStatus') === 'CONFIRMED' ? 'Yes' : 'No',
            }),
          );
        }
        this.usersLoading = false;
      });
  }
}
