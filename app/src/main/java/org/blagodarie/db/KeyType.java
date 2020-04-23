package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.Index;

/**
 * Класс, определяющий сущность Тип Ключа
 * <p>
 * Название таблицы - tbl_keyztype
 * <p>
 * Индексы:
 * - наименование ключа - уникально;
 *
 * @author sergeGabrus
 */
@Entity (
        tableName = "tbl_key_type",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"title"}, unique = true)
        }
)
public final class KeyType
        extends BaseEntity {

    /**
     * Перечисление Типов Ключей. Типы Ключей, перечисленные здесь, должны быть автоматически
     * добавлены в таблицу tbl_key_type, после создания базы данных.
     */
    public enum Type {
        /**
         * Номер телефона.
         */
        PHONE_NUMBER(1L, "PhoneNumber"),
        /**
         * Адрес электронной почты.
         */
        EMAIL(2L, "Email"),
        /**
         * Идентификатор аккаунта Google.
         */
        GOOGLE_ACCOUNT_ID(3L, "GoogleAccountId"),
        /**
         * Идентификатор аккаунта Google.
         */
        BLAGODARIE_KEY(4L, "BlagodarieKey");

        /**
         * Тип ключа.
         */
        @NonNull
        private final KeyType mKeyType;

        /**
         * Конструктор, создает новый объект.
         *
         * @param id    Идентификатор типа.
         * @param title Наименование типа.
         */
        Type (
                @NonNull final Long id,
                @NonNull final String title
        ) {
            this.mKeyType = new KeyType(id, title);
        }

        /**
         * Метод создает сущность {@link KeyType}.
         *
         * @return Возвращает сущность Тип Ключа.
         */
        @NonNull
        public final KeyType getKeyType () {
            return this.mKeyType;
        }
    }

    /**
     * Наименование.
     * Не может быть пустым.
     * Название столбца таблицы - title.
     */
    @NonNull
    @ColumnInfo (name = "title")
    private final String Title;

    /**
     * Конструктор, создает новый объект.
     *
     * @param Id    Идентификатор типа ключа.
     * @param Title Наименование типа ключа.
     */
    KeyType (
            @NonNull final Long Id,
            @NonNull final String Title
    ) {
        super(Id);
        this.Title = Title;
    }

    /**
     * Возвращает наименование типа ключа
     *
     * @return Наименование типа ключа
     */
    @NonNull
    public final String getTitle () {
        return this.Title;
    }

    @NonNull
    @Override
    public String toString () {
        return "KeyType{" +
                "Id=" + getId() +
                ", Title='" + Title + '\'' +
                '}';
    }
}
