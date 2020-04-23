package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

@Entity (
        tableName = "tbl_user_symptom_key_join",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"user_symptom_id","key_id"}, unique = true),
                @Index (value = {"user_symptom_id"}),
                @Index (value = {"key_id"})
        },
        foreignKeys = {
                @ForeignKey (
                        entity = UserSymptom.class,
                        parentColumns = "id",
                        childColumns = "user_symptom_id"
                ),
                @ForeignKey (
                        entity = Key.class,
                        parentColumns = "id",
                        childColumns = "key_id"
                ),
        }
)
public final class UserSymptomKeyJoin
        extends SynchronizableEntity {

    @NonNull
    @ColumnInfo (name = "user_symptom_id")
    private final Long UserSymptomId;

    @NonNull
    @ColumnInfo (name = "key_id")
    private final Long KeyId;

    public UserSymptomKeyJoin (
            @NonNull final Long UserSymptomId,
            @NonNull final Long KeyId
    ) {
        super(null, null);
        this.UserSymptomId = UserSymptomId;
        this.KeyId = KeyId;
    }

    @NonNull
    public final Long getUserSymptomId () {
        return UserSymptomId;
    }

    @NonNull
    public final Long getKeyId () {
        return KeyId;
    }

    @NonNull
    @Override
    public String toString () {
        return "UserSymptomKeyJoin{" +
                "Id=" + getId() +
                ", ServerId=" + getServerId() +
                ", UserSymptomId=" + UserSymptomId +
                ", KeyId=" + KeyId +
                '}';
    }
}
