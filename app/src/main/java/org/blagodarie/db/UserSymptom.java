package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Ignore;
import androidx.room.Index;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
@Entity (
        tableName = "tbl_user_symptom",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"symptom_id"})
        },
        foreignKeys = {
                @ForeignKey (
                        entity = Symptom.class,
                        parentColumns = "id",
                        childColumns = "symptom_id"
                )
        }
)
public final class UserSymptom
        extends SynchronizableEntity {

    @NonNull
    @ColumnInfo (name = "user_id")
    private final Long UserId;

    @NonNull
    @ColumnInfo (name = "symptom_id")
    private final Long SymptomId;

    @NonNull
    @ColumnInfo (name = "timestamp")
    private final Long Timestamp;

    @Nullable
    @ColumnInfo (name = "latitude")
    private final Double Latitude;

    @Nullable
    @ColumnInfo (name = "longitude")
    private final Double Longitude;

    UserSymptom (
            @Nullable final Long Id,
            @Nullable final Long ServerId,
            @NonNull final Long UserId,
            @NonNull final Long SymptomId,
            @NonNull final Long Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        super(Id, ServerId);
        this.UserId = UserId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @Ignore
    public UserSymptom (
            @NonNull final Long UserId,
            @NonNull final Long SymptomId,
            @NonNull final Long Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        super(null, null);
        this.UserId = UserId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
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

    @Nullable
    public final Double getLatitude () {
        return Latitude;
    }

    @Nullable
    public final Double getLongitude () {
        return Longitude;
    }

    @NonNull
    @Override
    public String toString () {
        return "UserSymptom{" +
                "Id=" + getId() +
                ", ServerId=" + getServerId() +
                ", UserId=" + UserId +
                ", SymptomId=" + SymptomId +
                ", Timestamp=" + Timestamp +
                ", Latitude=" + Latitude +
                ", Longitude=" + Longitude +
                '}';
    }
}
