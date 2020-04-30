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

@Entity (
        tableName = "tbl_last_user_symptom",
        primaryKeys = {"incognito_id", "symptom_id"},
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
public final class LastUserSymptom {

    @NonNull
    @ColumnInfo (name = "incognito_id", typeAffinity = ColumnInfo.TEXT)
    private final UUID IncognitoId;

    @NonNull
    @ColumnInfo (name = "symptom_id")
    private final Long SymptomId;

    @NonNull
    @ColumnInfo (name = "timestamp", typeAffinity = ColumnInfo.TEXT)
    private Date Timestamp;

    @Nullable
    @ColumnInfo (name = "latitude")
    private Double Latitude;

    @Nullable
    @ColumnInfo (name = "longitude")
    private Double Longitude;

    @NonNull
    @ColumnInfo (name = "symptoms_count", defaultValue = "1")
    private Long SymptomsCount = 1L;

    LastUserSymptom (
            @NonNull final UUID IncognitoId,
            @NonNull final Long SymptomId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude,
            @NonNull final Long SymptomsCount
    ) {
        this.IncognitoId = IncognitoId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
        this.SymptomsCount = SymptomsCount;
    }

    @Ignore
    public LastUserSymptom (
            @NonNull final UUID IncognitoId,
            @NonNull final Long SymptomId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        this.IncognitoId = IncognitoId;
        this.SymptomId = SymptomId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @NonNull
    public final UUID getIncognitoId () {
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

    public final void setTimestamp (@NonNull final Date timestamp) {
        Timestamp = timestamp;
    }

    @Nullable
    public final Double getLatitude () {
        return Latitude;
    }

    public final void setLatitude (@NonNull final Double latitude) {
        Latitude = latitude;
    }

    @Nullable
    public final Double getLongitude () {
        return Longitude;
    }

    public final void setLongitude (@NonNull final Double longitude) {
        Longitude = longitude;
    }

    @NonNull
    public final Long getSymptomsCount () {
        return SymptomsCount;
    }

    public final void setSymptomsCount (@NonNull final Long symptomsCount) {
        SymptomsCount = symptomsCount;
    }

    @NonNull
    @Override
    public String toString () {
        return "LastUserSymptom{" +
                "IncognitoId=" + IncognitoId +
                ", SymptomId=" + SymptomId +
                ", Timestamp=" + Timestamp +
                ", Latitude=" + Latitude +
                ", Longitude=" + Longitude +
                ", SymptomsCount=" + SymptomsCount +
                '}';
    }
}
