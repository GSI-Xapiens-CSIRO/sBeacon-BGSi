import { DecimalPipe } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  Output,
  ViewChild,
} from '@angular/core';

@Component({
  selector: 'app-file-dropper',
  standalone: true,
  imports: [],
  templateUrl: './file-dropper.component.html',
  styleUrl: './file-dropper.component.scss',
})
export class FileDropperComponent {
  @ViewChild('dropzone') dropzone!: ElementRef;
  @ViewChild('input') input!: ElementRef;
  @Input() disabled: boolean = false;
  @Input() files: string[] = [];
  @Output() dropped = new EventEmitter<FileList>();

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
    const files = (e.target as HTMLInputElement).files ?? new FileList();
    this.handleFiles(files);
  }

  handleFiles(files: FileList) {
    this.dropped.emit(files);
    this.input.nativeElement.value = '';
  }

  preventDefaults(e: Event) {
    e.preventDefault();
    e.stopPropagation();
  }
}
