package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Ignore;
import androidx.room.Index;

import java.util.Date;
import java.util.UUID;

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
        extends BaseEntity {

    @Nullable
    @ColumnInfo (name = "user_id")
    private final Long UserId;

    @NonNull
    @ColumnInfo (name = "incognito_id", typeAffinity = ColumnInfo.TEXT)
    private final UUID IncognitoId;

    @NonNull
    @ColumnInfo (name = "symptom_id")
    private final Long SymptomId;

    @NonNull
    @ColumnInfo (name = "timestamp", typeAffinity = ColumnInfo.TEXT)
    private final Date Timestamp;

    @Nullable
    @ColumnInfo (name = "latitude")
    private final Double Latitude;

    @Nullable
    @ColumnInfo (name = "longitude")
    private final Double Longitude;

    UserSymptom (
            @NonNull final Long Id,
            @Nullable final Long UserId,
            @NonNull final UUID IncognitoId,
            @NonNull final Long SymptomId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        super(Id);
        this.UserId = UserId;
        this.IncognitoId = IncognitoId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @Ignore
    public UserSymptom (
            @NonNull final UUID IncognitoId,
            @NonNull final Long SymptomId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        super(null);
        this.UserId = null;
        this.IncognitoId = IncognitoId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @Override
    @Nullable
    public Long getId(){
        return super.getId();
    }

    @Nullable
    final Long getUserId () {
        return UserId;
    }

    @NonNull
    UUID getIncognitoId () {
        return IncognitoId;
    }

    @NonNull
    public final Long getSymptomId () {
        return SymptomId;
    }

    @NonNull
    public final Date getTimestamp () {
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
                ", UserId=" + UserId +
                ", IncognitoId=" + IncognitoId +
                ", SymptomId=" + SymptomId +
                ", Timestamp=" + Timestamp +
                ", Latitude=" + Latitude +
                ", Longitude=" + Longitude +
                '}';
    }
}