import { Injectable } from '@angular/core';
import {
  ReplaySubject,
  distinctUntilChanged,
  pairwise,
  map,
  startWith,
  debounce,
  timer,
} from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class SpinnerService {
  private eventloopSync = 0;
  // This creates an instance of ReplaySubject that emits boolean values.
  // `ReplaySubject` is a type of subject that can send old values to new subscribers.
  // It records multiple values from the Observable execution and replays them to new subscribers.
  private loadingSubject = new ReplaySubject<boolean>();

  // This chain of operations starts with making an Observable out of `loadingSubject`.
  // We then pipe several operators into it.
  public loading = this.loadingSubject.asObservable().pipe(
    // The `startWith` operator emits its argument as the first value.
    // So in this case, our Observable initially emits a false value.
    startWith(false),

    // `distinctUntilChanged` only allows distinct consecutive values to pass through.
    // So if 'false' or 'true' is emitted multiple times consecutively, only the first one gets through.
    distinctUntilChanged(),

    // `pairwise` groups the values into arrays of two: [previousValue, currentValue].
    // It gives us pairs of consecutive values as array.
    pairwise(),

    // `debounce` operator delays the output of a value.
    // In this case, we delay by 1 second when the previous value was true,
    // otherwise there's no delay (0 milliseconds).
    debounce(([prev, _]) => (!!prev ? timer(500) : timer(0))),

    // Finally, `map` extracts the current value from each pair for emitting.
    map(([_, curr]) => curr),
  );

  // The `start` method increases the `eventloopSync` counter by one,
  // then signals that a process has started by emitting `true` from the `loadingSubject`.
  start() {
    ++this.eventloopSync; // Increment the event loop counter
    this.loadingSubject.next(true); // Emit 'true' to indicate loading has started
  }

  // The `end` method increases the `eventloopSync` counter by one.
  // If `eventloopSync` is zero (indicating there's no ongoing processes),
  // it emits `false` from the `loadingSubject`, signaling that a process has ended.
  end() {
    if (--this.eventloopSync === 0) this.loadingSubject.next(false); // Decrease event loop counter and emit 'false' if it's zero
  }
}
