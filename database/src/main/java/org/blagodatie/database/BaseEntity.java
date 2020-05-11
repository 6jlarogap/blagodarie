package org.blagodatie.database;

import androidx.annotation.NonNull;
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
    @NonNull
    @PrimaryKey (autoGenerate = true)
    @ColumnInfo (name = "id", typeAffinity = ColumnInfo.INTEGER)
    private Identifier Id;

    BaseEntity (@NonNull final Identifier id) {
        this.Id = id;
    }

    /**
     * Возвращает идентификатор сущности
     *
     * @return Идентификатор сущности
     */
    @NonNull
    public Identifier getId () {
        return this.Id;
    }

    @NonNull
    @Override
    public String toString () {
        return "BaseEntity{" +
                "Id=" + Id +
                '}';
    }
}

