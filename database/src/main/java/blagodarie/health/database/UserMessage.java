package blagodarie.health.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Ignore;
import androidx.room.Index;

import java.util.Date;
import java.util.Objects;
import java.util.UUID;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
@Entity (
        tableName = "tbl_user_message",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"message_id"})
        },
        foreignKeys = {
                @ForeignKey (
                        entity = Message.class,
                        parentColumns = "id",
                        childColumns = "message_id"
                )
        }
)
public final class UserMessage
        extends BaseEntity {

    @NonNull
    @ColumnInfo (name = "incognito_id", typeAffinity = ColumnInfo.TEXT)
    private final UUID IncognitoId;

    @NonNull
    @ColumnInfo (name = "message_id", typeAffinity = ColumnInfo.INTEGER)
    private final Identifier MessageId;

    @NonNull
    @ColumnInfo (name = "timestamp", typeAffinity = ColumnInfo.TEXT)
    private final Date Timestamp;

    @Nullable
    @ColumnInfo (name = "latitude")
    private final Double Latitude;

    @Nullable
    @ColumnInfo (name = "longitude")
    private final Double Longitude;

    UserMessage (
            @NonNull final Identifier Id,
            @NonNull final UUID IncognitoId,
            @NonNull final Identifier MessageId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        super(Id);
        this.IncognitoId = IncognitoId;
        this.MessageId = MessageId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @Ignore
    public UserMessage (
            @NonNull final UUID IncognitoId,
            @NonNull final Identifier MessageId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        super(Identifier.newInstance(null));
        this.IncognitoId = IncognitoId;
        this.MessageId = MessageId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @Override
    @NonNull
    public Identifier getId(){
        return super.getId();
    }

    @NonNull
    public UUID getIncognitoId () {
        return IncognitoId;
    }

    @NonNull
    public final Identifier getMessageId () {
        return MessageId;
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

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        UserMessage that = (UserMessage) o;
        return IncognitoId.equals(that.IncognitoId) &&
                MessageId.equals(that.MessageId) &&
                Timestamp.equals(that.Timestamp) &&
                Objects.equals(Latitude, that.Latitude) &&
                Objects.equals(Longitude, that.Longitude);
    }

    @Override
    public int hashCode () {
        return Objects.hash(IncognitoId, MessageId, Timestamp, Latitude, Longitude);
    }

    @NonNull
    @Override
    public String toString () {
        return "UserMessage{" +
                "Id=" + getId() +
                ", IncognitoId=" + IncognitoId +
                ", MessageId=" + MessageId +
                ", Timestamp=" + Timestamp +
                ", Latitude=" + Latitude +
                ", Longitude=" + Longitude +
                '}';
    }
}
