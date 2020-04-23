package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

/**
 * Базовый абстрактный класс для всех сущностей базы данных.
 * Содержит общие для всех сущностей поля и методы.
 *
 * @author sergeGabrus
 */
@Entity
public abstract class BaseEntity {

    /**
     * Идентификатор сущности.
     * Первичный ключ для всех сущностей, генерируется автоматически.
     * Название столбца таблицы - id.
     */
    @Nullable
    @PrimaryKey (autoGenerate = true)
    @ColumnInfo (name = "id")
    private Long Id;


    BaseEntity (@Nullable final Long id) {
        this.Id = id;
    }

    /**
     * Возвращает идентификатор сущности
     *
     * @return Идентификатор сущности
     */
    @Nullable
    public final Long getId () {
        return this.Id;
    }

    /**
     * Устанавливает идентификатор сущности
     *
     * @param id Идентификатор сущности
     */
    public final void setId (@NonNull final Long id) {
        this.Id = id;
    }

    @NonNull
    @Override
    public String toString () {
        return "BaseEntity{" +
                "Id=" + Id +
                '}';
    }
}

