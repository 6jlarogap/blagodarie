package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

@Entity (
        tableName = "tbl_symptom",
        inheritSuperIndices = true,
        indices = {
                @Index (value = {"name"}, unique = true),
                @Index (value = {"group_id"}),
                @Index (value = {"group_id", "order"}, unique = true)
        },
        foreignKeys = {
                @ForeignKey (
                        entity = SymptomGroup.class,
                        parentColumns = "id",
                        childColumns = "group_id"
                )
        }
)
public final class Symptom
        extends BaseEntity {

    @NonNull
    @ColumnInfo (name = "name")
    private final String Name;

    @Nullable
    @ColumnInfo (name = "group_id", typeAffinity = ColumnInfo.INTEGER)
    private final Identifier GroupId;

    @Nullable
    @ColumnInfo (name = "order")
    private final Integer Order;

    public Symptom (
            @NonNull final Identifier Id,
            @NonNull final String Name,
            @Nullable final Identifier GroupId,
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

    @Nullable
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
        final Symptom symptom = (Symptom) o;
        return getId().equals(symptom.getId());
    }

    @Override
    public int hashCode () {
        return Objects.hash(getId());
    }

    @NonNull
    @Override
    public String toString () {
        return "Symptom{" +
                "Id=" + getId() +
                ", Name='" + Name + '\'' +
                ", GroupId=" + GroupId +
                ", Order=" + Order +
                '}';
    }

    public static List<Symptom> getSymptoms () {
        final List<Symptom> symptoms = new ArrayList<>();/*
        symptoms.add(new Symptom(Identifier.newInstance(25L), "Пробуждение"));
        symptoms.add(new Symptom(Identifier.newInstance(19L), "Хорошее настроение"));
        symptoms.add(new Symptom(Identifier.newInstance(15L), "Хорошее самочувствие"));
        symptoms.add(new Symptom(Identifier.newInstance(20L), "Плохое настроение"));
        symptoms.add(new Symptom(Identifier.newInstance(29L), "Плохое самочувствие"));
        symptoms.add(new Symptom(Identifier.newInstance(1L), "Нехватка питьевой воды"));
        symptoms.add(new Symptom(Identifier.newInstance(2L), "Нехватка еды"));
        symptoms.add(new Symptom(Identifier.newInstance(3L), "Нехватка лекарств"));
        symptoms.add(new Symptom(Identifier.newInstance(17L), "Повышенное давление"));
        symptoms.add(new Symptom(Identifier.newInstance(18L), "Пониженное давление"));
        symptoms.add(new Symptom(Identifier.newInstance(16L), "Сердечная боль"));
        symptoms.add(new Symptom(Identifier.newInstance(11L), "Головная боль"));
        symptoms.add(new Symptom(Identifier.newInstance(10L), "Сухость носа"));
        symptoms.add(new Symptom(Identifier.newInstance(26L), "Заложенность носа"));
        symptoms.add(new Symptom(Identifier.newInstance(27L), "Насморк"));
        symptoms.add(new Symptom(Identifier.newInstance(5L), "Температура"));
        symptoms.add(new Symptom(Identifier.newInstance(28L), "Озноб"));
        symptoms.add(new Symptom(Identifier.newInstance(24L), "Аллергия"));
        symptoms.add(new Symptom(Identifier.newInstance(6L), "Кашель"));

        symptoms.add(new Symptom(Identifier.newInstance(4L), "Слабость"));
        symptoms.add(new Symptom(Identifier.newInstance(7L), "Боль в груди при дыхании"));
        symptoms.add(new Symptom(Identifier.newInstance(8L), "Затруднённое дыхание"));
        symptoms.add(new Symptom(Identifier.newInstance(9L), "Одышка"));
        symptoms.add(new Symptom(Identifier.newInstance(12L), "Боль и ломота в мышцах и суставах"));
        symptoms.add(new Symptom(Identifier.newInstance(13L), "Рвота"));
        symptoms.add(new Symptom(Identifier.newInstance(14L), "Диарея"));
        symptoms.add(new Symptom(Identifier.newInstance(21L), "Зубная боль"));
        symptoms.add(new Symptom(Identifier.newInstance(22L), "Боль в ушах"));
        symptoms.add(new Symptom(Identifier.newInstance(23L), "Головокружение"));
        symptoms.add(new Symptom(Identifier.newInstance(30L), "Чувство тревоги"));
        symptoms.add(new Symptom(Identifier.newInstance(31L), "Похолодало"));
        symptoms.add(new Symptom(Identifier.newInstance(32L), "Потеплело"));
        symptoms.add(new Symptom(Identifier.newInstance(33L), "Дождь"));
        symptoms.add(new Symptom(Identifier.newInstance(34L), "Ветер"));
        symptoms.add(new Symptom(Identifier.newInstance(35L), "Жара"));
        symptoms.add(new Symptom(Identifier.newInstance(36L), "Астма"));
        symptoms.add(new Symptom(Identifier.newInstance(37L), "Хорошая погода"));
        symptoms.add(new Symptom(Identifier.newInstance(40L), "Влажно"));
        symptoms.add(new Symptom(Identifier.newInstance(41L), "Сухо"));
        symptoms.add(new Symptom(Identifier.newInstance(42L), "Прохладно"));
        symptoms.add(new Symptom(Identifier.newInstance(44L), "Прием пищи"));
        symptoms.add(new Symptom(Identifier.newInstance(45L), "Запор"));
        symptoms.add(new Symptom(Identifier.newInstance(46L), "Чихание"));
        symptoms.add(new Symptom(Identifier.newInstance(47L), "Першит в горле"));
        symptoms.add(new Symptom(Identifier.newInstance(48L), "Пасмурно"));
        symptoms.add(new Symptom(Identifier.newInstance(49L), "Учащённое сердцебиение"));
        symptoms.add(new Symptom(Identifier.newInstance(50L), "Почки"));
        symptoms.add(new Symptom(Identifier.newInstance(51L), "Лицевой нерв"));*/
        return symptoms;
    }
}
