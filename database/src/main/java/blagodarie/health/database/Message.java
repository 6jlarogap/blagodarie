package blagodarie.health.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

import java.util.Objects;

@Entity (
        tableName = "tbl_message",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"name"}, unique = true),
                @Index (value = {"group_id"}),
                @Index (value = {"group_id", "order"}, unique = true)
        },
        foreignKeys = {
                @ForeignKey (
                        entity = MessageGroup.class,
                        parentColumns = "id",
                        childColumns = "group_id"
                )
        }
)
public final class Message
        extends BaseEntity {

    @NonNull
    @ColumnInfo (name = "name")
    private final String Name;

    @NonNull
    @ColumnInfo (name = "group_id", typeAffinity = ColumnInfo.INTEGER)
    private final Identifier GroupId;

    @Nullable
    @ColumnInfo (name = "order")
    private final Integer Order;

    public Message (
            @NonNull final Identifier Id,
            @NonNull final String Name,
            @NonNull final Identifier GroupId,
            @Nullable final Integer Order
    ) {
        super(Id);
        this.Name = Name;
        this.GroupId = GroupId;
        this.Order = Order;
    }

    @NonNull
    public final String getName () {
        return Name;
    }

    @NonNull
    public final Identifier getGroupId () {
        return GroupId;
    }

    @Nullable
    public final Integer getOrder () {
        return Order;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        final Message message = (Message) o;
        return getId().equals(message.getId()) &&
                Name.equals(message.Name) &&
                GroupId.equals(message.GroupId) &&
                Objects.equals(Order, message.Order);
    }

    @Override
    public int hashCode () {
        return Objects.hash(getId(), Name, GroupId, Order);
    }

    @NonNull
    @Override
    public String toString () {
        return "Message{" +
                "Id=" + getId() +
                ", Name='" + Name + '\'' +
                ", GroupId=" + GroupId +
                ", Order=" + Order +
                '}';
    }

}
