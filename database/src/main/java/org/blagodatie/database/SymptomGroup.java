package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

@Entity (
        tableName = "tbl_symptom_group",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"name"}, unique = true),
                @Index (value = {"parent_id"})
        },
        foreignKeys = {
                @ForeignKey (
                        entity = SymptomGroup.class,
                        parentColumns = "id",
                        childColumns = "parent_id"
                )
        }
)
public final class SymptomGroup
        extends BaseEntity {

    @NonNull
    @ColumnInfo (name = "name")
    private final String Name;

    @Nullable
    @ColumnInfo (name = "parent_id", typeAffinity = ColumnInfo.INTEGER)
    private final Identifier ParentId;

    SymptomGroup (
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

    @NonNull
    @Override
    public String toString () {
        return "SymptomGroup{" +
                "Id=" + getId() +
                ", Name='" + Name + '\'' +
                ", ParentId=" + ParentId +
                '}';
    }
}
