package blagodarie.health;

import androidx.annotation.NonNull;

import java.util.ArrayList;
import java.util.Collection;

public final class Reader
        implements ProgressProvider<Reader.ProgressListener> {

    interface ProgressListener
            extends ProgressProvider.ProgressListener {
        void onRead(final int index);
    }

    class Event extends ProgressProvider.Event{

    }

    @NonNull
    private final Collection<ProgressListener> mProgressListeners = new ArrayList<>();

    @Override
    public void addProgressListener (@NonNull final ProgressListener progressListener) {
        mProgressListeners.add(progressListener);
    }

    @Override
    public void removeProgressListener (@NonNull final ProgressListener progressListener) {
        mProgressListeners.remove(progressListener);
    }

    @Override
    public void notifyListeners (@NonNull Event event) {

    }

    public void read () {
        notifyListeners();
    }
}
