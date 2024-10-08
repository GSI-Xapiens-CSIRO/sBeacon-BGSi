import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ControlContainer,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatOptionModule } from '@angular/material/core';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { FilterTypes, ScopeTypes } from 'src/app/utils/interfaces';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-filter-editor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatOptionModule,
    MatIconModule,
    RouterLink,
    MatSelectModule,
    MatInputModule,
    MatCheckboxModule,
    MatButtonModule,
  ],
  templateUrl: './filter-editor.component.html',
  styleUrl: './filter-editor.component.scss',
})
export class FilterEditorComponent implements OnInit {
  @Output()
  searchFiltersClicked = new EventEmitter<void>();
  @Output()
  removeFilterClicked = new EventEmitter<void>();
  protected form!: FormGroup;
  protected scopeTypes = ScopeTypes;
  protected filterTypes = FilterTypes;

  constructor(private controlContainer: ControlContainer) {}

  ngOnInit(): void {
    this.form = this.controlContainer.control as FormGroup;
  }
}
