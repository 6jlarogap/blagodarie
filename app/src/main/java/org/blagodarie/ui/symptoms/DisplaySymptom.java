package org.blagodarie.ui.symptoms;

import android.os.Handler;

import androidx.annotation.NonNull;
import androidx.databinding.ObservableBoolean;
import androidx.databinding.ObservableField;

import java.util.Date;
import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class DisplaySymptom
        implements Comparable<DisplaySymptom> {

    /**
     * Время подсветки в миллисекундах.
     */
    private static final long HIGHLIGHT_TIME = 60000;

    @NonNull
    private final Long mSymptomId;

    @NonNull
    private final String mSymptomName;

    @NonNull
    private ObservableField<Date> mLastDate = new ObservableField<>();

    @NonNull
    private ObservableField<Double> mLastLatitude = new ObservableField<>();

    @NonNull
    private ObservableField<Double> mLastLongitude = new ObservableField<>();

    @NonNull
    private ObservableBoolean mInLoadProgress = new ObservableBoolean(false);

    @NonNull
    private ObservableBoolean mHighlight = new ObservableBoolean(false);

    public DisplaySymptom (
            @NonNull final Long symptomId,
            @NonNull final String symptomName
    ) {
        mSymptomId = symptomId;
        mSymptomName = symptomName;
    }

    @NonNull
    Long getSymptomId () {
        return mSymptomId;
    }

    @NonNull
    public String getSymptomName () {
        return mSymptomName;
    }

    @NonNull
    public final ObservableField<Date> getLastDate () {
        return mLastDate;
    }

    @NonNull
    public ObservableField<Double> getLastLatitude () {
        return mLastLatitude;
    }

    @NonNull
    public ObservableField<Double> getLastLongitude () {
        return mLastLongitude;
    }

    @NonNull
    public ObservableBoolean getInLoadProgress () {
        return mInLoadProgress;
    }

    @NonNull
    public ObservableBoolean getHighlight () {
        return mHighlight;
    }

    void highlight () {
        mHighlight.set(true);
        new Handler().postDelayed(() -> mHighlight.set(false), HIGHLIGHT_TIME);
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DisplaySymptom that = (DisplaySymptom) o;
        return mSymptomId.equals(that.mSymptomId);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mSymptomId);
    }

    @Override
    public String toString () {
        return "DisplaySymptom{" +
                "mSymptomId=" + mSymptomId +
                ", mSymptomName='" + mSymptomName + '\'' +
                ", mLastDate=" + mLastDate +
                ", mLastLatitude=" + mLastLatitude +
                ", mLastLongitude=" + mLastLongitude +
                '}';
    }

    @Override
    public int compareTo (@NonNull final DisplaySymptom o) {
        int result;
        if (this == o) {
            result = 0;
        } else {
            long thisTimestamp = this.mLastDate.get() == null ? 0 : this.mLastDate.get().getTime();
            long otherTimestamp = o.mLastDate.get() == null ? 0 : o.mLastDate.get().getTime();
            result = -Long.compare(thisTimestamp, otherTimestamp);
            if (result == 0) {
                result = this.mSymptomName.compareTo(o.mSymptomName);
            }
        }
        return result;
    }
}
