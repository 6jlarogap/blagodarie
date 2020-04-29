package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.Index;

@Entity (
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"server_id"}, unique = true)
        }
)
abstract class SynchronizableEntity
        extends BaseEntity {

    /**
     * Серверный идетификатор
     * Название столбца таблицы - server_id
     */
    @Nullable
    @ColumnInfo (name = "server_id")
    private Long ServerId;

    SynchronizableEntity (
            @Nullable final Long id,
            @Nullable final Long serverId
    ) {
        super(id);
        this.ServerId = serverId;
    }

    /**
     * Возвращает серверный идентификатор сущности
     *
     * @return Серверный идентификатор
     */
    @Nullable
    final Long getServerId () {
        return this.ServerId;
    }

    /**
     * Устанавливает серверный идентификатор сущности
     *
     * @param serverId Серверный идентификатор
     */
    public final void setServerId (@NonNull final Long serverId) {
        this.ServerId = serverId;
    }

}