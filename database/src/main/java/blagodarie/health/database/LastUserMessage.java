package blagodarie.health.database;

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
        tableName = "tbl_last_user_message",
        primaryKeys = {"incognito_id", "message_id"},
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
public final class LastUserMessage {

    @NonNull
    @ColumnInfo (name = "incognito_id", typeAffinity = ColumnInfo.TEXT)
    private final UUID IncognitoId;

    @NonNull
    @ColumnInfo (name = "message_id", typeAffinity = ColumnInfo.INTEGER)
    private final Identifier MessageId;

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
    @ColumnInfo (name = "messages_count", defaultValue = "1")
    private Long MessagesCount = 1L;

    LastUserMessage (
            @NonNull final UUID IncognitoId,
            @NonNull final Identifier MessageId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude,
            @NonNull final Long MessagesCount
    ) {
        this.IncognitoId = IncognitoId;
        this.MessageId = MessageId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
        this.MessagesCount = MessagesCount;
    }

    @Ignore
    public LastUserMessage (
            @NonNull final UUID IncognitoId,
            @NonNull final Identifier MessageId,
            @NonNull final Date Timestamp,
            @Nullable final Double Latitude,
            @Nullable final Double Longitude
    ) {
        this.IncognitoId = IncognitoId;
        this.MessageId = MessageId;
        this.Timestamp = Timestamp;
        this.Latitude = Latitude;
        this.Longitude = Longitude;
    }

    @NonNull
    final UUID getIncognitoId () {
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
    public final Long getMessagesCount () {
        return MessagesCount;
    }

    public final void setMessagesCount (@NonNull final Long messagesCount) {
        MessagesCount = messagesCount;
    }

    @NonNull
    @Override
    public String toString () {
        return "LastUserMessage{" +
                "IncognitoId=" + IncognitoId +
                ", MessageId=" + MessageId +
                ", Timestamp=" + Timestamp +
                ", Latitude=" + Latitude +
                ", Longitude=" + Longitude +
                ", MessagesCount=" + MessagesCount +
                '}';
    }
}
