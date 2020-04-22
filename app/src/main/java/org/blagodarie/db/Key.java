package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

@Entity (
        tableName = "tbl_key",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"value", "type_id"}, unique = true),
                @Index (value = {"owner_id"}),
                @Index (value = {"type_id"}),
                @Index (value = {"value"})
        },
        foreignKeys = {
                @ForeignKey (
                        entity = KeyType.class,
                        parentColumns = "id",
                        childColumns = "type_id"
                )
        }
)
public final class Key
        extends BaseEntity {

    /**
     * Идентификатор владельца ключа.
     * Название столбца таблицы - owner_id.
     */
    @ColumnInfo (name = "owner_id")
    private Long OwnerId;

    /**
     * Значение ключа.
     * Не может быть пустым.
     * Название столбца таблицы - value.
     */
    @NonNull
    @ColumnInfo (name = "value")
    private final String Value;

    /**
     * Идентификатор типа ключа.
     * Не может быть пустым.
     * Название столбца таблицы - type_id.
     */
    @NonNull
    @ColumnInfo (name = "type_id")
    private final Long TypeId;

    /**
     * Конструктор, устанавливающий все поля. (Требует Room)
     *
     * @param Id       Идентификатор
     * @param OwnerId  Идентификатор владельца ключа
     * @param Value    Значение ключа
     * @param TypeId   Идентификатор типа ключа
     */
    Key (
            @Nullable final Long Id,
            @Nullable final Long OwnerId,
            @NonNull final String Value,
            @NonNull final Long TypeId
    ) {
        super(Id);
        this.OwnerId = OwnerId;
        this.Value = Value;
        this.TypeId = TypeId;
    }

    /**
     * Конструктор,  устанавливающий только необходимые поля.
     *
     * @param value  Значение ключа.
     * @param typeId Идентификатор типа ключа.
     */
    Key (
            @NonNull final String value,
            @NonNull final Long typeId
    ) {
        super(null);
        this.Value = value;
        this.TypeId = typeId;
    }

    /**
     * Возвращает идентификатор владельца ключа.
     *
     * @return Идентификатор владельца ключа.
     */
    @Nullable
    final Long getOwnerId () {
        return this.OwnerId;
    }

    /**
     * Устанавливает идентификатор владельца ключа.
     *
     * @param ownerId Идентификатор владельца ключа.
     */
    final void setOwnerId (@Nullable final Long ownerId) {
        this.OwnerId = ownerId;
    }

    /**
     * Возвращает значение ключа.
     *
     * @return Значение ключа.
     */
    @NonNull
    final String getValue () {
        return this.Value;
    }

    /**
     * Возвращает идентификатор типа ключа.
     *
     * @return Идентификатор типа ключа.
     */
    @NonNull
    final Long getTypeId () {
        return this.TypeId;
    }

    @Override
    public String toString () {
        return "Key{" +
                "Id=" + getId() +
                ", OwnerId=" + OwnerId +
                ", Value='" + Value + '\'' +
                ", TypeId=" + TypeId +
                '}';
    }
}