package org.blagodarie;

import androidx.annotation.NonNull;

public interface ProgressProvider<ProgressListenerType extends ProgressProvider.ProgressListener> {

    interface ProgressListener {
        void onStart ();

        void onFinish ();
    }

    enum Event {
        START, FINISH
    }

    void addProgressListener (@NonNull final ProgressListenerType progressListener);

    void removeProgressListener (@NonNull final ProgressListenerType progressListener);

    void notifyListeners(@NonNull final Event event);
}
