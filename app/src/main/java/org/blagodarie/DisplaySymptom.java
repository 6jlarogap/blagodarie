package org.blagodarie;

import androidx.annotation.NonNull;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class DisplaySymptom
        implements Comparable<DisplaySymptom> {

    @NonNull
    private final Symptom mSymptom;

    private Long mLastTimestamp;

    public DisplaySymptom (@NonNull final Symptom symptom) {
        mSymptom = symptom;
    }

    @NonNull
    public final Symptom getSymptom () {
        return mSymptom;
    }

    public final Long getLastTimestamp () {
        return mLastTimestamp;
    }

    final void setLastTimestamp (Long mLastTimestamp) {
        this.mLastTimestamp = mLastTimestamp;
    }

    public final String getLastTimestampLikeDateString () {
        return mLastTimestamp != null ? SimpleDateFormat.getDateTimeInstance().format(new Date(mLastTimestamp)) : "";
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DisplaySymptom that = (DisplaySymptom) o;
        return mSymptom.equals(that.mSymptom);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mSymptom);
    }

    @Override
    public String toString () {
        return "DisplaySymptom{" +
                "mSymptom=" + mSymptom +
                ", mLastTimestamp=" + mLastTimestamp +
                '}';
    }

    @Override
    public int compareTo (@NonNull final DisplaySymptom o) {
        int result;
        if (this == o) {
            result = 0;
        } else {
            long thisTimestamp = this.mLastTimestamp == null ? 0 : this.mLastTimestamp;
            long otherTimestamp = o.mLastTimestamp == null ? 0 : o.mLastTimestamp;
            result = -Long.compare(thisTimestamp, otherTimestamp);
            if (result == 0) {
                result = this.mSymptom.getName().compareTo(o.mSymptom.getName());
            }
        }
        return result;
    }
}
