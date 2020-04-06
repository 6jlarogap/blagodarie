package org.blagodarie;

import androidx.annotation.NonNull;

import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
final class UserSymptom {

    @NonNull
    private final Long mUserId;

    @NonNull
    private final Long mSymptomId;

    @NonNull
    private final Long mTimestamp;

    private final Double mLatitude;

    private final Double mLongitude;

    UserSymptom (
            @NonNull final Long userId,
            @NonNull final Long symptomId,
            @NonNull final Long timestamp,
            final Double latitude,
            final Double longitude
    ) {
        mUserId = userId;
        mSymptomId = symptomId;
        mTimestamp = timestamp;
        mLatitude = latitude;
        mLongitude = longitude;
    }

    @NonNull
    public final Long getUserId () {
        return mUserId;
    }

    @NonNull
    public final Long getSymptomId () {
        return mSymptomId;
    }

    @NonNull
    public final Long getTimestamp () {
        return mTimestamp;
    }

    public final Double getLatitude () {
        return mLatitude;
    }

    public final Double getLongitude () {
        return mLongitude;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        UserSymptom that = (UserSymptom) o;
        return mUserId.equals(that.mUserId) &&
                mSymptomId.equals(that.mSymptomId) &&
                mTimestamp.equals(that.mTimestamp);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mUserId, mSymptomId, mTimestamp);
    }

    @NonNull
    @Override
    public String toString () {
        return "UserSymptom{" +
                "mUserId=" + mUserId +
                ", mSymptomId=" + mSymptomId +
                ", mTimestamp=" + mTimestamp +
                ", mLatitude=" + mLatitude +
                ", mLongitude=" + mLongitude +
                '}';
    }
}
