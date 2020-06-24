package blagodarie.health.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

import java.util.Objects;

@Entity (
        tableName = "tbl_message_group",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"name"}, unique = true),
                @Index (value = {"parent_id"})
        },
        foreignKeys = {
                @ForeignKey (
                        entity = MessageGroup.class,
                        parentColumns = "id",
                        childColumns = "parent_id"
                )
        }
)
public final class MessageGroup
        extends BaseEntity {

    @NonNull
    @ColumnInfo (name = "name")
    private final String Name;

    @Nullable
    @ColumnInfo (name = "parent_id", typeAffinity = ColumnInfo.INTEGER)
    private final Identifier ParentId;

    public MessageGroup (
            @NonNull final Identifier Id,
            @NonNull final String Name,
            @Nullable final Identifier ParentId
    ) {
        super(Id);
        this.Name = Name;
        this.ParentId = ParentId;
    }

    @NonNull
    public final String getName () {
        return Name;
    }

    @Nullable
    public final Identifier getParentId () {
        return ParentId;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        final MessageGroup that = (MessageGroup) o;
        return getId().equals(that.getId()) &&
                Name.equals(that.Name) &&
                Objects.equals(ParentId, that.ParentId);
    }

    @Override
    public int hashCode () {
        return Objects.hash(getId(), Name, ParentId);
    }

    @NonNull
    @Override
    public String toString () {
        return "MessageGroup{" +
                "Id=" + getId() +
                ", Name='" + Name + '\'' +
                ", ParentId=" + ParentId +
                '}';
    }
}
