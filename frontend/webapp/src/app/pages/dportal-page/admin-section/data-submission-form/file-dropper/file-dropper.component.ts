import { DecimalPipe } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

export interface FileDropEvent {
  vcf: File;
  tbi: File;
  json: File;
}

@Component({
  selector: 'app-file-dropper',
  standalone: true,
  imports: [MatSnackBarModule, DecimalPipe],
  templateUrl: './file-dropper.component.html',
  styleUrl: './file-dropper.component.scss',
})
export class FileDropperComponent {
  @ViewChild('dropzone') dropzone!: ElementRef;
  @ViewChild('input') input!: ElementRef;
  @Input() disabled: boolean = false;
  @Output() dropped = new EventEmitter<FileDropEvent>();
  types: string[] = ['.vcf.gz', '.vcf.gz.tbi', '.json'];
  // html can only handle last extension
  htmlTypes: string[] = ['.gz', '.tbi', '.json'];
  message: string =
    'Add VCF (.vcf.gz), TBI (.tbi) and JSON (.json) files for submission.';

  vcf: File | null = null;
  tbi: File | null = null;
  json: File | null = null;

  constructor(private sb: MatSnackBar) {}

  highlight(e: Event) {
    this.preventDefaults(e);
    if (this.disabled) {
      return;
    }
    if (this.dropzone) {
      this.dropzone.nativeElement.classList.add('bui-dropper-active');
    }
  }

  unhighlight(e: Event) {
    this.preventDefaults(e);
    if (this.disabled) {
      return;
    }
    if (this.dropzone) {
      this.dropzone.nativeElement.classList.remove('bui-dropper-active');
    }
  }

  handleDrop(e: DragEvent) {
    this.preventDefaults(e);
    if (this.disabled) {
      return;
    }
    const files: FileList = e.dataTransfer?.files ?? new FileList();
    this.handleFiles(files);
  }

  handlePick(e: Event) {
    console.log(e);
    const files = (e.target as HTMLInputElement).files ?? new FileList();
    this.handleFiles(files);
  }

  handleFiles(files: FileList) {
    // validations >>
    if (files.length == 0) {
      return;
    }
    if (files.length > 3) {
      this.sb.open('Cannot provide more than three files.', 'Okay', {
        duration: 60000,
      });
      return;
    }

    for (let index = 0; index < files.length; index++) {
      const file = files.item(index)!;

      if (file.name.endsWith('.vcf.gz')) {
        this.vcf = file;
      } else if (file.name.endsWith('.vcf.gz.tbi')) {
        this.tbi = file;
      } else if (file.name.endsWith('.json')) {
        this.json = file;
      }
    }

    // validations <<
    if (this.vcf && this.tbi && this.json) {
      this.dropped.emit({ vcf: this.vcf, tbi: this.tbi, json: this.json });
    }
  }

  preventDefaults(e: Event) {
    e.preventDefault();
    e.stopPropagation();
  }

  reset() {
    this.vcf = null;
    this.tbi = null;
    this.json = null;
    this.input.nativeElement.value = '';
  }
}
