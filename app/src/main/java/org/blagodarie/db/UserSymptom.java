package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.Index;
import androidx.room.PrimaryKey;

import java.util.Objects;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
@Entity(
        indices = {
                @Index (value = {"server_id"}, unique = true)
        }
)
public final class UserSymptom {

    @PrimaryKey (autoGenerate = true)
    @ColumnInfo (name = "id")
    private final Long Id;

    @ColumnInfo (name = "server_id")
    private final Long ServerId;

    @NonNull
    @ColumnInfo (name = "user_id")
    private final Long UserId;

    @NonNull
    @ColumnInfo (name = "symptom_id")
    private final Long SymptomId;

    @NonNull
    @ColumnInfo (name = "timestamp")
    private final Long Timestamp;

    @ColumnInfo (name = "latitude")
    private final Double Latitude;

    @ColumnInfo (name = "longitude")
    private final Double Longitude;

    UserSymptom (
            @NonNull final Long Id,
            @NonNull final Long ServerId,
            @NonNull final Long UserId,
            @NonNull final Long SymptomId,
            @NonNull final Long Timestamp,
            final Double Latitude,
            final Double Longitude
    ) {
        this.Id = Id;
        this.ServerId = ServerId;
        this.UserId = UserId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    public UserSymptom (
            @NonNull final Long UserId,
            @NonNull final Long SymptomId,
            @NonNull final Long Timestamp,
            final Double Latitude,
            final Double Longitude
    ) {
        this.Id = null;
        this.ServerId = null;
        this.UserId = UserId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    public final Long getId () {
        return Id;
    }

    public final Long getServerId () {
        return ServerId;
    }

    @NonNull
    public final Long getUserId () {
        return UserId;
    }

    @NonNull
    public final Long getSymptomId () {
        return SymptomId;
    }

    @NonNull
    public final Long getTimestamp () {
        return Timestamp;
    }

    public final Double getLatitude () {
        return Latitude;
    }

    public final Double getLongitude () {
        return Longitude;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        UserSymptom that = (UserSymptom) o;
        return UserId.equals(that.UserId) &&
                SymptomId.equals(that.SymptomId) &&
                Timestamp.equals(that.Timestamp);
    }

    @Override
    public int hashCode () {
        return Objects.hash(UserId, SymptomId, Timestamp);
    }

    @NonNull
    @Override
    public String toString () {
        return "UserSymptom{" +
                "Id=" + Id +
                ", ServerId=" + ServerId +
                ", UserId=" + UserId +
                ", SymptomId=" + SymptomId +
                ", Timestamp=" + Timestamp +
                ", Latitude=" + Latitude +
                ", Longitude=" + Longitude +
                '}';
    }
}
