package org.blagodarie.ui.symptoms;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;
import androidx.lifecycle.LiveData;

import org.blagodarie.sync.UserSymptomSyncer;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.Symptom;
import org.blagodatie.database.UserSymptom;

import java.util.Date;
import java.util.Timer;
import java.util.TimerTask;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class DisplaySymptom
        extends BaseObservable
        implements Comparable<DisplaySymptom> {

    private static final String TAG = DisplaySymptom.class.getSimpleName();

    interface UnconfirmedUserSymptomListener {
        void onConfirm (@NonNull final DisplaySymptom displaySymptom);
        void onCancel (@NonNull final UserSymptom canceledUserSymptom);
    }

    @NonNull
    private final Symptom mSymptom;

    @Nullable
    private Date mLastDate;

    private long mUserSymptomCount = 0;

    @Nullable
    private UserSymptom mUnconfirmedUserSymptom;

    private boolean mHaveNotSynced = false;

    @NonNull
    private final UnconfirmedUserSymptomListener mConfirmUserSymptomListener;

    @Nullable
    private Timer mConfirmationTimer;

    public DisplaySymptom (
            @NonNull final Symptom symptom,
            @NonNull final LiveData<Boolean> haveNotSynced,
            @NonNull final LiveData<UserSymptom> notConfirmedUserSymptom,
            @NonNull final UnconfirmedUserSymptomListener unconfirmedUserSymptomListener
    ) {
        Log.d(TAG, "DisplaySymptom");
        mSymptom = symptom;
        haveNotSynced.observeForever(this::setHaveNotSynced);
        notConfirmedUserSymptom.observeForever(latestUserSymptom -> {
            if (latestUserSymptom != null && !latestUserSymptom.equals(mUnconfirmedUserSymptom)) {
                setNotConfirmedUserSymptom(latestUserSymptom);
            }
        });
        mConfirmUserSymptomListener = unconfirmedUserSymptomListener;
    }

    @NonNull
    final Identifier getSymptomId () {
        return mSymptom.getId();
    }

    @NonNull
    @Bindable
    public final String getSymptomName () {
        return mSymptom.getName();
    }

    @Nullable
    @Bindable
    public final Date getLastDate () {
        Date lastDate = mLastDate;
        if (mUnconfirmedUserSymptom != null) {
            lastDate = mUnconfirmedUserSymptom.getTimestamp();
        }
        return lastDate;
    }

    final void setLastDate (@Nullable final Date lastDate) {
        mLastDate = lastDate;
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
    }

    @Bindable
    final long getUserSymptomCount () {
        long userSymptomCount = mUserSymptomCount;
        if (mUnconfirmedUserSymptom != null) {
            userSymptomCount++;
        }
        return userSymptomCount;
    }

    final void setUserSymptomCount (final long userSymptomCount) {
        mUserSymptomCount = userSymptomCount;
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
    }

    @Bindable
    public final boolean isHaveNotSynced () {
        return mHaveNotSynced;
    }

    private void setHaveNotSynced (boolean mHaveNotSynced) {
        this.mHaveNotSynced = mHaveNotSynced;
        notifyPropertyChanged(org.blagodarie.BR.haveNotSynced);
    }

    private void startTimer (final long delay) {
        Log.d(TAG, "startTimer");
        if (mConfirmationTimer == null) {
            mConfirmationTimer = new Timer();
            mConfirmationTimer.schedule(getConfirmationTask(), delay);
        }
    }

    @Nullable
    @Bindable
    public final UserSymptom getNotConfirmedUserSymptom () {
        return mUnconfirmedUserSymptom;
    }

    private void clearNotConfirmedUserSymptom () {
        mUnconfirmedUserSymptom = null;
        notifyPropertyChanged(org.blagodarie.BR.notConfirmedUserSymptom);
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
        notifyPropertyChanged(org.blagodarie.BR.userSymptomCount);
    }

    private void setNotConfirmedUserSymptom (@NonNull final UserSymptom notConfirmedUserSymptom) {
        Log.d(TAG, "setNotConfirmedUserSymptom notConfirmedUserSymptom=" + notConfirmedUserSymptom);
        final long howLongAgo = System.currentTimeMillis() - notConfirmedUserSymptom.getTimestamp().getTime();
        Log.d(TAG, "howLongAgo=" + howLongAgo);
        if (howLongAgo <= UserSymptomSyncer.USER_SYMPTOM_CONFIRMATION_TIME) {
            mUnconfirmedUserSymptom = notConfirmedUserSymptom;
            startTimer(UserSymptomSyncer.USER_SYMPTOM_CONFIRMATION_TIME - howLongAgo);
        }
        notifyPropertyChanged(org.blagodarie.BR.notConfirmedUserSymptom);
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
        notifyPropertyChanged(org.blagodarie.BR.userSymptomCount);
    }

    private void confirmUserSymptom () {
        Log.d(TAG, "confirmUserSymptom");
        mConfirmUserSymptomListener.onConfirm(this);
        clearConfirmationTimer();
        clearNotConfirmedUserSymptom();
    }

    public final void cancelUnconfirmedUserSymptom () {
        Log.d(TAG, "cancelUnconfirmedUserSymptom");
        clearConfirmationTimer();
        if (mUnconfirmedUserSymptom != null) {
            mConfirmUserSymptomListener.onCancel(mUnconfirmedUserSymptom);
        }
        clearNotConfirmedUserSymptom();
    }

    private void clearConfirmationTimer () {
        Log.d(TAG, "clearConfirmationTimer");
        if (mConfirmationTimer != null) {
            mConfirmationTimer.cancel();
            mConfirmationTimer = null;
        }
    }

    private TimerTask getConfirmationTask () {
        Log.d(TAG, "getConfirmationTask");
        return new TimerTask() {
            @Override
            public void run () {
                confirmUserSymptom();
            }
        };
    }


    @Override
    public int compareTo (@NonNull final DisplaySymptom o) {
        int result;
        if (this == o) {
            result = 0;
        } else {
            long thisTimestamp = this.getLastDate() == null ? 0 : this.getLastDate().getTime();
            long otherTimestamp = o.getLastDate() == null ? 0 : o.getLastDate().getTime();
            result = -Long.compare(thisTimestamp, otherTimestamp);
            if (result == 0) {
                result = this.getSymptomName().compareTo(o.getSymptomName());
            }
        }
        return result;
    }

}
