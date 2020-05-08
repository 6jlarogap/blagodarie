package org.blagodarie.ui.symptoms;

import android.os.Handler;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;
import androidx.lifecycle.LiveData;

import org.blagodarie.Repository;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.Symptom;

import java.util.Date;
import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class DisplaySymptom
        extends BaseObservable
        implements Comparable<DisplaySymptom> {

    /**
     * Время подсветки в миллисекундах.
     */
    private static final long HIGHLIGHT_TIME = 60000;

    @NonNull
    private final Identifier mSymptomId;

    @NonNull
    private final String mSymptomName;

    @Nullable
    private Date mLastDate;

    @Nullable
    private Double mLastLatitude;

    @Nullable
    private Double mLastLongitude;

    private boolean mHaveNotSynced = false;

    private volatile long mUserSymptomCount = 0;

    private boolean mHighlight = false;

    public DisplaySymptom (
            @NonNull final Identifier symptomId,
            @NonNull final String symptomName,
            @NonNull final LiveData<Boolean> haveNotSynced
    ) {
        mSymptomId = symptomId;
        mSymptomName = symptomName;
        haveNotSynced.observeForever(this::setHaveNotSynced);
    }

    @NonNull
    Identifier getSymptomId () {
        return mSymptomId;
    }

    @NonNull
    @Bindable
    public final String getSymptomName () {
        return mSymptomName;
    }

    @Nullable
    @Bindable
    public final Date getLastDate () {
        return mLastDate;
    }

    final void setLastDate (@Nullable final Date lastDate) {
        mLastDate = lastDate;
        notifyPropertyChanged(org.blagodarie.BR.lastDate);
    }

    @Nullable
    @Bindable
    public Double getLastLatitude () {
        return mLastLatitude;
    }

    final void setLastLatitude (@Nullable final Double lastLatitude) {
        mLastLatitude = lastLatitude;
        notifyPropertyChanged(org.blagodarie.BR.lastLatitude);
    }

    @Nullable
    @Bindable
    public Double getLastLongitude () {
        return mLastLongitude;
    }

    final void setLastLongitude (@Nullable final Double lastLongitude) {
        mLastLongitude = lastLongitude;
        notifyPropertyChanged(org.blagodarie.BR.lastLongitude);
    }

    @Bindable
    public boolean isHaveNotSynced () {
        return mHaveNotSynced;
    }

    void setHaveNotSynced (boolean mHaveNotSynced) {
        this.mHaveNotSynced = mHaveNotSynced;
        notifyPropertyChanged(org.blagodarie.BR.haveNotSynced);
    }

    long getUserSymptomCount () {
        return mUserSymptomCount;
    }

    void setUserSymptomCount (final long userSymptomCount) {
        this.mUserSymptomCount = userSymptomCount;
    }

    @Bindable
    public boolean getHighlight () {
        return mHighlight;
    }

    private void setHighlight (final boolean highlight) {
        mHighlight = highlight;
        notifyPropertyChanged(org.blagodarie.BR.highlight);
    }

    void highlight () {
        setHighlight(true);
        new Handler().postDelayed(() -> setHighlight(false), HIGHLIGHT_TIME);
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DisplaySymptom that = (DisplaySymptom) o;
        return mUserSymptomCount == that.mUserSymptomCount &&
                mSymptomId.equals(that.mSymptomId) &&
                mSymptomName.equals(that.mSymptomName) &&
                Objects.equals(mLastDate, that.mLastDate) &&
                Objects.equals(mLastLatitude, that.mLastLatitude) &&
                Objects.equals(mLastLongitude, that.mLastLongitude);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mSymptomId, mSymptomName, mLastDate, mLastLatitude, mLastLongitude, mUserSymptomCount);
    }

    @Override
    public String toString () {
        return "DisplaySymptom{" +
                "mSymptomId=" + mSymptomId +
                ", mSymptomName='" + mSymptomName + '\'' +
                ", mLastDate=" + mLastDate +
                ", mLastLatitude=" + mLastLatitude +
                ", mLastLongitude=" + mLastLongitude +
                ", mUserSymptomCount=" + mUserSymptomCount +
                '}';
    }

    @Override
    public int compareTo (@NonNull final DisplaySymptom o) {
        int result;
        if (this == o) {
            result = 0;
        } else {
            long thisTimestamp = this.mLastDate == null ? 0 : this.mLastDate.getTime();
            long otherTimestamp = o.mLastDate == null ? 0 : o.mLastDate.getTime();
            result = -Long.compare(thisTimestamp, otherTimestamp);
            if (result == 0) {
                result = this.mSymptomName.compareTo(o.mSymptomName);
            }
        }
        return result;
    }

}
